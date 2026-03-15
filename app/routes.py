import os
from flask import Blueprint, request, jsonify, make_response, current_app
from sqlalchemy.exc import IntegrityError
from . import db
from .models import Candidate, Skill
from .parser import extract_text
from .nlp_extractor import extract_all
from .utils import (
    allowed_file,
    get_file_extension,
    save_uploaded_file,
    cleanup_file,
)

api = Blueprint("api", __name__, url_prefix="/api")


def ok(data, message="Success", status=200):
    """Return a proper Flask JSON response with correct status code."""
    return make_response(jsonify({"status": "success", "message": message, "data": data}), status)


def err(message, status=400):
    """Return a proper Flask JSON error response with correct status code."""
    return make_response(jsonify({"status": "error", "message": message}), status)


# ---------------------------------------------------------------------------
# POST /api/upload  –  Upload and parse a resume
# ---------------------------------------------------------------------------
@api.route("/upload", methods=["POST"])
def upload_resume():
    # 1. Validate that a file was included in the request
    if "file" not in request.files:
        return err("No file part in the request", 400)

    file = request.files["file"]

    if file.filename == "":
        return err("No file selected", 400)

    if not allowed_file(file.filename):
        return err("Invalid file type. Only PDF and DOCX are allowed.", 415)

    filepath = None
    try:
        # 2. Save the uploaded file temporarily
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        filepath, filename = save_uploaded_file(file, upload_folder)
        ext = get_file_extension(filename)

        # 3. Extract raw text from the file
        raw_text = extract_text(filepath, ext)
        if not raw_text:
            return err("Could not extract text from the file.", 422)

        # 4. Run NLP extraction
        extracted = extract_all(raw_text)

        # 5. Handle duplicate email (unique constraint)
        email = extracted.get("email")
        if email:
            existing = Candidate.query.filter_by(email=email).first()
            if existing:
                return err(
                    f"A candidate with email '{email}' already exists. "
                    f"Candidate ID: {existing.id}",
                    409,
                )

        # 6. Persist the candidate record
        candidate = Candidate(
            full_name=extracted.get("full_name"),
            email=email,
            phone=extracted.get("phone"),
            education=extracted.get("education"),
            experience_summary=extracted.get("experience_summary"),
        )
        db.session.add(candidate)

        # 7. Persist skills (get-or-create) and link them
        for skill_name in extracted.get("skills", []):
            skill = Skill.query.filter_by(skill_name=skill_name).first()
            if not skill:
                skill = Skill(skill_name=skill_name)
                db.session.add(skill)
            if skill not in candidate.skills:
                candidate.skills.append(skill)

        db.session.commit()

        return ok(candidate.to_dict(), "Resume parsed and saved successfully.", 201)

    except IntegrityError:
        db.session.rollback()
        return err("Database integrity error. Possible duplicate entry.", 409)
    except ValueError as e:
        return err(str(e), 422)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload error: {e}")
        return err(f"Internal server error: {str(e)}", 500)
    finally:
        # 8. Clean up the temporary file
        if filepath:
            cleanup_file(filepath)


# ---------------------------------------------------------------------------
# GET /api/candidates  –  List all candidates (paginated)
# ---------------------------------------------------------------------------
@api.route("/candidates", methods=["GET"])
def list_candidates():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        pagination = Candidate.query.order_by(Candidate.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        data = {
            "candidates": [c.to_dict() for c in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "per_page": pagination.per_page,
        }
        return ok(data)
    except Exception as e:
        current_app.logger.error(f"List candidates error: {e}")
        return err("Failed to retrieve candidates.", 500)


# ---------------------------------------------------------------------------
# GET /api/candidates/<id>  –  Get a single candidate by ID
# ---------------------------------------------------------------------------
@api.route("/candidates/<int:candidate_id>", methods=["GET"])
def get_candidate(candidate_id):
    try:
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            return err(f"Candidate with ID {candidate_id} not found.", 404)
        return ok(candidate.to_dict())
    except Exception as e:
        current_app.logger.error(f"Get candidate error: {e}")
        return err("Failed to retrieve candidate.", 500)


# ---------------------------------------------------------------------------
# GET /api/search?skill=Python&name=John  –  Search candidates
# ---------------------------------------------------------------------------
@api.route("/search", methods=["GET"])
def search_candidates():
    skill_query = request.args.get("skill", "").strip()
    name_query = request.args.get("name", "").strip()

    if not skill_query and not name_query:
        return err("Provide at least one search parameter: 'skill' or 'name'.", 400)

    try:
        query = Candidate.query

        if name_query:
            query = query.filter(Candidate.full_name.ilike(f"%{name_query}%"))

        if skill_query:
            query = query.join(Candidate.skills).filter(
                Skill.skill_name.ilike(f"%{skill_query}%")
            )

        candidates = query.order_by(Candidate.created_at.desc()).all()

        data = {
            "results": [c.to_dict() for c in candidates],
            "count": len(candidates),
        }
        return ok(data)
    except Exception as e:
        current_app.logger.error(f"Search error: {e}")
        return err("Search failed.", 500)


# ---------------------------------------------------------------------------
# DELETE /api/candidates/<id>  –  Delete a candidate
# ---------------------------------------------------------------------------
@api.route("/candidates/<int:candidate_id>", methods=["DELETE"])
def delete_candidate(candidate_id):
    try:
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            return err(f"Candidate with ID {candidate_id} not found.", 404)
        db.session.delete(candidate)
        db.session.commit()
        return ok({"id": candidate_id}, "Candidate deleted successfully.")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete candidate error: {e}")
        return err("Failed to delete candidate.", 500)


# ---------------------------------------------------------------------------
# GET /api/health  –  Health check endpoint
# ---------------------------------------------------------------------------
@api.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Resume Parser API is running."})

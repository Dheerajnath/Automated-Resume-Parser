import os
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {"pdf", "docx"}


def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_extension(filename: str) -> str:
    """Return the lowercase file extension without the dot."""
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


def save_uploaded_file(file, upload_folder: str) -> tuple[str, str]:
    """
    Save an uploaded file to the upload folder.
    Returns (filepath, filename).
    """
    filename = secure_filename(file.filename)
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    return filepath, filename


def cleanup_file(filepath: str) -> None:
    """Remove a temporary file after processing."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except OSError:
        pass  # Silently ignore cleanup errors


def success_response(data: dict, message: str = "Success", status: int = 200):
    """Build a standardised success JSON response tuple."""
    return {"status": "success", "message": message, "data": data}, status


def error_response(message: str, status: int = 400):
    """Build a standardised error JSON response tuple."""
    return {"status": "error", "message": message}, status

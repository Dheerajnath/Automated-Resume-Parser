# Automated Resume Parser

A production-ready web application that accepts resume uploads (PDF/DOCX), extracts structured candidate data using NLP, stores results in PostgreSQL, and exposes a REST API.

---

## Features

- Upload resumes in **PDF** or **DOCX** format
- Extracts: **Name, Email, Phone, Skills, Education, Experience Summary**
- Uses **spaCy** (NER) + **regex** for NLP extraction
- Matches against a curated list of **50+ skills**
- Stores data in **PostgreSQL** via SQLAlchemy
- REST API with full CRUD + search
- Fully **Dockerized** for one-command startup

---

## Project Structure

```
resume_parser/
├── app/
│   ├── __init__.py         # App factory
│   ├── models.py           # SQLAlchemy models
│   ├── routes.py           # API endpoints (Blueprint)
│   ├── parser.py           # PDF/DOCX text extraction
│   ├── nlp_extractor.py    # spaCy + regex NLP logic
│   ├── utils.py            # Helper utilities
│   └── config.py           # Configuration
├── migrations/             # Flask-Migrate migration files
├── uploads/                # Temporary resume storage
├── requirements.txt
├── run.py
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Quick Start (Docker — Recommended)

### Prerequisites
- Docker & Docker Compose installed

### Steps

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd resume_parser

# 2. Copy environment file
cp .env.example .env

# 3. Build and start all services
docker-compose up --build

# The API will be available at http://localhost:5000
```

Migrations run automatically on container startup.

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL running locally

### Steps

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy model
python -m spacy download en_core_web_sm

# 4. Configure environment
cp .env.example .env
# Edit .env to set your local DATABASE_URL

# 5. Initialise the database and run migrations
export FLASK_APP=run.py
flask db init        # Only first time
flask db migrate -m "Initial migration"
flask db upgrade

# 6. Start the development server
python run.py
```

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/resumedb` |
| `SECRET_KEY` | Flask secret key | `change-me-in-production` |
| `UPLOAD_FOLDER` | Directory for temporary file storage | `uploads` |

---

## API Reference

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Upload a Resume
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@/path/to/resume.pdf"
```

**Response (201):**
```json
{
  "status": "success",
  "message": "Resume parsed and saved successfully.",
  "data": {
    "id": 1,
    "full_name": "Jane Doe",
    "email": "jane.doe@example.com",
    "phone": "+1 555-123-4567",
    "education": "B.Tech in Computer Science, University of Example, 2020",
    "experience_summary": "Organizations mentioned: Google, Accenture",
    "skills": ["Python", "Flask", "Docker", "PostgreSQL", "Machine Learning"],
    "created_at": "2024-01-15T10:30:00"
  }
}
```

### List All Candidates
```bash
curl http://localhost:5000/api/candidates
curl "http://localhost:5000/api/candidates?page=1&per_page=10"
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Success",
  "data": {
    "candidates": [ { "id": 1, "full_name": "Jane Doe", "..." } ],
    "total": 42,
    "page": 1,
    "pages": 5,
    "per_page": 10
  }
}
```

### Get Candidate by ID
```bash
curl http://localhost:5000/api/candidates/1
```

### Search Candidates
```bash
# Search by skill
curl "http://localhost:5000/api/search?skill=Python"

# Search by name
curl "http://localhost:5000/api/search?name=John"

# Combine both filters
curl "http://localhost:5000/api/search?name=Jane&skill=Docker"
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Success",
  "data": {
    "results": [ { "id": 1, "full_name": "Jane Doe", "..." } ],
    "count": 1
  }
}
```

### Delete a Candidate
```bash
curl -X DELETE http://localhost:5000/api/candidates/1
```

---

## Database Schema

```
candidates
----------
id              SERIAL PRIMARY KEY
full_name       VARCHAR(255)
email           VARCHAR(255) UNIQUE
phone           VARCHAR(50)
education       TEXT
experience_summary TEXT
created_at      TIMESTAMP

skills
------
id              SERIAL PRIMARY KEY
skill_name      VARCHAR(100) UNIQUE

candidate_skills  (join table)
-----------------
id              SERIAL PRIMARY KEY
candidate_id    INTEGER REFERENCES candidates(id) ON DELETE CASCADE
skill_id        INTEGER REFERENCES skills(id) ON DELETE CASCADE
```

---

## Running Migrations Manually

```bash
# Inside Docker
docker-compose exec web flask db migrate -m "description"
docker-compose exec web flask db upgrade

# Locally
flask db migrate -m "description"
flask db upgrade
```

---

## Deployment

### Deploy to Render

1. Push the project to a GitHub repository.
2. Create a new **Web Service** on [render.com](https://render.com).
3. Set **Build Command**: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
4. Set **Start Command**: `flask db upgrade && python run.py`
5. Add a **PostgreSQL** database via Render's dashboard.
6. Set environment variables (`DATABASE_URL`, `SECRET_KEY`, `UPLOAD_FOLDER`) in Render's settings.

### Deploy to AWS (Elastic Beanstalk)

1. Install the [EB CLI](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html).
2. Run `eb init` to configure your environment.
3. Create a `Procfile`: `web: flask db upgrade && python run.py`
4. Provision an **RDS PostgreSQL** instance and set `DATABASE_URL` in EB environment properties.
5. Run `eb create` and `eb deploy`.

---

## Future Enhancements

- **Resume scoring** against a job description using cosine similarity
- **Asynchronous processing** with Celery + Redis for large file volumes
- **OCR support** for scanned PDF resumes via Tesseract
- **Named entity disambiguation** using a fine-tuned spaCy model
- **Authentication & authorization** (JWT or OAuth2)
- **Admin dashboard** with analytics and candidate pipeline management
- **Export to CSV/Excel**
- **LinkedIn profile enrichment** via external APIs
- **Webhook notifications** when a new candidate is parsed

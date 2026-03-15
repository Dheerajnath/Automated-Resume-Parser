import re
import spacy

# Load the spaCy English model (must be installed: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise RuntimeError(
        "spaCy model 'en_core_web_sm' not found. "
        "Run: python -m spacy download en_core_web_sm"
    )

# Predefined skill list (case-insensitive matching)
SKILL_LIST = [
    "Python", "Java", "C++", "C#", "C", "JavaScript", "TypeScript", "Go", "Rust", "Ruby",
    "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB",
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "SQLite",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Data Science",
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "OpenCV",
    "Flask", "Django", "FastAPI", "Spring Boot", "Express", "Rails",
    "React", "Angular", "Vue.js", "Node.js", "Next.js",
    "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins",
    "AWS", "Azure", "GCP", "Google Cloud",
    "Git", "GitHub", "GitLab", "Bitbucket",
    "Linux", "Unix", "Bash", "Shell Scripting",
    "Pandas", "NumPy", "Matplotlib", "Seaborn", "SciPy",
    "Power BI", "Tableau", "Looker", "Excel",
    "REST API", "GraphQL", "Microservices", "CI/CD",
    "HTML", "CSS", "SASS",
]

# Education keywords to detect
EDUCATION_KEYWORDS = [
    r"B\.?Tech", r"M\.?Tech", r"B\.?Sc", r"M\.?Sc", r"BE\b", r"ME\b",
    r"MBA", r"PhD", r"Ph\.D", r"B\.?E\b", r"M\.?E\b",
    r"Bachelor", r"Master", r"Doctorate", r"Diploma", r"Associate",
    r"B\.?A\b", r"M\.?A\b", r"BCA", r"MCA",
]


def extract_email(text: str) -> str | None:
    """Extract email address using regex."""
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    """Extract phone number using regex. Handles various formats."""
    pattern = r"(\+?\d{1,3}[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}"
    match = re.search(pattern, text)
    return match.group(0).strip() if match else None


def extract_name(text: str) -> str | None:
    """
    Extract full name using spaCy NER (PERSON entity).
    Returns the first PERSON entity found in the first 500 characters,
    which is usually the candidate's name at the top of the resume.
    """
    # Focus on the top portion of the resume for name extraction
    header_text = text[:500]
    doc = nlp(header_text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()
    return None


def extract_skills(text: str) -> list[str]:
    """
    Extract skills from resume text using case-insensitive matching
    against the predefined SKILL_LIST.
    """
    found_skills = []
    text_lower = text.lower()
    for skill in SKILL_LIST:
        # Use word boundary matching for accurate detection
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found_skills.append(skill)
    return found_skills


def extract_education(text: str) -> str | None:
    """
    Extract education details by finding lines that contain education keywords.
    Returns a summary string of education-related lines.
    """
    lines = text.split("\n")
    education_lines = []
    for line in lines:
        for keyword in EDUCATION_KEYWORDS:
            if re.search(keyword, line, re.IGNORECASE):
                cleaned = line.strip()
                if cleaned and cleaned not in education_lines:
                    education_lines.append(cleaned)
                break  # Avoid duplicating the same line for multiple keyword matches
    return "; ".join(education_lines) if education_lines else None


def extract_experience_summary(text: str) -> str | None:
    """
    Extract experience-related text using spaCy NER for ORG entities,
    combined with heuristic section detection.
    Returns a summary of found organizations/experience sections.
    """
    # Try to find an experience section using common headers
    section_pattern = re.compile(
        r"(experience|work history|employment|professional background)[^\n]*\n(.*?)(?=\n[A-Z][A-Z\s]{3,}:|$)",
        re.IGNORECASE | re.DOTALL,
    )
    match = section_pattern.search(text)
    if match:
        section_text = match.group(2).strip()
        # Return first 500 characters of the experience section
        return section_text[:500] if len(section_text) > 500 else section_text

    # Fallback: use spaCy to extract ORG entities as hints
    doc = nlp(text[:2000])  # Limit for performance
    orgs = list({ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"})
    if orgs:
        return "Organizations mentioned: " + ", ".join(orgs[:5])

    return None


def extract_all(text: str) -> dict:
    """
    Run all NLP extractors on the given text.
    Returns a dictionary with all extracted fields.
    """
    return {
        "full_name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience_summary": extract_experience_summary(text),
    }

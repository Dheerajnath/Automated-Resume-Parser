from datetime import datetime
from . import db


# Association table for many-to-many relationship between candidates and skills
candidate_skills = db.Table(
    "candidate_skills",
    db.Column("id", db.Integer, primary_key=True),
    db.Column(
        "candidate_id",
        db.Integer,
        db.ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
    ),
    db.Column(
        "skill_id",
        db.Integer,
        db.ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    ),
)


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    education = db.Column(db.Text, nullable=True)
    experience_summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Many-to-many relationship with skills
    skills = db.relationship(
        "Skill",
        secondary=candidate_skills,
        backref=db.backref("candidates", lazy="dynamic"),
        lazy="subquery",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "education": self.education,
            "experience_summary": self.experience_summary,
            "skills": [skill.skill_name for skill in self.skills],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(100), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "skill_name": self.skill_name}

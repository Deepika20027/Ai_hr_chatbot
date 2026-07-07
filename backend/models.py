# backend/models.py

from datetime import datetime
# Corrected import: Use absolute import for db
from database import db # Import the db instance from database.py
from werkzeug.security import generate_password_hash, check_password_hash
import uuid # For generating unique IDs

class User(db.Model):
    """
    Represents a user in the system, either a candidate or a recruiter.
    """
    # Using String(36) to store UUIDs, which are better for distributed systems
    # and don't expose sequential user IDs.
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='candidate') # 'candidate' or 'recruiter'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to CandidateScreening (one-to-one for candidates)
    # lazy='joined' means the related CandidateScreening will be loaded with the User
    # uselist=False indicates a one-to-one relationship (one user has one screening record)
    screening = db.relationship('CandidateScreening', backref='candidate_user', lazy=True, uselist=False)

    def set_password(self, password):
        """Hashes the given password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

class CandidateScreening(db.Model):
    """
    Stores the screening data for a candidate, including questions, answers, and score.
    """
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Foreign Key linking to the User table
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), unique=True, nullable=False)
    # Storing questions and answers as JSON string (Text type for potentially long strings)
    # This allows flexibility in the structure of Q&A pairs.
    questions_answers_json = db.Column(db.Text, nullable=False)
    average_score = db.Column(db.Float, nullable=True)
    # Status of the candidate's screening: 'pending', 'completed', 'selected', 'rejected'
    status = db.Column(db.String(20), nullable=False, default='pending')
    completed_at = db.Column(db.DateTime, nullable=True)
    # Automatically updates timestamp on record modification
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CandidateScreening UserID: {self.user_id} Status: {self.status}>"

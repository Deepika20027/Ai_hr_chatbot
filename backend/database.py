# backend/database.py

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy. This 'db' object is the core of your database integration.
# It will be bound to your Flask application later.
db = SQLAlchemy()

# backend/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the base directory of the project (where app.py will be)
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Base configuration class for the Flask application.
    Contains common configuration settings.
    """
    # Flask Secret Key: Used for session management and other security features.
    # It's crucial to set this via an environment variable in production.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_fallback_secret_key_if_env_not_set'

    # SQLAlchemy Database URI: Defines the connection string to your database.
    # For SQLite, it points to a file. The 'instance' folder is a common Flask pattern
    # for storing instance-specific files like databases.
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'site.db')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:admin@localhost/ai_hr_chatbot'
    # Disable SQLAlchemy event system tracking, which can save memory.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google Gemini API Key: Loaded from environment variable for security.
    # This key will be used to authenticate requests to the Gemini API for AI generation.
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    # Base URL for the Gemini API (using gemini-2.0-flash model)
    GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

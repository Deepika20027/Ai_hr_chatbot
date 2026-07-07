# backend/init_db.py

import os
import sys
from flask import Flask

# --- BEGIN IMPORT FIX ---
# Explicitly add the directory containing this script (which should be 'backend/')
# to the Python path. This helps resolve imports when running the script directly.
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
# --- END IMPORT FIX ---

# Now, import modules as if 'backend' is the top-level package
# These should now work as 'backend.config', 'backend.database', 'backend.models'
from config import Config
from database import db
from models import User, CandidateScreening # Import your models

def create_app():
    """
    Creates a minimal Flask application instance for database initialization.
    This is necessary because SQLAlchemy's 'db.create_all()' needs an active
    Flask application context to know which database to connect to.
    """
    app = Flask(__name__)
    app.config.from_object(Config) # Load configuration from Config class
    db.init_app(app) # Initialize SQLAlchemy with the Flask app
    return app

def init_db():
    """
    Initializes the database: ensures the 'instance' directory exists,
    and then creates all tables defined in your SQLAlchemy models.
    """
    app = create_app()
    with app.app_context(): # Activates the Flask application context
        # Define the path to the instance folder
        # app.root_path is the directory where the Flask app module is located (i.e., backend/)
        instance_path = os.path.join(app.root_path, 'instance')
        # Create the 'instance' directory if it doesn't already exist
        os.makedirs(instance_path, exist_ok=True)

        # Construct the full path to the SQLite database file
        db_path = os.path.join(instance_path, 'site.db')

        # Check if the database file already exists to avoid overwriting
        if os.path.exists(db_path):
            print(f"Database '{db_path}' already exists. Skipping creation.")
            print("If you want to recreate it (and lose all data), delete the 'site.db' file first.")
        else:
            print(f"Creating database tables in '{db_path}'...")
            # This is the SQLAlchemy command that creates all tables
            # defined as db.Model subclasses.
            db.create_all()
            print("Database tables created successfully.")

if __name__ == '__main__':
    # This block ensures that init_db() is called only when the script is executed directly.
    # To run this script:
    # 1. Navigate to your 'backend' directory in your terminal.
    # 2. Make sure your Python virtual environment is activated.
    # 3. Run the script using: python -m init_db
    init_db()

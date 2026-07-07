# backend/app.py

import os
import uuid
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import random # Still useful for initial testing or fallback, but actual scoring will use AI

# Import your configuration, database, and models
from config import Config
from database import db
from models import User, CandidateScreening

# --- Flask App Initialization ---
def create_app():
    """
    Creates and configures the Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app)

    return app

app = create_app()

# --- Helper Function for Gemini API Call (Question Generation - existing) ---
def generate_gemini_questions():
    """
    Calls the Google Gemini API to generate 10 HR screening questions.
    """
    api_key = app.config.get('GEMINI_API_KEY')
    api_url = app.config.get('GEMINI_API_BASE_URL')

    if not api_key:
        app.logger.error("GEMINI_API_KEY is not set in config.")
        return {"error": "API key not configured."}, 500

    if not api_url:
        app.logger.error("GEMINI_API_BASE_URL is not set in config.")
        return {"error": "Gemini API URL not configured."}, 500

    prompt = "Generate a list of 10 common HR screening interview questions. Provide them as a JSON array of strings, like `[\"Question 1\", \"Question 2\", ...]`"
    chat_history = [{ "role": "user", "parts": [{ "text": prompt }] }]

    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "items": { "type": "STRING" }
            }
        }
    }

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(f"{api_url}?key={api_key}", headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        if result.get('candidates') and len(result['candidates']) > 0 and \
           result['candidates'][0].get('content') and \
           result['candidates'][0]['content'].get('parts') and \
           len(result['candidates'][0]['content']['parts']) > 0:
            
            json_string = result['candidates'][0]['content']['parts'][0]['text']
            parsed_questions = json.loads(json_string)

            if isinstance(parsed_questions, list) and len(parsed_questions) == 10:
                return {"questions": parsed_questions}, 200
            else:
                app.logger.warning(f"Gemini API returned unexpected format or count for questions: {parsed_questions}")
                return {"error": "Failed to generate 10 questions in expected format. Please try again."}, 500
        else:
            app.logger.warning(f"Gemini API response structure unexpected for questions: {result}")
            return {"error": "Failed to generate questions. Unexpected API response structure."}, 500

    except requests.exceptions.HTTPError as http_err:
        app.logger.error(f"HTTP error occurred during question generation: {http_err} - Response: {http_err.response.text}")
        return {"error": f"Gemini API HTTP error during question generation: {http_err.response.text}"}, http_err.response.status_code
    except requests.exceptions.ConnectionError as conn_err:
        app.logger.error(f"Connection error occurred during question generation: {conn_err}")
        return {"error": "Network error connecting to Gemini API for questions. Please check your connection."}, 503
    except requests.exceptions.Timeout as timeout_err:
        app.logger.error(f"Timeout error occurred during question generation: {timeout_err}")
        return {"error": "Gemini API request timed out for questions."}, 504
    except requests.exceptions.RequestException as req_err:
        app.logger.error(f"An unexpected error occurred during question generation request: {req_err}")
        return {"error": f"An error occurred while calling Gemini API for questions: {req_err}"}, 500
    except json.JSONDecodeError as json_err:
        app.logger.error(f"JSON decode error from Gemini API response for questions: {json_err} - Raw: {response.text}")
        return {"error": "Failed to parse Gemini API response for questions."}, 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred in generate_gemini_questions: {e}")
        return {"error": "An internal server error occurred during question generation."}, 500


# --- NEW Helper Function for Gemini API Call (Answer Evaluation) ---
def evaluate_answer_with_gemini(question, answer):
    """
    Calls the Google Gemini API to evaluate a candidate's answer for a given question.
    Returns a score out of 5 and a brief justification.
    """
    api_key = app.config.get('GEMINI_API_KEY')
    api_url = app.config.get('GEMINI_API_BASE_URL')

    if not api_key or not api_url:
        app.logger.error("Gemini API key or URL not configured for evaluation.")
        return 0.0, "API configuration error."

    # Prompt Engineering for Answer Evaluation
    # We ask for a JSON response to easily parse the score and justification.
    prompt = f"""
    You are an HR interview assistant. Evaluate the following candidate's answer to an interview question.
    Provide a score between 1.0 and 5.0 (inclusive, allowing decimals) and a brief justification for the score.

    Question: "{question}"
    Candidate's Answer: "{answer}"

    Consider factors like:
    - Relevance to the question
    - Clarity and coherence
    - Depth and insight
    - Professionalism
    - Conciseness

    Respond ONLY with a JSON object in the following format:
    {{
      "score": <float_score_out_of_5>,
      "justification": "<brief_text_justification>"
    }}
    """

    chat_history = [{ "role": "user", "parts": [{ "text": prompt }] }]

    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "score": { "type": "NUMBER" },
                    "justification": { "type": "STRING" }
                },
                "required": ["score", "justification"]
            },
            "temperature": 0.2, # Lower temperature for more consistent scoring
            "maxOutputTokens": 200 # Limit response length
        }
    }

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(f"{api_url}?key={api_key}", headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        if result.get('candidates') and len(result['candidates']) > 0 and \
           result['candidates'][0].get('content') and \
           result['candidates'][0]['content'].get('parts') and \
           len(result['candidates'][0]['content']['parts']) > 0:
            
            json_string = result['candidates'][0]['content']['parts'][0]['text']
            parsed_evaluation = json.loads(json_string)

            score = float(parsed_evaluation.get('score', 0.0))
            justification = parsed_evaluation.get('justification', "No justification provided.")

            # Ensure score is within bounds
            score = max(1.0, min(5.0, score))

            return score, justification
        else:
            app.logger.warning(f"Gemini API response structure unexpected for evaluation: {result}")
            return 0.0, "Unexpected API response structure for evaluation."

    except requests.exceptions.HTTPError as http_err:
        app.logger.error(f"HTTP error during answer evaluation: {http_err} - Response: {http_err.response.text}")
        return 0.0, f"API HTTP error: {http_err.response.text}"
    except requests.exceptions.ConnectionError as conn_err:
        app.logger.error(f"Connection error during answer evaluation: {conn_err}")
        return 0.0, "Network error during evaluation."
    except requests.exceptions.Timeout as timeout_err:
        app.logger.error(f"Timeout error during answer evaluation: {timeout_err}")
        return 0.0, "API request timed out during evaluation."
    except requests.exceptions.RequestException as req_err:
        app.logger.error(f"An unexpected error occurred during evaluation request: {req_err}")
        return 0.0, f"An error occurred during evaluation: {req_err}"
    except json.JSONDecodeError as json_err:
        app.logger.error(f"JSON decode error from Gemini API response for evaluation: {json_err} - Raw: {response.text}")
        return 0.0, "Failed to parse API response for evaluation."
    except Exception as e:
        app.logger.error(f"An unexpected error occurred in evaluate_answer_with_gemini: {e}")
        return 0.0, f"Internal server error during evaluation: {e}"


# --- API Routes ---

@app.route('/api/signup', methods=['POST'])
def signup():
    """
    Handles user registration for both candidates and recruiters.
    Expects JSON: {'email', 'password', 'role'}
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not email or not password or not role:
        return jsonify({"message": "Email, password, and role are required"}), 400

    if role not in ['candidate', 'recruiter']:
        return jsonify({"message": "Invalid role specified"}), 400

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "User with this email already exists"}), 409 # Conflict

    try:
        new_user = User(id=str(uuid.uuid4()), email=email, role=role)
        new_user.set_password(password) # Hash the password
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully", "user_id": new_user.id, "role": new_user.role}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error during signup: {e}")
        return jsonify({"message": "Internal server error during signup"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """
    Handles user login.
    Expects JSON: {'email', 'password'}
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        return jsonify({"message": "Login successful", "user_id": user.id, "email": user.email, "role": user.role}), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 401 # Unauthorized

# --- Candidate Routes ---

@app.route('/api/candidate/dashboard/<user_id>', methods=['GET'])
def candidate_dashboard(user_id):
    """
    Retrieves candidate dashboard info, including screening status.
    """
    user = User.query.get(user_id)
    if not user or user.role != 'candidate':
        return jsonify({"message": "Candidate not found or unauthorized"}), 404

    screening = CandidateScreening.query.filter_by(user_id=user_id).first()
    status = screening.status if screening else 'not_started'

    return jsonify({"user_id": user.id, "email": user.email, "screening_status": status}), 200


@app.route('/api/candidate/start_screening', methods=['GET'])
def start_screening():
    """
    Generates and returns 10 HR screening questions using Gemini API.
    """
    questions_response, status_code = generate_gemini_questions()
    return jsonify(questions_response), status_code


@app.route('/api/candidate/submit_screening', methods=['POST'])
def submit_screening():
    """
    Receives candidate's answers, sends them to Gemini for evaluation,
    and saves the screening data with the actual scores to the database.
    Expects JSON: {'user_id', 'email', 'answers': [{'question', 'answer'}]}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    email = data.get('email')
    answers_list = data.get('answers')

    if not user_id or not email or not answers_list:
        return jsonify({"message": "Missing user_id, email, or answers"}), 400

    user = User.query.get(user_id)
    if not user or user.role != 'candidate':
        return jsonify({"message": "Candidate not found or unauthorized"}), 404

    if len(answers_list) != 10:
        return jsonify({"message": "Expected 10 answers for screening"}), 400

    processed_answers = []
    total_score = 0
    
    # Iterate through each question-answer pair and evaluate with Gemini
    for i, qa in enumerate(answers_list):
        question = qa.get('question')
        answer = qa.get('answer')
        
        if not question or not answer:
            app.logger.warning(f"Skipping malformed QA pair at index {i}: {qa}")
            # Optionally, return an error or assign a default score
            processed_answers.append({'question': question, 'answer': answer, 'score': 0.0, 'justification': 'Malformed input.'})
            continue # Skip to next QA if malformed

        # Call the Gemini evaluation helper function
        score, justification = evaluate_answer_with_gemini(question, answer)
        
        processed_answers.append({
            'question': question,
            'answer': answer,
            'score': round(score, 2), # Round score for storage
            'justification': justification
        })
        total_score += score

    average_score = round(total_score / len(processed_answers), 2) if processed_answers else 0

    try:
        screening = CandidateScreening.query.filter_by(user_id=user_id).first()

        if screening:
            screening.questions_answers_json = json.dumps(processed_answers)
            screening.average_score = average_score
            screening.status = 'completed'
            screening.completed_at = datetime.utcnow()
        else:
            screening = CandidateScreening(
                id=str(uuid.uuid4()),
                user_id=user_id,
                questions_answers_json=json.dumps(processed_answers),
                average_score=average_score,
                status='completed',
                completed_at=datetime.utcnow()
            )
            db.session.add(screening)

        db.session.commit()
        return jsonify({"message": "Screening completed and data saved successfully", "average_score": average_score}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving screening data after AI evaluation: {e}")
        return jsonify({"message": "Internal server error saving screening data"}), 500

# --- Recruiter Routes ---

@app.route('/api/recruiter/candidates', methods=['GET'])
def get_all_candidates():
    """
    Retrieves all candidates with or without screening.
    """
    candidates = User.query.filter_by(role='candidate').all()
    result = []

    for user in candidates:
        screening = CandidateScreening.query.filter_by(user_id=user.id).first()

        result.append({
            "id": user.id,
            "email": user.email,
            "name": user.email.split('@')[0],
            "average_score": screening.average_score if screening else None,
            "status": screening.status if screening else "not_started",
            "completed_at": screening.completed_at.isoformat() if screening and screening.completed_at else None
        })

    return jsonify(result), 200

@app.route('/api/recruiter/candidate/<user_id>', methods=['GET'])
def get_candidate_details(user_id):
    """
    Retrieves detailed screening information for a specific candidate.
    """
    user = User.query.get(user_id)
    if not user or user.role != 'candidate':
        return jsonify({"message": "Candidate not found or unauthorized"}), 404

    screening = CandidateScreening.query.filter_by(user_id=user_id).first()
    if not screening:
        return jsonify({"message": "Screening data not found for this candidate"}), 404

    questions_answers = json.loads(screening.questions_answers_json)

    candidate_details = {
        "id": user.id,
        "email": user.email,
        "name": user.email.split('@')[0],
        "average_score": screening.average_score,
        "status": screening.status,
        "completed_at": screening.completed_at.isoformat() if screening.completed_at else None,
        "questions_answers": questions_answers # Now includes score and justification
    }
    return jsonify(candidate_details), 200

@app.route('/api/recruiter/candidate/<user_id>/status', methods=['PUT'])
def update_candidate_status(user_id):
    """
    Updates the status of a candidate's screening.
    Expects JSON: {'status': 'selected' or 'rejected'}
    """
    data = request.get_json()
    new_status = data.get('status')

    if new_status not in ['selected', 'rejected']:
        return jsonify({"message": "Invalid status. Must be 'selected' or 'rejected'"}), 400

    screening = CandidateScreening.query.filter_by(user_id=user_id).first()
    if not screening:
        return jsonify({"message": "Screening data not found for this candidate"}), 404

    try:
        screening.status = new_status
        screening.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Candidate status updated successfully", "new_status": new_status}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating candidate status: {e}")
        return jsonify({"message": "Internal server error updating status"}), 500

# --- Run the Flask App ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)

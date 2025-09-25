# Import the necessary libraries
from flask import Flask, request, render_template
from twilio.twiml.messaging_response import MessagingResponse
import os
from google.cloud import dialogflow_v2 as dialogflow
import json

# Create a new Flask application
app = Flask(__name__)

# Set the environment variable to point to your downloaded JSON key file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "private-key.json"


# --- CORRECTED FUNCTION ---
# Single function to connect to Dialogflow, which can return the full response if needed
def detect_intent_texts(project_id, session_id, text, language_code, return_full_response=False):
    """Returns the bot's response from Dialogflow."""
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    try:
        response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )
        if return_full_response:
            return response
        return response.query_result.fulfillment_text
    except Exception as e:
        print(f"Error connecting to Dialogflow: {e}")
        return "Sorry, I am having trouble connecting to my brain right now."


@app.route('/')
def index():
    return render_template("index.html")


# This function reads from your local 'database'
def get_outbreak_alert(city):
    with open('health_data.json', 'r') as f:
        data = json.load(f)
    alert = data['outbreak_alerts'].get(city.lower(), "No specific alerts for your area right now.")
    return alert


# --- CORRECTED FUNCTION ---
# Single webhook with the correct logic for handling regular intents and the outbreak alert
@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower()
    print(f"Incoming message from WhatsApp: {incoming_msg}")

    project_id = "medex-eckj"
    session_id = request.values.get('From', '')

    # Get the full response from Dialogflow to check the intent name
    response = detect_intent_texts(project_id, session_id, incoming_msg, 'en-US', return_full_response=True)

    # Check if the response is a string (an error message) or the full object
    if isinstance(response, str):
        bot_response = response
    else:
        intent_name = response.query_result.intent.display_name
        bot_response = response.query_result.fulfillment_text

        # If the outbreak intent is matched, override the bot_response
        if intent_name == 'Outbreak-Alert':
            # For the demo, we are hardcoding the city
            city = "kochi"
            bot_response = get_outbreak_alert(city)

    print(f"Bot's response: {bot_response}")

    # Create and send the final reply
    resp = MessagingResponse()
    resp.message(bot_response)
    return str(resp)


# This line is needed to run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
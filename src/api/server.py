import datetime
import os
import json
import logging

from flask import Flask, request, jsonify
from google.cloud import pubsub_v1
from dotenv import load_dotenv
from google.api_core.exceptions import NotFound

# Imports the Cloud Logging client library
import google.cloud.logging

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

app = Flask(__name__)

# Replace 'your-project-id' and 'your-topic-name' with your Google Cloud project ID and Pub/Sub topic name
credential_path = os.getenv("CREDENTIAL_PATH")
project_id = os.getenv("PROJECT_ID")
valid_pubsub = os.getenv("VALID_PUBSUB_TOPIC")
invalid_pubsub = os.getenv("INVALID_PUBSUB_TOPIC")

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

# Instantiates a client
gcp_logging_client = google.cloud.logging.Client()
gcp_logging_client.setup_logging()

publisher = pubsub_v1.PublisherClient()
valid_topic_path = publisher.topic_path(project_id, valid_pubsub)
invalid_topic_path = publisher.topic_path(project_id, invalid_pubsub)


@app.route('/publish', methods=['POST'])
def publish_message():
    body = request.json

    try:
        if 'table_name' not in body:
            error = 'Missing "table_name" parameter'
            invalid_data = {
                "data": body,
                "error": error,
                "timestamp": datetime.datetime.now().timestamp()
            }
            publisher.publish(invalid_topic_path, data=json.dumps(invalid_data).encode('utf-8'))
            logging.error(error)
            return jsonify({'error': error}), 400

        if 'data' not in body:
            error = 'Missing "data" parameter'
            invalid_data = {
                "data": body,
                "error": error,
                "timestamp": datetime.datetime.now().timestamp()
            }
            publisher.publish(invalid_topic_path, data=json.dumps(invalid_data).encode('utf-8'))
            logging.error(error)
            return jsonify({'error': error}), 400


        # Publish the message to Pub/Sub
        future = publisher.publish(valid_topic_path, data=json.dumps(body).encode())
        message_id = future.result()

        return jsonify({'message_id': message_id}), 200

    except NotFound as nf:
        logging.exception(f"Exception raised: resource not found {nf}")
    except Exception as e:
        logging.exception(f"Exception Raised: {e}")

@app.route('/publish', methods=['GET'])
def publish_message_get():
    return "publish api"

if __name__ == '__main__':
    app.run(debug=True, port=8080)

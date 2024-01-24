FROM python:3.11-slim

WORKDIR /app

RUN pip install google-cloud-logging==3.8.0 Flask google-cloud-pubsub python-dotenv gunicorn

#COPY ./credentials.json /app
COPY src/api /app
#COPY .env /app


# Set environment variables (ensure you set these correctly for your environment)
ENV CREDENTIAL_PATH=/app/credentials.json
ENV PROJECT_ID="gcp-demo-telemetry"
ENV VALID_PUBSUB_TOPIC="demoValidDataTopic"
ENV INVALID_PUBSUB_TOPIC="demoInvalidDataTopic"

# Expose port 5000
EXPOSE 8080

# Run the Flask app in production mode
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
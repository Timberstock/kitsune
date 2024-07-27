# Use a smaller base image
FROM python:3.10-slim

# To get prints  correctly?
ENV PYTHONUNBUFFERED True

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Copy the service account key file
COPY timberstock-firebase-adminsdk-credentials.json /app/service_account_key.json

# Set the environment variable for the service account key
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/service_account_key.json"


# Install WeasyPrint dependencies
RUN apt-get update && apt-get -y install build-essential python3-dev python3-pip \
    python3-setuptools python3-wheel python3-cffi \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# EXPOSE port 8080 to allow communication to/from server
EXPOSE 8080

# Set the entrypoint to run your FastAPI application
CMD ["uvicorn", "kitsune_app.main:app", "--host", "0.0.0.0", "--port", "8080"]
# Use an official Python runtime as the base image
FROM python:3.10-slim

# Create a virtualenv for dependencies. This isolates these packages from
# system-level packages.
# Use -p python3 or -p python3.7 to select python version. Default is version 2.
RUN python3 -m venv /venv

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV VIRTUAL_ENV /venv
ENV PATH /venv/bin:$PATH

# Install platform's packages required for WeasyPrint
RUN apt-get update && apt-get -y install build-essential python3-dev python3-pip \
python3-setuptools python3-wheel python3-cffi \
libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# Copy the application's requirements.txt and run pip to install all
# dependencies into the virtualenv.
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Add the application source code, and move there
ADD . /app/kitsune_app
WORKDIR /app/kitsune_app

# Run a WSGI server to serve the application. uvicorn must be declared as
# a dependency in requirements.txt.
# We use uvicorn WSGI server to serve the application. We specify this --host
# because, given this now on a container, default (127.0.0.1) means "only listen
# for connections from the same machine (container in this case)". While 0.0.0.0
# means "listen for all connections" (including the host, i.e a different "machine").

# This is for development
# CMD ["uvicorn", "kitsune_app.main:app", "--host", "0.0.0.0", "--reload"]

# This would be for production
# CMD ["uvicorn", "kitsune_app.main:app", "--host", "0.0.0.0"]

CMD gunicorn -w 4 -k uvicorn.workers.UvicornWorker kitsune_app.main:app
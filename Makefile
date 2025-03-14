# Deploy the app to Google Cloud Run.
.PHONY: deploy
deploy:
	$(info Make sure the project is correctly set with the correct ACCOUNT, PROJECT_ID and REGION)
	gcloud run deploy kitsune-api --port 8080 --source .

# Run the app locally using docker-compose
# Requests to the app will be served at http://localhost:8180/
# To develop, remember to use the Dev Containers in VSCode extension, and attach VSCode to the running container so we can explore the libraries and the code
# as it is installed in the container itself (e.g. we can explore firebase_admin library and get code suggestions)
.PHONY: docker-compose-up
docker-compose-up:
	docker compose up

# Build with docker-compose
.PHONY: docker-compose-build
docker-compose-build:
	docker compose build

# Open a shell inside the container
.PHONY: docker-shell
docker-shell:
	docker exec -it kitsune_container bash


# Linters
# Must be run inside a venv with the requirements installed
# =======
.PHONY: black
black:
	black ./kitsune_app/

.PHONY: black!
black!:
	black ./kitsune_app/ --check

.PHONY: flake8
flake8:
	flake8 ./kitsune_app/

.PHONY: isort
isort:
	isort ./kitsune_app/

.PHONY: isort!
isort!:
	isort ./kitsune_app/ --check-only

.PHONY: mypy
mypy:
	mypy \
	./kitsune_app/middlewares \
	./kitsune_app/routers \
	./kitsune_app/utils \
	./kitsune_app/main.py \
	./kitsune_app/settings.py


# Run linters
.PHONY: pylinters
pylinters:
	make black flake8 isort mypy

.PHONY: pylinters!
pylinters!:
	make black! flake8 isort! mypy




# Deprecated commands

# (deprecated, should use docker compose now)
# Run dockerized app locally (this is while we don't have a docker-compose file, since it doesn't take long to build the image)
# We need to have the firebase credentials file one level up from the project folder
.PHONY: docker-build-and-run
docker-build-and-run:
	docker build -t kitsune_image .
	docker run -p 8000:8000 \
	-e GOOGLE_APPLICATION_CREDENTIALS=/firebase-adminsdk-credentials.json \
	-v $(shell pwd)/../timberstock-firebase-adminsdk-credentials.json:/firebase-adminsdk-credentials.json \
	-v $(shell pwd):/app \
	--name kitsune_container kitsune_image

# Restart docker by stoping and removing container and image (deprecated, should use docker-compose now)
.PHONY: restart-docker-clean
restart-docker-clean:
	docker stop kitsune_container
	docker rm kitsune_container
	docker rmi kitsune_image

# Run the app locally (deprecated, should use docker now)
.PHONY: local-server
local-server-deprecated:
	. .venv/bin/activate; uvicorn kitsune_app.main:app --reload
	

# Setup the project (deprecated, should use docker now)
.PHONY: setup
setup:
	pip install -r requirements.txt
	

# Cleanup the project (deprecated, should use docker now)
.PHONY: restart
restart:
	rm -rf __pycache__
	rm -rf .venv
	python3 -m venv .venv
	. .venv/bin/activate; pip install -r requirements.txt


	

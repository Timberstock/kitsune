# Useful commands
	
# Run the app locally
.PHONY: local-server
local-server:
	. .venv/bin/activate; uvicorn kitsune_app.main:app --reload
	

# Setup the project
.PHONY: setup
setup:
	pip install -r requirements.txt
	

# Cleanup the project
.PHONY: restart
restart:
	rm -rf __pycache__
	rm -rf .venv
	python3 -m venv .venv
	. .venv/bin/activate; pip install -r requirements.txt


# Deploy the app to Google App Engine
.PHONY: deploy
deploy:
	gcloud app deploy
	



# Linters
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
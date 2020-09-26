PATH:=bin/:${PATH}
.PHONY: update-deps init update clean test mysql dropdb createdb redis celery run build push

API_IMAGE = lsstsqre/squash-api

help:
	@echo "Available commands:"
	@echo "  update-deps update dependencies"
	@echo "  init    install develop version"
	@echo "  update  update dependencies and install develop version"
	@echo "  clean			remove temp files"
	@echo "  test			run tests and generate test coverage"
	@echo "  mysql  		start mysql for development"
	@echo "  dropdb       		drop dev and test databases"
	@echo "  createdb       	create dev and test databases"
	@echo "  redis			run redis container for development"
	@echo "  celery			start celery worker in development mode"
	@echo "  run			run tests and run the app in development mode"
	@echo "  build          build squash-api docker image"
	@echo "  push           push docker images to docker hub"


update-deps:
		pip install --upgrade pip-tools pip setuptools
		pip-compile --upgrade --build-isolation --generate-hashes --output-file requirements/main.txt requirements/main.in
		pip-compile --upgrade --build-isolation --generate-hashes --output-file requirements/dev.txt requirements/dev.in
		pip-sync requirements/main.txt requirements/dev.txt

init:
		pip install --editable .
		pip install --upgrade -r requirements/main.txt -r requirements/dev.txt
		rm -rf .tox
		pip install --upgrade tox
		pre-commit install

update: update-deps init


clean:
	find ./ -type f -name '*.pyc' -exec rm -f {} \;
	rm -rf .coverage*
	rm -rf .cache
	rm -rf .tox
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf dist
	rm -rf build

test:
	flake8 app tests
	coverage run --source=app test.py

mysql: check-squash-db-credentials
	docker run --rm --name mysql -e MYSQL_ROOT_PASSWORD=${SQUASH_DB_PASSWORD} -p 3306:3306 -d mysql:5.7

dropdb: check-squash-db-credentials
	docker exec mysql sh -c "MYSQL_PWD=${SQUASH_DB_PASSWORD} mysql -e 'DROP DATABASE squash_dev'"
	docker exec mysql sh -c "MYSQL_PWD=${SQUASH_DB_PASSWORD} mysql -e 'DROP DATABASE squash_test'"

createdb: check-squash-db-credentials
	docker exec mysql sh -c "MYSQL_PWD=${SQUASH_DB_PASSWORD} mysql -e 'CREATE DATABASE squash_dev'"
	docker exec mysql sh -c "MYSQL_PWD=${SQUASH_DB_PASSWORD} mysql -e 'CREATE DATABASE squash_test'"

redis:
	docker run --rm --name redis -p 6379:6379 redis

celery: check-aws-credentials
	celery -A app.tasks -E -l DEBUG worker

run: test
	flask run

build: check-tag
	docker build -t $(API_IMAGE):${TAG} .

push: check-tag
	docker push $(API_IMAGE):${TAG}

check-tag:
	@if test -z ${TAG}; then echo "Error: TAG is undefined."; exit 1; fi

check-squash-db-credentials:
	@if test -z ${SQUASH_DB_PASSWORD}; then echo "Error: SQUASH_DB_PASSWORD is undefined."; exit 1; fi

check-aws-credentials:
	@if [ -z ${AWS_ACCESS_KEY_ID} ]; \
	then echo "Error: AWS_ACCESS_KEY_ID is undefined."; \
  	exit 1; \
  fi
	@if [ -z ${AWS_SECRET_ACCESS_KEY} ]; \
  then echo "Error: AWS_SECRET_ACCESS_KEY is undefined."; \
    exit 1; \
  fi

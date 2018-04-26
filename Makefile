PATH:=bin/:${PATH}
.PHONY: clean test mysql redis celery run mysql-secret build push configmap deployment\
service check-tag check-cloudsql-credentials check-squash-db-password

MYSQL_PASSWD = passwd.txt
API = lsstsqre/squash-restful-api
NGINX = lsstsqre/squash-restful-api-nginx
NGINX_CONFIG = kubernetes/nginx/nginx.conf
DEPLOYMENT_TEMPLATE = kubernetes/deployment-template.yaml
DEPLOYMENT_CONFIG = kubernetes/deployment.yaml
SERVICE_CONFIG = kubernetes/service.yaml
REPLACE = ./kubernetes/replace.sh

help:
	@echo "Available commands:"
	@echo "  clean			remove temp files"
	@echo "  test			run tests and generate test coverage"
	@echo "  mysql  		start mysql for development"
	@echo "  db       		(re)create dev and test databases"
	@echo "  redis			run redis container for development"
	@echo "  celery			start celery worker in development mode"
	@echo "  run			run tests and run the app in development mode"
	@echo "  cloudsql-secret create secrets with cloud sql proxy key and db password"
	@echo "  aws-secret     create secret with aws credentials"
	@echo "  s3-bucket      create the S3 Bucket for this deployment"
	@echo "  build          build squash-restful-api and nginx docker images"
	@echo "  push           push docker images to docker hub"
	@echo "  configmap      create configmap for customized nginx configuration"
	@echo "  deployment     create kubernetes deployment"
	@echo "  service        create kubernetes service"

clean:
	find ./ -type f -name '*.pyc' -exec rm -f {} \;
	rm -rf .coverage
	rm -rf .cache

test:
	flake8 app tests
	coverage run --source=app test.py

mysql: check-squash-db-credentials
	docker run --rm --name mysql -e MYSQL_ROOT_PASSWORD=${SQUASH_DB_PASSWORD} -p 3306:3306 -d mysql:5.7

dropdb: check-squash-db-credentials
	docker exec mysql sh -c "mysql -p${SQUASH_DB_PASSWORD} -e 'DROP DATABASE squash_dev'"
	docker exec mysql sh -c "mysql -p${SQUASH_DB_PASSWORD} -e 'DROP DATABASE squash_test'"

createdb: check-squash-db-credentials
	docker exec mysql sh -c "mysql -p${SQUASH_DB_PASSWORD} -e 'CREATE DATABASE squash_dev'"
	docker exec mysql sh -c "mysql -p${SQUASH_DB_PASSWORD} -e 'CREATE DATABASE squash_test'"

redis:
	docker run --rm --name redis -p 6379:6379 redis

s3-bucket: check-aws-credentials check-namespace
	aws s3api create-bucket --bucket squash-${NAMESPACE}.data --region us-east-1

celery: check-aws-credentials
	celery -A app.tasks -E -l DEBUG worker

run: test
	flask run

cloudsql-secret: check-cloudsql-credentials
	kubectl delete --ignore-not-found=true secrets cloudsql-instance-credentials
	kubectl create secret generic cloudsql-instance-credentials --from-file=credentials.json=${PROXY_KEY_FILE_PATH}
	kubectl delete --ignore-not-found=true secrets cloudsql-db-credentials
	kubectl create secret generic cloudsql-db-credentials --from-literal=username=proxyuser --from-literal=password=${SQUASH_DB_PASSWORD}

build: check-tag
	docker build -t $(API):${TAG} .
	docker build -t $(NGINX):${TAG} kubernetes/nginx

push: check-tag
	docker push $(API):${TAG}
	docker push $(NGINX):${TAG}

configmap:
	@echo "Creating config map for nginx configuration..."
	kubectl delete --ignore-not-found=true configmap squash-restful-api-nginx-conf
	kubectl create configmap squash-restful-api-nginx-conf --from-file=$(NGINX_CONFIG)

aws-secret: check-aws-credentials
	@echo "Creating AWS secret"
	kubectl delete --ignore-not-found=true secrets squash-aws-creds
	kubectl create secret generic squash-aws-creds \
        --from-literal=AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
        --from-literal=AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}

deployment: check-tag check-squash-api-credentials configmap
	@echo "Creating deployment..."
	@$(REPLACE) $(DEPLOYMENT_TEMPLATE) $(DEPLOYMENT_CONFIG)
	kubectl delete --ignore-not-found=true deployment squash-restful-api
	kubectl create -f $(DEPLOYMENT_CONFIG)

service:
	@echo "Creating service..."
	kubectl delete --ignore-not-found=true services squash-restful-api
	kubectl create -f $(SERVICE_CONFIG)

check-tag:
	@if test -z ${TAG}; then echo "Error: TAG is undefined."; exit 1; fi

check-cloudsql-credentials: check-squash-db-credentials
	@if test -z ${PROXY_KEY_FILE_PATH}; then echo "Error: PROXY_KEY_FILE_PATH is undefined."; exit 1; fi

check-squash-api-credentials:
	@if test -z ${SQUASH_DEFAULT_USER}; then echo "Error: SQUASH_DEFAULT_USER is undefined."; exit 1; fi
	@if test -z ${SQUASH_DEFAULT_PASSWORD}; then echo "Error: SQUASH_DEFAULT_PASSWORD is undefined."; exit 1; fi

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

check-namespace:
	@if [ -z ${NAMESPACE} ]; \
	then echo "Error: NAMESPACE is undefined."; \
	     exit 1; \
	fi
PATH:=bin/:${PATH}
.PHONY: clean test run mysql-secret build push configmap deployment\
service check-tag

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
	@echo "  run			run tests and run the app in development mode"
	@echo "  cloudsql-credentials  create secrets with cloud sql proxy key and db password."
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

run: test
	python run.py

cloudsql-credentials: check-cloudsql-credentials
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

deployment: check-tag configmap
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

check-cloudsql-credentials:
	@if test -z ${SQUASH_DB_PASSWORD}; then echo "Error: SQUASH_DB_PASSWORD is undefined."; exit 1; fi
	@if test -z ${PROXY_KEY_FILE_PATH}; then echo "Error: PROXY_KEY_FILE_PATH is undefined."; exit 1; fi

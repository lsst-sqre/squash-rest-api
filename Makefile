PATH:=bin/:${PATH}
.PHONY: all clean test run

help:
	@echo "Available commands:"
	@echo "  clean			remove temp files"
	@echo "  test			run all tests and generate test coverage"

clean:
	find ./ -type f -name '*.pyc' -exec rm -f {} \;
	rm -rf .coverage
	rm -rf .cache

test:
	flake8 app tests
	coverage run --source=app test.py

run: test
	python run.py

all: clean


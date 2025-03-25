SERID=$(shell id -u)
GROUPID=$(shell id -g)

help:
	@echo 'Available commands:'
	@echo ''
	@echo 'build ................................ Builds image'
	@echo 'run .................................. Runs the webserver'
	@echo 'test ................................. Runs all tests except integration'
	@echo 'lock ................................. Locks the versions of dependencies.'
	@echo ''

build:
	docker compose build

test:
	./bin/run.sh pytest . --disable-warnings -s

lock:
	./bin/run.sh poetry lock

run:
	docker compose up

shell:
	./bin/run.sh bash

makemigrations:
	./bin/run.sh python manage.py makemigrations

migrate:
	./bin/run.sh python manage.py migrate

create-superuser:
	./bin/run.sh python manage.py createsuperuser

.PHONY: all build test run shell makemigrations migrate
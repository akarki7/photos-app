# Photos APP Backend

Backend for Photos APP

## Requirements

### For development

You need:

* docker
* docker-compose
* uv

### For deployment

You should not deploy this project by hand. Follow the deploy guidelines
in a later section.

## How to use this repository

This project is built using Python, Django, Docker, Terraform
and PostgreSQL or a PostgreSQL related database.

In order for you to built it locally you can execute commands available
in the `Makefile`.

For a quick test drive, you can type in your terminal:

```bash
make build
make migrate
make run
```

Your project will be available at `localhost:8000`.

If this is the first time you creating a new project, you
will **first** need to have a valid `uv.lock` file
in the root of your project.

You can construct one by using uv directly with:

```bash
uv lock
```

## How to install new packages

```bash
uv add <package-name>
uv remove <package-name>
```
```

## Logs
---
* Logs can be found in the file `django.log` 

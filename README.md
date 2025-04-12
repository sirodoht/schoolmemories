# schoolmemories

## Development

This is a standard [Django](https://docs.djangoproject.com/) application with
[uv](https://github.com/astral-sh/uv).

1. Setup environment variables with:

```sh
cp .envrc.example .envrc
source .envrc
```

2. Create database tables with:

```sh
uv run manage.py migrate
```

3. Run development server with:

```sh
uv run manage.py runserver
```

## Format and lint

Run Python formatting with:

```sh
uv run ruff format
```

Run Python linting with:

```sh
uv run ruff check --fix
```

Run Djade Django HTML formatting with:

```sh
uv run djade main/templates/**/*.html
```

## Deploy

Every commit on branch `main` auto-deploys using GitHub Actions. To deploy manually:

```sh
cd ansible/
cp .envrc.example .envrc
uv run ansible-playbook -v playbook.yaml
```

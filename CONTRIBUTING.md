# Contributing guide

## Development

Use `BUILDKIT_PROGRESS=plain` before the docker compose commands to see all the output.

### To upgrade dependencies

```shell
docker build --target upgrade_deps .
docker compose run --rm upgrade_deps
```

### Start local server

```shell
docker build --target dev_app .
docker compose up --menu=false dev_app
docker compose down dev_app
```

### To get the contents of the python3-apt package locally

```shell
docker build --target export_deps --output export_deps .
```

## Run tests and linters



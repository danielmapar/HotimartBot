# 1. Hotimart Bot

## 1.1. Summary

- [1. Hotimart Bot](#1-hotimart-bot)
  - [1.1. Summary](#11-summary)
  - [1.2. Introduction](#12-introduction)
  - [1.3. Requirements](#13-requirements)
  - [1.4. Tests](#14-tests)


## 1.2. Introduction

Hotimart bot scraper for download courses videos.

## 1.3. Requirements

1. Install poetry <https://python-poetry.org/docs/>
2. Configure local virtual environments in poetry (<https://python-poetry.org/docs/configuration/>)

```powershell
poetry config virtualenvs.in-project true
```

3. Install necessary dependencies:

```powershell
cd hotmartbot
poetry install
```

OBS: Execute with "--no-dev" option if you don't want to install the dev packages.

1. Execute the Hotmart bot:

```powershell
poetry run hotmart-bot <domain> <username> <password>
```

## 1.4. Tests

1. All tests:

```powershell
poetry run pytest -v tests
```

2. See test coverage:

```powershell
poetry run pytest --cov
```

## Disclaimer & WARNINGS:

* Use this ONLY for Educational Purposes! By using this code you agree that I'm not responsible for any kind of trouble caused by the code. Make sure web-scraping is legal in your region.

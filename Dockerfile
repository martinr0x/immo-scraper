FROM python:3.12-bookworm

RUN pip install poetry

WORKDIR /app

COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.in-project true
RUN poetry install --only=main --no-root
RUN poetry run playwright install-deps
RUN poetry run playwright install

COPY immo-scraper/* immo-scraper/

ENTRYPOINT poetry run python immo-scraper/telegram_bot.py
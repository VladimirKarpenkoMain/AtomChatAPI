#!/bin/sh

sleep 5

python /backend/app/core/generate_certs.py
python /backend/app/core/generate_db.py

alembic upgrade head

gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000
#!/bin/sh
python /backend/app/core/generate_certs.py
python /backend/app/core/generate_db.py

sleep 5

alembic upgrade head

gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000
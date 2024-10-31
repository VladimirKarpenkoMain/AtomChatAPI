FROM python:3.11-alpine

RUN mkdir /backend

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /backend

WORKDIR /backend
ENV PYTHONPATH=/backend

RUN chmod a+x /backend/docker/app.sh

CMD ["gunicorn", "app.main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind=0.0.0.0:8000"]
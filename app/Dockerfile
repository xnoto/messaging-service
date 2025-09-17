FROM python:3.11-alpine

RUN apk add --no-cache curl ca-certificates

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

ENV POSTGRES_USER=messaging_user
ENV POSTGRES_PASSWORD=messaging_password
ENV POSTGRES_DB=messaging_service
ENV POSTGRES_HOST=db
ENV POSTGRES_PORT=5432

CMD ["python", "app.py"]
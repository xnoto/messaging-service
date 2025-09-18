FROM python:3.11-alpine

RUN apk add --no-cache curl

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./

CMD ["python", "app.py"]

FROM python:3.13-slim

WORKDIR /app

COPY requirement.txt requirement.txt

RUN pip3 install -r requirement.txt

COPY . .

CMD uvicorn main:app --host=0.0.0.0 --reload
FROM python:3.10-alpine

WORKDIR /app 
COPY . /app/setu

RUN pip install -r /app/setu/requirements.txt

CMD ["gunicorn", "-b", "0.0.0.0:5555", "setu:app"]

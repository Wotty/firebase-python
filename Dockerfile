FROM python:3.7



COPY . app/
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PORT 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
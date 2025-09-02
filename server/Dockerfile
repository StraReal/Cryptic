FROM python:latest
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY ./requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app /app

CMD ["python", "signaling_server.py"]
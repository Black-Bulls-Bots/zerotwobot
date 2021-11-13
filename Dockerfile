FROM python:3.9-slim-buster

WORKDIR /bot

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3', "-m", "zerotwobot"]

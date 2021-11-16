FROM jokerhacker/zerotwo-python:latest

RUN  git clone https://github.com/Black-Bulls-Bots/zerotwobot -b main  /root/zerotwo
RUN  mkdir  /root/zerotwo/bin/
WORKDIR /root/zerotwo/

COPY  ./zerotwobot/elevated_users.json* ./zerotwobot/config.py* /root/zerotwo/zerotwobot/
RUN pip3 install -r requirements.txt

CMD ["python3", "-m", "zerotwobot"]

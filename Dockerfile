FROM alpine:edge

LABEL maintainer="jokerhacker.6521@pm.me"
LABEL version="0.1"
LABEL description="This is custom Docker Image for the User Bot"

RUN sed -e 's;^#http\(.*\)/edge/community;http\1/edge/community;g' -i /etc/apk/repositories
RUN echo 'http://dl-cdn.alpinelinux.org/alpine/edge/testing' >> /etc/apk/repositori

RUN apk add --no-cache=true --update \
    git \
    python3-dev \
    python3

RUN python3 -m ensurepip \
    && pip3 install --upgrade pip setuptools \
    && pip3 install wheel \
    && rm -r /usr/lib/python*/ensurepip && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

RUN git clone https://github.com/jokerhacker22/zerotwobot/ /root/zerotwobot
RUN mkdir /root/zerotwobot/bin/
WORKDIR /root/zerotwobot/


#
# Install requirements
#
RUN pip3 install -r requirements.txt
RUN rm /bin/sh && ln -s /bin/bash /bin/sh
CMD ["python3","-m","zerotwobot"]
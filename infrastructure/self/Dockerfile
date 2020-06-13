FROM python:3.7-alpine

MAINTAINER Vitaliy Boyarsky <boyarsky.vitaliy@live.com>

ENV ENDPOINT='http://127.0.0.1:5000'

RUN apk add --no-cache gcc musl-dev linux-headers

WORKDIR /src
COPY .source_code .
RUN pip install -r requirements.txt

EXPOSE 5000
VOLUME /data

ENTRYPOINT python app.py \
    --host 0.0.0.0 \
    --repo /data \
    --endpoint $ENDPOINT

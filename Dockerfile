FROM python:3.12-alpine
ENV CONNECTOR_TYPE=INTERNAL_ENRICHMENT

RUN apk --no-cache add git build-base libmagic libffi-dev ca-certificates \
    curl bash vim nano busybox-extras && \
    update-ca-certificates

COPY src /opt/opencti-connector-favicon-hash

RUN cd /opt/opencti-connector-favicon-hash && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apk del git build-base

COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

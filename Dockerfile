FROM python:3.9-alpine

WORKDIR /src
ADD     . /src
RUN     apk --no-cache add build-base python3-dev && python setup.py install && apk del python3-dev build-base


WORKDIR    /workspace
ENTRYPOINT ["/usr/local/bin/zonefile-migrate"]
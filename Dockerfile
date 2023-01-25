FROM python:3.10-alpine as builder
WORKDIR /usr/src/app
RUN apk add gcc musl-dev make g++ git
ENV SODIUM_INSTALL=system
RUN pip install virtualenv && virtualenv /app # && /app/bin/pip install
RUN pip install poetry --no-cache-dir
COPY . .
RUN poetry build
RUN /app/bin/pip install dist/`ls dist | grep .whl` --no-cache-dir


FROM python:3.10-alpine
RUN apk add bash --no-cache
COPY --from=builder /app /app
COPY ./config/cron.jobs /var/spool/cron/crontabs/root
WORKDIR /config
CMD ["bash",  "-c", "set -m; crond -L /dev/stdout -f & /app/bin/switcharoohelper > /dev/stdout; fg %1"]

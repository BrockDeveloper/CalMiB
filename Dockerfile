FROM python:3.10-alpine

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

ARG port=80
ENV PORT ${port}
EXPOSE ${port}

HEALTHCHECK --interval=5m --timeout=3s \
  CMD curl -f http://localhost:${PORT}/docs || exit 1

CMD uvicorn main:app --proxy-headers --host 0.0.0.0 --port ${PORT}

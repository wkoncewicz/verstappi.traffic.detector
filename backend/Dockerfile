FROM python:3.11-alpine AS builder

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev

RUN python -m ensurepip && \
    pip install --upgrade pip

COPY app/requirements.txt ./
RUN pip install --prefix=/install -r requirements.txt

COPY app/ .

FROM python:3.11-alpine

WORKDIR /app

COPY --from=builder /install /usr/local

COPY --from=builder /app ./

CMD ["python", "app.py"]

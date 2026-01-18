FROM python:3.11-slim AS builder

WORKDIR /app

RUN python -m ensurepip && \
    pip install --upgrade pip

COPY app/requirements.txt ./
RUN pip install --prefix=/install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY app/ .

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        ffmpeg \
        libvlc5 \
        libvlc-dev \
        vlc-bin \
        vlc-plugin-base \
    && rm -rf /var/lib/apt/lists/*

ENV VLC_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/vlc/plugins

COPY --from=builder /install /usr/local

COPY --from=builder /app ./

CMD ["python", "main.py"]
    
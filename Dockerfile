FROM python:3.11-slim

WORKDIR /main

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ curl git cmake pkg-config \
    libjpeg-dev zlib1g-dev libpng-dev libopenblas-dev liblapack-dev \
    libssl-dev libffi-dev libxml2-dev libxslt1-dev libpq-dev \
    rustc cargo \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt


RUN echo "== requirements.txt ==" && cat /app/requirements.txt && \
    python -m pip install --upgrade pip setuptools wheel && \
    pip --version && \
    pip install -vvv --default-timeout=100 -r /app/requirements.txt

COPY . .


EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV ENV=production

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

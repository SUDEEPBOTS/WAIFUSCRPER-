# --------------------------------------------------------------------------
# Copyright (c) 2026 TOXICXD43 / SUDEEPBOTS. All Rights Reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
# --------------------------------------------------------------------------

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies for cryptography, build tools & git
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application files
COPY . .

# Start the bot worker
CMD ["python3", "-m", "WAIFUSCRPER"]

FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install pre-compiled dlib (no compilation)
RUN pip install --no-cache-dir dlib-bin==19.24.0

# Install face-recognition without its dependencies (to avoid pulling dlib source)
RUN pip install --no-cache-dir --no-deps face-recognition==1.3.0

# Copy requirements and install remaining packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole project
COPY . .

# Ensure STATIC_ROOT is set (fix for missing setting)
RUN if ! grep -q "STATIC_ROOT" config/settings.py; then \
        echo "STATIC_ROOT = BASE_DIR / 'staticfiles'" >> config/settings.py; \
    fi

# Collect static files (now STATIC_ROOT is guaranteed)
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
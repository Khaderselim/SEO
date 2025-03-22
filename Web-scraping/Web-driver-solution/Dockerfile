FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    wget \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libasound2 \
    libxdamage1 \
    libxshmfence1 \
    libgtk-3-0 \
    libx11-xcb1 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libxss1 \
    libgconf-2-4 \
    dbus-x11 \
    supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Setup dbus
RUN mkdir -p /var/run/dbus
RUN dbus-uuidgen > /var/lib/dbus/machine-id

# Set working directory
WORKDIR /app

# Copy project files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright with specific browser
RUN python -m playwright install --with-deps chromium
RUN playwright install-deps

COPY . .

# Copy Supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose API port
EXPOSE ${PORT:-5000}

# Start Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
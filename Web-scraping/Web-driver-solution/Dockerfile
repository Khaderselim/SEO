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
    dbus \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up dbus
RUN mkdir -p /var/run/dbus

# Copy and install requirements
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Copy application code
COPY . .

# Create a script to start Xvfb and run the application
RUN echo '#!/bin/bash\nXvfb :99 -screen 0 1024x768x16 &\nexport DISPLAY=:99\npython main.py' > start.sh
RUN chmod +x start.sh

# Run the script
CMD ["./start.sh"]
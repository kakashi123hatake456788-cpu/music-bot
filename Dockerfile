FROM python:3.10-slim

# Install FFmpeg and git required for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy requirement definitions first for cached layer installation
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all repository code
COPY . .

# Expose Render default port
EXPOSE 10000

# Execute the application entry point
CMD ["python", "main.py"]

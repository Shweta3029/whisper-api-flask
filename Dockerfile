FROM python:3.10-slim

WORKDIR /app

# Install ffmpeg and git
RUN apt-get update && apt-get install -y ffmpeg git

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/openai/whisper.git

# Copy the rest of the app
COPY . .

# ✅ Google Cloud Run listens on port 8080
EXPOSE 8080

# ✅ Make sure to bind to port 8080
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8080"]

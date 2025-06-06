FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg git

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/openai/whisper.git

COPY . .

EXPOSE 8080  # ✅ Must match Cloud Run's expected port

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8080"]  # ✅ Matches EXPOSE and Cloud Run settings

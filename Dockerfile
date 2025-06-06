FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg git

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/openai/whisper.git

COPY . .

EXPOSE 5000

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000"]

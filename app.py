from flask import Flask, request, jsonify
import os
import whisper
import tempfile
from pytube import YouTube
import subprocess
import uuid
from google.cloud import storage  # Firebase Storage SDK
import firebase_admin
from firebase_admin import credentials, storage
import json
import os

# Read credentials from environment variable
firebase_creds = json.loads(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON'))

# Initialize Firebase with credentials loaded from env
cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'aigle-dr7eb.appspot.com'
})

bucket = storage.bucket()

app = Flask(__name__)
model = whisper.load_model("base")  # or 'small', 'medium', etc. depending on server size

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Initialize Firebase Storage client
storage_client = storage.Client()
bucket_name = "aigle-dr7eb.firebasestorage.app"  # Your Firebase Storage bucket name
bucket = storage_client.bucket(bucket_name)

# Utility: Download YouTube video
def download_youtube_video(link):
    yt = YouTube(link)
    stream = yt.streams.filter(only_audio=False, file_extension='mp4').first()
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    stream.download(output_path=UPLOAD_FOLDER, filename=filename)
    return filepath

# Utility: Transcribe + get timestamps
def transcribe_with_whisper(filepath):
    result = model.transcribe(filepath, verbose=False, word_timestamps=True)
    return result

# Utility: Cut a short from start to end (in sec)
def cut_video(input_path, start, end, output_path):
    command = [
        "ffmpeg", "-i", input_path,
        "-ss", str(start), "-to", str(end),
        "-c:v", "copy", "-c:a", "copy",
        output_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

# Utility: Add hardcoded subtitles (basic)
def add_subtitles(video_path, transcript, output_path):
    subtitle_file = f"{video_path}.srt"
    with open(subtitle_file, 'w') as f:
        for i, segment in enumerate(transcript['segments']):
            f.write(f"{i+1}\n")
            f.write(f"{segment['start']:.2f} --> {segment['end']:.2f}\n")
            f.write(f"{segment['text'].strip()}\n\n")

    command = [
        "ffmpeg", "-i", video_path, "-vf",
        f"subtitles={subtitle_file}", output_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

# Upload to Firebase Storage and make public
def upload_file_to_firebase(local_file_path, destination_blob_name):
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file_path)
    blob.make_public()
    return blob.public_url

@app.route("/generate-shorts", methods=["POST"])
def generate_shorts():
    yt_link = request.form.get("youtube_link")
    with_subs = request.form.get("subtitles") == 'true'

    try:
        if yt_link:
            video_path = download_youtube_video(yt_link)
        elif 'file' in request.files:
            f = request.files['file']
            filename = f"{uuid.uuid4()}.mp4"
            video_path = os.path.join(UPLOAD_FOLDER, filename)
            f.save(video_path)
        else:
            return jsonify({"error": "No video file or YouTube link provided"}), 400

        # Transcribe video
        result = transcribe_with_whisper(video_path)

        # Cut first 60 seconds short
        start = 0
        end = 60
        short_path = os.path.join(PROCESSED_FOLDER, f"short_{uuid.uuid4()}.mp4")
        cut_video(video_path, start, end, short_path)

        # Add subtitles if requested
        if with_subs:
            final_output = os.path.join(PROCESSED_FOLDER, f"subtitled_{uuid.uuid4()}.mp4")
            add_subtitles(short_path, result, final_output)
        else:
            final_output = short_path

        # Upload final video to Firebase Storage
        file_name_in_bucket = f"shorts/{os.path.basename(final_output)}"
        public_url = upload_file_to_firebase(final_output, file_name_in_bucket)

        return jsonify({"message": "Short created", "file_url": public_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

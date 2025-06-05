# app.py

from flask import Flask, request, jsonify
import os
import whisper
import tempfile
from pytube import YouTube
import subprocess
import uuid

app = Flask(__name__)
model = whisper.load_model("base")  # or 'small', 'medium', etc. depending on server size

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

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

@app.route("/generate-shorts", methods=["POST"])
def generate_shorts():
    video_file = None
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

        # Transcribe it
        result = transcribe_with_whisper(video_path)

        # Take first 60 seconds segment for short (or logic can be extended)
        start = 0
        end = 60
        short_path = os.path.join(PROCESSED_FOLDER, f"short_{uuid.uuid4()}.mp4")
        cut_video(video_path, start, end, short_path)

        # Add subtitles if asked
        if with_subs:
            final_output = os.path.join(PROCESSED_FOLDER, f"subtitled_{uuid.uuid4()}.mp4")
            add_subtitles(short_path, result, final_output)
        else:
            final_output = short_path

        return jsonify({"message": "Short created", "file_path": final_output})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

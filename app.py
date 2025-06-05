from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import tempfile

from werkzeug.utils import secure_filename

import whisper

app = Flask(__name__)
CORS(app)

model = whisper.load_model("base")

def trim_video(input_path, output_path, duration):
    command = [
        "ffmpeg",
        "-ss", "0",
        "-i", input_path,
        "-t", str(duration),
        "-c", "copy",
        output_path
    ]
    subprocess.run(command, check=True)

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file.save(tmp.name)
        result = model.transcribe(tmp.name)
    os.unlink(tmp.name)
    return jsonify(result)

@app.route('/generate-short', methods=['POST'])
def generate_short():
    video_file = request.files.get('video')
    duration = int(request.form.get('duration', 30))  # default 30 seconds

    if video_file is None:
        return jsonify({"error": "No video file uploaded"}), 400

    filename = secure_filename(video_file.filename)
    input_path = os.path.join(tempfile.gettempdir(), filename)
    output_path = os.path.join(tempfile.gettempdir(), f"short_{filename}")

    video_file.save(input_path)

    try:
        trim_video(input_path, output_path, duration)
    except Exception as e:
        return jsonify({"error": f"FFmpeg error: {str(e)}"}), 500

    # Return the trimmed video file to download
    return send_file(output_path, as_attachment=True, attachment_filename=f"short_{filename}")

if __name__ == "__main__":
    app.run(debug=True)

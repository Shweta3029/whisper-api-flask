from flask import Flask, abort, request
from flask_cors import CORS
from tempfile import NamedTemporaryFile
import whisper
import torch

# Check if NVIDIA GPU is available
torch.cuda.is_available()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load the Whisper model:
model = whisper.load_model("base", device=DEVICE)

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello():
    return "Whisper Hello World!"


@app.route('/whisper', methods=['POST'])
def handler():
    if not request.files:
        # If the user didn't submit any files, return a 400 (Bad Request) error.
        abort(400)
        from flask import request, jsonify

@app.route('/generate-short', methods=['POST'])
def generate_short():
    video_file = request.files.get('video')
    duration = int(request.form.get('duration', 30))  # default 30 seconds

    input_path = 'input.mp4'
    output_path = 'output_short.mp4'

    if video_file is None:
        return jsonify({"error": "No video file uploaded"}), 400

    video_file.save(input_path)

    try:
        trim_video(input_path, output_path, duration)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Video trimmed", "output_file": output_path})


    # For each file, let's store the results in a list of dictionaries.
    results = []

    # Loop over every file that the user submitted.
    for filename, handle in request.files.items():
        # Create a temporary file.
        # The location of the temporary file is available in `temp.name`.
        temp = NamedTemporaryFile()
        # Write the user's uploaded file to the temporary file.
        # The file will get deleted when it drops out of scope.
        handle.save(temp)
        # Let's get the transcript of the temporary file.
        result = model.transcribe(temp.name)
        # Now we can store the result object for this file.
        results.append({
            'filename': filename,
            'transcript': result['text'],
        })

    # This will be automatically converted to JSON.
    return {'results': results}
    import subprocess

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

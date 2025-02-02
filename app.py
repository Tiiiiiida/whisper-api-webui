import os
import time
import tempfile
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, stream_with_context
from flask_cors import CORS
from functools import wraps
from pydub import AudioSegment
from werkzeug.security import check_password_hash

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")
openai_api_key = os.environ.get("OPENAI_API_KEY", "")
api_base_url = os.environ.get("API_BASE_URL", "")
ACCESS_PASSWORD_HASH = os.environ.get("ACCESS_PASSWORD_HASH")


def get_audio_info(input_file):
    # Returns duration (s), sample rate, channels, sample width, and computed uncompressed bit rate
    audio = AudioSegment.from_file(input_file)
    duration = len(audio) / 1000  # seconds
    sample_rate = audio.frame_rate
    channels = audio.channels
    sample_width = audio.sample_width  # in bytes
    bit_rate = sample_rate * channels * sample_width * 8  # bits per second
    return duration, sample_rate, channels, sample_width, bit_rate


def compress_audio(input_file):
    try:
        # Get original audio properties
        audio = AudioSegment.from_file(input_file)
        orig_duration, orig_sr, orig_channels, orig_sample_width, orig_bit_rate = get_audio_info(input_file)

        # Determine target parameters
        target_sample_rate = 16000 if orig_sr >= 16000 else orig_sr
        target_channels = 1  # Force mono
        target_bitrate_val = 320000 if orig_bit_rate > 320000 else orig_bit_rate
        target_bitrate_str = f"{target_bitrate_val // 1000}k"

        # Create temporary file for output
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".m4a")

        # Export using ffmpeg
        audio.export(
            temp_file.name,
            format="mp4",
            codec="aac",
            parameters=["-ac", str(target_channels), "-ar", str(target_sample_rate), "-b:a", target_bitrate_str]
        )

        return temp_file.name

    except Exception as e:
        # Log error for debugging
        print(f"ERROR: Audio compression failed: {e}")
        raise Exception(f"Audio compression failed. Details: {e}")


def split_audio_m4a(input_file, max_size=25 * 1024 * 1024):
    # Split the given m4a file into segments so that each part is below max_size
    audio = AudioSegment.from_file(input_file)
    file_size = os.path.getsize(input_file)
    num_splits = (file_size // max_size) + 1
    segment_length = len(audio) // num_splits
    split_files = []
    for i in range(num_splits):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".m4a")
        start_time = i * segment_length
        end_time = (i + 1) * segment_length if i < num_splits - 1 else len(audio)
        segment = audio[start_time:end_time]
        # Use m4a export with AAC codec; reusing similar parameters is optional since the compressed file already meets the criteria
        segment.export(temp_file.name, format="mp4", codec="aac")
        split_files.append(temp_file.name)
    return split_files


def transcribe_audio(input_file, model):
    headers = {"Authorization": f"Bearer {openai_api_key}"}
    files = {"file": open(input_file, "rb")}
    data = {"model": model, "response_format": "text"}
    endpoint = f"{api_base_url}/v1/audio/transcriptions"
    start_time = time.time()
    response = requests.post(endpoint, headers=headers, files=files, data=data)
    end_time = time.time()
    if response.status_code == 200:
        return response.text, end_time - start_time
    raise Exception(f"API request failed: {response.status_code} - {response.text}")


def get_models():
    headers = {"Authorization": f"Bearer {openai_api_key}"}
    response = requests.get(f"{api_base_url}/v1/models", headers=headers)
    if response.status_code == 200:
        models = [m["id"] for m in response.json()["data"] if "whisper" in m["id"]]
        if not models:
            models = [m["id"] for m in response.json()["data"]]
        return models
    return []


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated"):
            flash("Authentication required", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@login_required
def index():
    model_options = get_models()
    return render_template("index.html", models=model_options)


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    def generate():
        yield "INFO: File upload received.\n"
        uploaded_file = request.files.get("audio_file")
        if not uploaded_file:
            yield "ERROR: No file uploaded.\n"
            return
        # Save uploaded file
        suffix = os.path.splitext(uploaded_file.filename)[1]
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        uploaded_file.save(temp_input.name)
        file_size_mb = os.path.getsize(temp_input.name) / (1024 * 1024)
        yield f"INFO: File saved: {uploaded_file.filename} (size: {file_size_mb:.2f} MB).\n"

        try:
            duration, sample_rate, channels, sample_width, bit_rate = get_audio_info(temp_input.name)
            yield f"INFO: Audio duration: {duration:.2f}s, Sample rate: {sample_rate}Hz, Channels: {channels}\n"

            # Check file size and decide processing
            if os.path.getsize(temp_input.name) < 25 * 1024 * 1024:
                yield "INFO: File size within limits (<25MB). Skipping compression and splitting.\n"
                file_list = [temp_input.name]
            else:
                yield "INFO: File size exceeds 25MB. Attempting compression...\n"
                compressed_file = compress_audio(temp_input.name)
                comp_size_mb = os.path.getsize(compressed_file) / (1024 * 1024)
                yield f"INFO: Compressed file size: {comp_size_mb:.2f} MB.\n"
                if os.path.getsize(compressed_file) < 25 * 1024 * 1024:
                    yield "INFO: Compressed file is within limits.\n"
                    file_list = [compressed_file]
                else:
                    yield "INFO: Compressed file still exceeds 25MB. Proceeding to split the file...\n"
                    split_files = split_audio_m4a(compressed_file)
                    yield f"INFO: Split into {len(split_files)} parts.\n"
                    file_list = split_files

            # Start transcription
            model = request.form.get("model")
            full_transcript = ""
            total_time = 0
            yield f"INFO: Starting transcription using model: {model}\n"
            for idx, file in enumerate(file_list, start=1):
                if len(file_list) > 1:
                    yield f"INFO: Processing part {idx}/{len(file_list)}...\n"
                try:
                    transcript, t_time = transcribe_audio(file, model)
                    full_transcript += transcript + "\n"
                    total_time += t_time
                    yield f"INFO: Part {idx} transcribed in {t_time:.2f} seconds.\n"
                except Exception as e:
                    yield f"ERROR: Failed transcribing part {idx}: {str(e)}\n"
                finally:
                    if os.path.exists(file):
                        os.unlink(file)

            # Clean up the original uploaded file if it still exists
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            yield f"INFO: All processing completed in {total_time:.2f} seconds.\n"
            yield "INFO: Temporary files cleaned up.\n"
            # Special marker for frontend to detect the start of results
            yield "RESULT_BEGIN\n"
            yield full_transcript
        except Exception as e:
            yield f"ERROR: Processing failed: {str(e)}\n"
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
                yield "INFO: Cleaned up temporary files.\n"

    return Response(stream_with_context(generate()), mimetype="text/plain")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if check_password_hash(ACCESS_PASSWORD_HASH, request.form.get("password")):
            session["authenticated"] = True
            return redirect(url_for("index"))
        flash("Invalid password", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
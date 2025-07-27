from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import os
import whisper
from transformers import pipeline
import time
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Model Loading (can be done once at startup if desired) ---
# To save time on each request, you could load models here.
# However, for memory efficiency on systems with less RAM, loading on-demand is safer.

def transcribe_audio(audio_path):
    """Transcribes the audio file using Whisper."""
    print("Loading Whisper model 'base'...")
    try:
        # Force model to run on CPU to avoid Metal/GPU memory errors on macOS
        model = whisper.load_model("base", device="cpu")
        print("Transcribing audio...")
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

def summarize_text(text):
    """Summarizes the text using a Hugging Face model."""
    if not text or not text.strip():
        return None
    
    print("Loading summarization model 'facebook/bart-large-cnn'...")
    try:
        # Using a robust model for summarization, forced to CPU
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device="cpu")
        
        transcript_word_count = len(text.split())
        # Set max length to half the transcript length
        max_len = transcript_word_count // 2
        # Set min length to 80% of the max length to encourage longer summaries
        min_len = (max_len * 8) // 10

        # Ensure a reasonable minimum length for very short transcripts
        if max_len < 30:
            max_len = 30
        if min_len < 15:
            min_len = 15


        print(f"Summarizing text (Min: {min_len}, Max: {max_len})...")
        summary_result = summarizer(text, max_length=max_len, min_length=min_len, do_sample=False)
        return summary_result[0]['summary_text']
    except Exception as e:
        print(f"Error during summarization: {e}")
        return None

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """Handles file upload and returns the filename."""
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        # Use a secure filename and a unique prefix
        filename = f"audio_{int(time.time())}.mp3"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'filename': filename})
    return jsonify({'error': 'File upload failed'}), 500

@app.route('/process/<filename>')
def process(filename):
    """Processes the audio file and streams progress."""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return Response("File not found.", status=404)

    def generate():
        # 1. Transcription
        yield 'data: {"status": "Transcribing audio...", "percent": 25}\n\n'
        transcript = transcribe_audio(filepath)
        if not transcript:
            error_data = json.dumps({"error": "Failed to transcribe audio."})
            yield f'data: {error_data}\n\n'
            return

        yield f'data: {json.dumps({"status": "Transcription complete. Summarizing...", "percent": 60})}\n\n'
        
        # 2. Summarization
        summary = summarize_text(transcript)
        if not summary:
            error_data = json.dumps({"error": "Failed to generate summary."})
            yield f'data: {error_data}\n\n'
            return

        # 3. Done
        final_data = json.dumps({
            "status": "Done",
            "percent": 100,
            "transcript": transcript,
            "summary": summary
        })
        yield f'data: {final_data}\n\n'
        
        # Clean up the uploaded file
        try:
            os.remove(filepath)
            print(f"Removed uploaded file: {filepath}")
        except OSError as e:
            print(f"Error removing file {filepath}: {e}")

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=9099)

import torch
from transformers import pipeline
import whisper
import sentencepiece # Required by some Hugging Face models

print("All necessary libraries imported successfully!")

try:
    # Test Whisper loading (will download a tiny model if not present)
    model = whisper.load_model("tiny.en")
    print("Whisper 'tiny.en' model loaded successfully.")
except Exception as e:
    print(f"Error loading Whisper model: {e}")

try:
    # Test Hugging Face pipeline loading
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    print("Hugging Face summarization pipeline loaded successfully.")
except Exception as e:
    print(f"Error loading Hugging Face pipeline: {e}")

print("\nInstallation seems good! You can now proceed with your main script.")
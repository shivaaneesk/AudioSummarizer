import whisper
import os
from transformers import pipeline

AUDIO_FILE_PATH = "audio.mp3"
WHISPER_MODEL_SIZE = "base"

def transcribe_audio(audio_path, model_size="base"):
    print(f"Loading Whisper model '{model_size}' (this may take a moment, especially first time download)...")
    try:
        model = whisper.load_model(model_size, device="cpu")
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        print("Please ensure you have enough RAM and a stable internet connection for the first download.")
        print("You might also try a smaller model size like 'tiny' or 'base'.")
        return None

    print(f"Transcribing audio file: '{audio_path}'...")
    try:
        result = model.transcribe(audio_path)
        transcript = result["text"]
        print("\n--- Transcription Complete ---")
        print(transcript) 
        return transcript
    except FileNotFoundError:
        print(f"Error: Audio file not found at '{audio_path}'")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during transcription: {e}")
        return None

def summarize_text(text, min_len, max_len):
    if not text or not text.strip():
        print("No valid text to summarize.")
        return None

    if max_len < min_len:
        print(f"Warning: Calculated max_length ({max_len}) is less than min_length ({min_len}). Adjusting max_length.")
        max_len = min_len + 20 

    print("\nLoading summarization model (this may take a moment, especially first time download)...")
    try:

        summarizer = pipeline("text2text-generation", model="t5-base", device="cpu")
        print(f"Summarizing text (Min Length: {min_len}, Max Length: {max_len})...")

        summary_result = summarizer("summarize: " + text, max_length=max_len, min_length=min_len, do_sample=True, top_k=50, top_p=0.95)
        summary = summary_result[0]['generated_text']
        print("\n--- Summary Complete ---")
        return summary
    except Exception as e:
        print(f"Error during summarization: {e}")
        print("Ensure you have a stable internet connection for the first model download.")
        return None

if __name__ == "__main__":
    if not os.path.exists(AUDIO_FILE_PATH):
        print(f"Error: The audio file '{AUDIO_FILE_PATH}' does not exist in the current directory.")
        print("Please make sure your audio file is in the same folder as 'audio.py' (or provide its full path).")
    else:
        transcribed_text = transcribe_audio(AUDIO_FILE_PATH, WHISPER_MODEL_SIZE)

        if transcribed_text:
            transcript_word_count = len(transcribed_text.split())
            summary_max_len = max(20, transcript_word_count // 2) 
            summary_min_len = max(10, summary_max_len // 4)      

            print("\n--- Debugging Transcript Content ---")
            print(f"Length of raw transcript: {len(transcribed_text)} characters")
            print(f"First 200 characters of transcript: {transcribed_text[:200]}")
            print(f"Is transcript just whitespace? {transcribed_text.strip() == ''}")
            print(f"Calculated SUMMARY_MIN_LENGTH: {summary_min_len}")
            print(f"Calculated SUMMARY_MAX_LENGTH: {summary_max_len}")
            print("------------------------------------")

            final_summary = summarize_text(transcribed_text, summary_min_len, summary_max_len)

            if final_summary:
                print("\n" + "="*50)
                print("             FINAL AUDIO SUMMARY             ")
                print("="*50)
                print(final_summary)
                print("="*50)

                base_filename = os.path.splitext(AUDIO_FILE_PATH)[0]
                output_filename = f"{base_filename}_summary.txt"
                try:
                    with open(output_filename, "w", encoding="utf-8") as f:
                        f.write("--- Original Transcript ---\n")
                        f.write(transcribed_text)
                        f.write("\n\n--- Summarized Text ---\n")
                        f.write(final_summary)
                    print(f"\nSummary and full transcript saved to '{output_filename}'")
                except Exception as e:
                    print(f"Error saving output to file: {e}")
            else:
                print("Could not generate summary (summarization failed or no text to summarize).")
        else:
            print("Could not generate summary due to transcription failure.")

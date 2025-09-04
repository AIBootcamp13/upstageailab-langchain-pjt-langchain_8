# tests/test_audio.py
import sys
from pathlib import Path

# Add src to the Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.audio_processor import transcribe_audio

def run_test():
    """Tests the audio processor with a sample audio file."""
    print("--- Running Audio Processor Test ---")
    
    # NOTE: You must provide this sample audio file
    sample_audio_path = Path(__file__).parent / "test_audio.mp3"
    if not sample_audio_path.exists():
        print(f"ERROR: Test audio not found at {sample_audio_path}")
        return

    # Use a lightweight model for testing
    test_model = "openai/whisper-tiny"
    
    print(f"Model: {test_model}")
    print(f"Audio File: {sample_audio_path.name}")
    
    transcript = transcribe_audio(sample_audio_path, test_model)
    
    print("\n--- Generated Transcript ---")
    print(transcript)
    print("----------------------------\n")

if __name__ == "__main__":
    run_test()
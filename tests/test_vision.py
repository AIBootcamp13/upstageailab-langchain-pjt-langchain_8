# tests/test_vision.py
import sys
from pathlib import Path
import torch
from PIL import Image

# Add src to the Python path to allow direct imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.vision_processor import describe_image

def run_test():
    """Tests the vision processor with a sample image."""
    print("--- Running Vision Processor Test ---")
    
    # This script looks for 'test_image.png' in the same 'tests/' directory.
    # It does NOT take command-line arguments.
    sample_image_path = Path(__file__).parent / "test_image.png"
    if not sample_image_path.exists():
        print(f"ERROR: Test image not found at {sample_image_path}")
        print("Please make sure 'test_image.png' is inside the 'tests/' folder.")
        return

    # Use a lightweight model for testing
    test_model = "llava-hf/llava-1.5-7b-hf" 
    
    print(f"Model: {test_model}")
    print(f"Image: {sample_image_path.name}")
    
    description = describe_image(sample_image_path, test_model)
    
    print("\n--- Generated Description ---")
    print(description)
    print("-----------------------------\n")

# This is the critical part that executes the test function.
# If this block is missing, the script will do nothing.
if __name__ == "__main__":
    run_test()
# scripts/test_parser.py
from pathlib import Path
from src.document_preprocessor import DocumentPreprocessor
from src.config import ROOT_DIR

def test_pdf_parsing():
    """
    Tests the configured PDF parser by loading a PDF and printing the
    content of the first and last pages.
    """
    # --- Configuration ---
    # 1. Place a test PDF in your 'data' directory.
    # 2. Change 'your_test_file.pdf' to the actual filename.
    pdf_filename = "Analysis and Assessment of Gateway Process_by_CIA.pdf"
    # -------------------

    try:
        test_pdf_path = ROOT_DIR / "data" / "source_pdfs" / pdf_filename
        if not test_pdf_path.exists():
            print(f"Error: Test file not found at {test_pdf_path}")
            print("Please place a PDF in the 'data' directory and update the filename in this script.")
            return
    except Exception as e:
        print(f"Error setting up path: {e}")
        return

    print("--- Testing PDF Parser ---")
    print(f"Loading file: {test_pdf_path}")

    try:
        # Initialize the preprocessor, which automatically selects the parser from config.yaml
        preprocessor = DocumentPreprocessor(test_pdf_path)
        print(f"Using parser: '{preprocessor.parser_type}'")

        # Load the document into pages before it gets chunked
        pages = preprocessor.loader.load()
        print(f"Successfully loaded {len(pages)} pages.")

        # Check and print the content of the first and last pages
        if pages:
            print("\n--- First Page Content ---")
            print(pages[0].page_content)
            print("--------------------------\n")

            # --- ADDED: Check for the second-to-last page ---
            if len(pages) > 2: # Ensure there are at least 3 pages
                print("--- Second-to-Last Page Content ----")
                print(pages[-2].page_content) # Use -2 to access the second-to-last item
                print("-------------------------------------\n")
            if len(pages) > 1:
                print("--- Last Page Content ----")
                print(pages[-1].page_content)
                print("--------------------------\n")
        else:
            print("No content was extracted from the PDF.")

    except Exception as e:
        print(f"\nAn error occurred during parsing: {e}")

if __name__ == "__main__":
    test_pdf_parsing()
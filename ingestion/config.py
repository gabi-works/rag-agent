from pathlib import Path


GUIDELINE_PATH = "../resources/original/guideline.pdf"
API_SPEC_PATH = "../resources/original/api_specification.pdf"

BASE_DIR = Path.cwd().parent
RESOURCES_DIR = BASE_DIR / "resources"
ORIGINAL_DIR = RESOURCES_DIR / "original"
PROCESSED_DIR = RESOURCES_DIR / "processed"

def get_file_paths(doc_type):
    original_pdf = ORIGINAL_DIR / f"{doc_type}.pdf"
    processed_doc_dir = PROCESSED_DIR / doc_type
    return {
        "original_pdf": original_pdf,
        "processed_dir": processed_doc_dir,
        "splitted_pdfs": processed_doc_dir / "splitted_pdfs",
        "analyze_request_info": processed_doc_dir / "analyze_request_info.json",
        "analyzed_jsons": processed_doc_dir / "analyzed_jsons"
    }

GUIDELINE_PATHS = get_file_paths("guideline")
API_SPEC_PATHS = get_file_paths("api_specification")
import os
import json
import pymupdf
from pathlib import Path

from ingestion.states import FileState
from ingestion.nodes.base import BaseNode


class InitPDFNode(BaseNode):
    def __init__(self, file_paths, language="kr", **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.file_paths = file_paths
        self.language = language

    def execute(self, state: FileState) -> FileState:
        file_paths = self.file_paths
        original_pdf_path = file_paths["original_pdf"]
        file_basename = Path(original_pdf_path).stem
        file_type = Path(original_pdf_path).suffix[1:]

        result = FileState(
            file_paths=file_paths,
            file_basename=file_basename,
            file_type=file_type,
            language=self.language
        )
        
        self.log("InitPDFNode execution completed", 
                 file_basename=file_basename, 
                 file_type=file_type)
        return result


class SplitPDFNode(BaseNode):
    def __init__(self, batch_size=1, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.batch_size = batch_size

    def execute(self, state: FileState) -> FileState:
        file_paths = state["file_paths"]
        original_pdf_path = file_paths["original_pdf"]
        splitted_file_base_path = file_paths["splitted_pdfs"]
        analyze_request_info_path = file_paths["analyze_request_info"]
        split_size = self.batch_size

        base_file = pymupdf.open(original_pdf_path)
        num_total_page = base_file.page_count

        splitted_file_paths = []

        for start_page in range(0, num_total_page, split_size):
            end_page = min(start_page + split_size, num_total_page) - 1
            result_file_name = f"{state['file_basename']}_{start_page:03d}_{end_page:03d}.pdf"
            with pymupdf.open() as result_file:
                result_file.insert_pdf(base_file, from_page=start_page, to_page=end_page)
                result_file_path = os.path.join(splitted_file_base_path, result_file_name)
                result_file.save(result_file_path)
                splitted_file_paths.append(result_file_path)

        analyze_request_info = {path: {"request_id": None, "analyzed_json_file_path": None} 
                                for path in splitted_file_paths}

        if not os.path.exists(analyze_request_info_path):
            analyze_request_dict = {
                path: {
                    "splitted_file_path": path,
                    "request_id": None,
                    "analyzed_json_file_path": None
                } for path in splitted_file_paths
            }

            with open(analyze_request_info_path, 'w', encoding='utf-8') as json_file:
                json.dump(analyze_request_dict, json_file, ensure_ascii=False, indent=2)
            
            self.log(f"Created new analyze_request_info file: {analyze_request_info_path}")
        else:
            self.log(f"analyze_request_info file already exists: {analyze_request_info_path}")

        result = FileState(
            split_size=split_size,
            num_total_page=num_total_page,
            splitted_file_paths=splitted_file_paths,
            analyze_request_info=analyze_request_info
        )
        
        self.log("SplitPDFNode execution completed", 
                 num_total_page=num_total_page, 
                 num_split_files=len(splitted_file_paths),
        )
        return result

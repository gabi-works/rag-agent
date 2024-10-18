from typing import TypedDict


class FileState(TypedDict):
    file_path: str
    file_basename: str
    file_type: str
    num_total_page: int
    split_size: int
    splitted_file_paths: list[str]
    analyzed_file_paths: dict[int, str]
    page_metadata: dict[int, dict]
    page_elements: dict[int, dict[str, list[dict]]]
    page_summary: dict[int, str]
    image_paths: dict[int, str]
    image_summaries: dict[int, str]
    table_paths: dict[int, str]
    table_summaries: dict[int, str]
    table_markdowns: dict[int, str]
    table_summary_batches: list[dict]
    texts: list[str]
    text_summaries: dict[int, str]
    language: str
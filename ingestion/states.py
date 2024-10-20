from typing import TypedDict


class FileState(TypedDict):
    file_paths: dict[str, str]
    file_basename: str
    file_type: str
    num_total_page: int
    split_size: int
    splitted_file_paths: list[str]
    analysis_request_info: list[dict]
    page_metadata: dict[int, dict]
    page_elements: dict[int, dict[str, list[dict]]]
    page_summaries: dict[int, str]
    image_paths: dict[int, str]
    image_summaries: dict[int, str]
    table_paths: dict[int, str]
    table_summaries: dict[int, str]
    table_markdowns: dict[int, str]
    table_summary_batches: list[dict]
    texts: list[str]
    text_summaries: dict[int, str]
    language: str
import re
import json

from ingestion.states import FileState
from ingestion.nodes.base import BaseNode
from ingestion.utils.image_processor import ImageCropper
from ingestion.chains.summary import table_markdown_extractor


class ElementsNode(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__

    def extract_page_num(self, file_basename):
        name_pattern =  r'.*_(\d{3})_(\d{3})\.json$'
        match = re.match(name_pattern, file_basename)

        if match:
            start_page, end_page = match.groups()
            return int(start_page), int(end_page)
        else:
            self.log(f"Invalid file basename: {file_basename}")
            return None, None

    def execute(self, state: FileState) -> FileState:
        json_file_paths = sorted(
            info["analyzed_json_file_path"]
            for info in state["analysis_request_info"].values()
            if info["analyzed_json_file_path"] is not None
        )
        page_metadata = dict()
        page_elements = dict()
        element_id = 0

        for json_file_path in json_file_paths:
            with open(json_file_path, "r") as f:
                json_data = json.load(f)

            start_page_num, end_page_num = self.extract_page_num(json_file_path)

            for element in json_data["metadata"]["pages"]:
                original_page_num = int(element["page"])
                relative_page_num = start_page_num + original_page_num - 1

                metadata = {
                    "size" : [
                        int(element["width"]),
                        int(element["height"]) 
                    ],
                }
                page_metadata[relative_page_num] = metadata

            for element in json_data["elements"]:
                original_page_num = int(element["page"])
                relative_page_num = start_page_num + original_page_num - 1

                if relative_page_num not in page_elements:
                    page_elements[relative_page_num] = []

                element["id"] = element_id
                element_id += 1

                element["page"] = relative_page_num
                page_elements[relative_page_num].append(element)
        
        parsed_page_elements = self.extract_tag_elements_per_page(page_elements)
        
        return FileState(
            page_metadata=page_metadata,
            page_elements=parsed_page_elements
        )
    
    def extract_tag_elements_per_page(self, page_elements):
        parsed_page_elements = dict()

        for key, page_elements in page_elements.items():

            figure_elements = []
            table_elements = []
            text_elements = []

            for element in page_elements:
                if element["category"] == "figure":
                    figure_elements.append(element)
                elif element["category"] == "table":
                    table_elements.append(element)
                else:
                    text_elements.append(element)

            parsed_page_elements[key] = {
                "figure_elements": figure_elements,
                "table_elements": table_elements,
                "text_elements": text_elements,
                "elements": page_elements
            }

        return parsed_page_elements


class ImageCropperNode(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__

    def execute(self, state: FileState) -> FileState:
        pdf_file = state["file_paths"]["original_pdf"]
        page_numbers = list(state["page_metadata"].keys())

        output_dir = state["file_paths"]["processed_dir"] / "figures"

        cropped_images = dict()
        for page_num in page_numbers:
            figure_elements = state["page_elements"].get(page_num, {}).get("figure_elements", [])
            for element in figure_elements:
                if element["category"] == "figure":
                    output_file = output_dir / f"{element['id']}.png"
                    cropped_images[element["id"]] = output_file
                    ImageCropper.process_pdf_page(
                        pdf_file=pdf_file,
                        page_num=page_num,
                        coordinates=element["bounding_box"],
                        page_size=state["page_metadata"][page_num]["size"],
                        output_file=output_file,
                        dpi=300
                    )
                    
        self.log("ImageCropperNode execution completed",
                 num_total_image=len(cropped_images))
        
        return FileState(image_paths=cropped_images)


class TableCropperNode(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__

    def execute(self, state: FileState) -> FileState:
        pdf_file = state["file_paths"]["original_pdf"]
        page_numbers = list(state["page_metadata"].keys())

        output_dir = state["file_paths"]["processed_dir"] / "tables"

        cropped_tables = dict()
        for page_num in page_numbers:
            figure_elements = state["page_elements"].get(page_num, {}).get("table_elements", [])
            for element in figure_elements:
                if element["category"] == "table":
                    output_file = output_dir / f"{element['id']}.png"
                    cropped_tables[element["id"]] = output_file
                    ImageCropper.process_pdf_page(
                        pdf_file=pdf_file,
                        page_num=page_num,
                        coordinates=element["bounding_box"],
                        page_size=state["page_metadata"][page_num]["size"],
                        output_file=output_file,
                        dpi=300
                    )
                    
        self.log("ImageCropperNode execution completed",
                 num_total_table=len(cropped_tables))
        
        return FileState(table_paths=cropped_tables)


class ExtractTextNode(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__

    def execute(self, state: FileState) -> FileState:
        page_numbers = list(state["page_metadata"].keys())

        extracted_texts = dict()

        for page_num in page_numbers:
            extracted_texts[page_num] = ""

            for element in state["page_elements"].get(page_num, {}).get("text_elements", []):
                extracted_texts[page_num] += element["text"]
        
        self.log("ExtractTextNode execution completed",
                 num_total_text=len(extracted_texts))

        return FileState(texts=extracted_texts)


class TableMarkdownExtractorNode(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "TableMarkdownExtractorNode"

    def execute(self, state: FileState):
        table_markdowns = table_markdown_extractor.invoke(
            state["table_summary_batches"],
        )

        table_markdown_output = dict()

        for data_batch, table_summary in zip(
            state["table_summary_batches"], table_markdowns
        ):
            table_markdown_output[data_batch["id"]] = table_summary

        return FileState(table_markdowns=table_markdown_output)
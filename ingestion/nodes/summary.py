from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain

from ingestion.chains.summary import (
    extract_image_summary,
    extract_table_summary,  
)
from ingestion.states import FileState
from ingestion.nodes.base import BaseNode


class PageSummaryNode(BaseNode):
    def __init__(self, api_key, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.api_key = api_key

    def create_page_summary_chain(self):
        prompt = PromptTemplate.from_template(
            """Please summarize the sentence according to the following REQUEST.
            
        REQUEST:
        1. Summarize the main points in bullet points.
        2. Write the summary in same language as the context.
        3. DO NOT translate any technical terms.
        4. DO NOT include any unnecessary information.
        5. Summary must include important entities, numerical values.

        CONTEXT:
        {context}

        SUMMARY:"
        """
        )

        llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0,
            api_key=self.api_key,
        )

        page_text_summary_chain = create_stuff_documents_chain(llm, prompt)
        return page_text_summary_chain

    def execute(self, state: FileState) -> FileState:
        texts = state["texts"]

        page_summaries = dict()

        sorted_texts = sorted(texts.items(), key=lambda x: x[0])

        inputs = [
            {"context": [Document(page_content=text)]}
            for page_num, text in sorted_texts
        ]
        text_summary_chain = self.create_page_summary_chain()

        summaries = text_summary_chain.batch(inputs)

        for page_num, summary in enumerate(summaries):
            page_summaries[page_num] = summary
        
        self.log("PageSummaryNode execution completed",
                 page_summaries=page_summaries)
        
        return FileState(page_summaries=page_summaries)
    

class ImageSummaryNode(BaseNode):
    def __init__(self, api_key, **kwargs):
        super().__init__(**kwargs)
        self.name = "CreateImageSummaryNode"
        self.api_key = api_key

    def create_image_summary_data_batches(self, state: FileState):
        data_batches = []

        page_numbers = sorted(list(state["page_elements"].keys()))

        for page_num in page_numbers:
            text = state["page_summaries"][page_num]
            for image_element in state["page_elements"][page_num]["figure_elements"]:
                image_id = int(image_element["id"])

                data_batches.append(
                    {
                        "image": state["image_paths"][image_id],
                        "text": text,
                        "page": page_num,
                        "id": image_id,
                        "language": state["language"],
                    }
                )
        return data_batches

    def execute(self, state: FileState):
        image_summary_data_batches = self.create_image_summary_data_batches(state)
        image_summaries = extract_image_summary.invoke(
            image_summary_data_batches,
        )

        image_summary_output = dict()

        for data_batch, image_summary in zip(
            image_summary_data_batches, image_summaries
        ):
            image_summary_output[data_batch["id"]] = image_summary

        return FileState(image_summaries=image_summary_output)


class TableSummaryNode(BaseNode):
    def __init__(self, api_key, **kwargs):
        super().__init__(**kwargs)
        self.name = "CreateTableSummaryNode"
        self.api_key = api_key

    def create_table_summary_data_batches(self, state: FileState):
        data_batches = []

        page_numbers = sorted(list(state["page_elements"].keys()))

        for page_num in page_numbers:
            text = state["page_summaries"][page_num]
            for image_element in state["page_elements"][page_num]["table_elements"]:
                image_id = int(image_element["id"])
                
                data_batches.append(
                    {
                        "table": state["table_paths"][image_id],
                        "text": text,
                        "page": page_num,
                        "id": image_id,
                        "language": state["language"]
                        }
                )
        return data_batches

    def execute(self, state: FileState):
        table_summary_data_batches = self.create_table_summary_data_batches(state)
        table_summaries = extract_table_summary.invoke(
            table_summary_data_batches,
        )

        table_summary_output = dict()

        for data_batch, table_summary in zip(
            table_summary_data_batches, table_summaries
        ):
            table_summary_output[data_batch["id"]] = table_summary

        return FileState(
            table_summaries=table_summary_output,
            table_summary_batches=table_summary_data_batches,
        )
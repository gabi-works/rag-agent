from typing import List, Optional
from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema.retriever import BaseRetriever
from langchain.retrievers import BM25Retriever, EnsembleRetriever

from ingestion.utils.document_processor import clean_retrieved_documents


class Retriever:
    def __init__(self, target_docs: List[Document]):
        self.target_docs = target_docs
        self.retriever: Optional[BaseRetriever] = None

    def get_retriever(self) -> BaseRetriever:
        if self.retriever is None:
            bm25_retriever = BM25Retriever.from_documents(self.target_docs)
            bm25_retriever.k = 5

            embedding = OpenAIEmbeddings()
            faiss_vectorstore = FAISS.from_documents(self.target_docs, embedding)
            faiss_retriever = faiss_vectorstore.as_retriever(search_kwargs={"k": 5})

            self.retriever = EnsembleRetriever(
                retrievers=[bm25_retriever, faiss_retriever],
                weights=[0.7, 0.3],
            )
        return self.retriever

    def retrieve_and_check(
        self,
        question: str,
        groundedness_check: Optional[callable] = None,
        use_checker: bool = False,
    ) -> List[Document]:
        if self.retriever is None:
            self.get_retriever()

        retrieved_documents = self.retriever.invoke(question)
        cleaned_documents = clean_retrieved_documents(retrieved_documents)

        if not use_checker:
            return cleaned_documents

        checking_inputs = [
            {"context": doc.page_content, "input": question}
            for doc in cleaned_documents
        ]

        checked_results = groundedness_check.batch(checking_inputs)

        return [
            doc
            for doc, result in zip(cleaned_documents, checked_results)
            if result.score == "yes"
        ]

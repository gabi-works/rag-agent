from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers import BM25Retriever, EnsembleRetriever

from ingestion.utils.document_processor import clean_retrieved_documents

def get_retriever(target_docs):
    bm25_retriever = BM25Retriever.from_documents(
        target_docs,
    )
    bm25_retriever.k = 5

    embedding = OpenAIEmbeddings()

    faiss_vectorstore = FAISS.from_documents(
        target_docs,
        embedding,
    )
    faiss_retriever = faiss_vectorstore.as_retriever(search_kwargs={"k": 5})

    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever],
        weights=[0.7, 0.3],
    )
    return ensemble_retriever


def retrieve_and_check(question, 
                       retriever, 
                       groundedness_check=None,
                       use_checker=False):
    
    retrieved_documents = retriever.invoke(question)

    cleaned_documents = clean_retrieved_documents(retrieved_documents)

    filtered_documents = []
    if use_checker:
        checking_inputs = [
            {"context": doc.page_content, "input": question}
            for doc in cleaned_documents
        ]

        checked_results = groundedness_check.batch(checking_inputs)

        filtered_documents = [
            doc
            for doc, result in zip(cleaned_documents, checked_results)
            if result.score == "yes"
        ]
    else:
        filtered_documents = cleaned_documents

    return filtered_documents
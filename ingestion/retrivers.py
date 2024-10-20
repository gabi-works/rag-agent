from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers import BM25Retriever, EnsembleRetriever


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
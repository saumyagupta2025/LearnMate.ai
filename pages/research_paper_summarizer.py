import streamlit as st
import pypdf as pdf
import pandas as pd
import numpy as np
from llama_index.llms.ollama import Ollama
import re
import nltk
from nltk.corpus import stopwords
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# loads BAAI/bge-small-en
# embed_model = HuggingFaceEmbedding()

# loads BAAI/bge-small-en-v1.5
embed_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

nltk.download("stopwords")
stop_words = set(stopwords.words("english"))



llm = Ollama(model="llama2", request_timeout=120.0)
# resp = llm.complete("Who is Paul Graham?")

# print(resp)



# Reading pdf
def read_pdf(file_path):
    reader = pdf.PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    return text


def data_preprocessing(text):
    text = text.lower()

    # Removing punctuation
    text = re.sub(r"[^\w\s]", "", text)

    # removing stop words
    text = " ".join(word for word in text.split() if word not in stop_words)
    return text

def chunking(cleaned_text):
    text_splitter = RecursiveCharacterTextSplitter(
    # Set a really small chunk size, just to show.
    chunk_size=1000,
    chunk_overlap=150,
    length_function=len,
    is_separator_regex=False,
    )

    chunks = text_splitter.create_documents([cleaned_text])
    return chunks

# def create_text_embeddings(embed_model, chunks):

#     for chunk in chunks:
#         embeddings = embed_model.get_text_embedding("Hello World!")
#     # Store in FAISS

def create_text_embeddings(embed_model, chunks):
    documents = []
    for chunk in chunks:
        chunk_text = chunk.page_content
        chunk_embedding = embed_model.embed_documents(chunk_text)
        documents.append(Document(page_content=chunk_text, embedding=chunk_embedding))

    vectorstore = FAISS.from_documents(documents, embed_model)

    return vectorstore


def generate_response(query, retrieved_docs, llm):
    # Concatenate relevant document chunks for the prompt
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    # Prepare the prompt for the LLM, combining the query with context
    prompt = f"Using the following context, answer the query:\n\nContext:\n{context}\n\nQuery: {query}"
    # Generate the response
    response = llm.complete(prompt)
    return response

if __name__ == '__main__':
    file_path = 'sample_data/research_papers/NIPS-2017-attention-is-all-you-need-Paper.pdf'
    extracted_text = read_pdf(file_path)
    cleaned_text = data_preprocessing(extracted_text)
    chunks = chunking(cleaned_text)
    faiss_vectorstore = create_text_embeddings(embed_model, chunks)

    print("completed main")

    # Perform vector search and retrieval
    user_query = "Explain the concept of attention in transformers explained in this document."
    docs = faiss_vectorstore.similarity_search(user_query, k=5)

    # Retrieved vectors
    print("retrieved docs")
    for doc in docs:
        print("\n =============================== ")
        print(doc)
        print("\n")


    # Generate a response based on the retrieved documents
    llm_response = generate_response(user_query, docs, llm)

    print("LLM Response:\n", llm_response)


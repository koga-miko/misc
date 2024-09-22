from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM
from langchain.indexes import VectorstoreIndexCreator

loader = PyPDFLoader("menyu-reishuu.pdf")

embeddings = OllamaEmbeddings(model="mxbai-embed-large")
llm = OllamaLLM(model="gemma2:27b")

index = VectorstoreIndexCreator(
    vectorstore_cls=Chroma,
    embedding=embeddings
).from_loaders([loader])

query = "しぼルトメニューとは何ですか?日本語で回答して下さい。"

answer = index.query(query, llm=llm)
print(answer)

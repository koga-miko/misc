from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM
from langchain.indexes import VectorstoreIndexCreator

loader = PyPDFLoader("menyu-reishuu.pdf")

embeddings = OllamaEmbeddings(model="gemma2")
llm = OllamaLLM(model="gemma2")

index = VectorstoreIndexCreator(
    vectorstore_cls=Chroma,
    embedding=embeddings
).from_loaders([loader])

# query = "しぼルトメニューとは何ですか?日本語で回答して下さい。"
query = "しぼルトメニューについて、具体的なメニューを5点ほど教えてください"

answer = index.query(query, llm=llm)
print(answer)

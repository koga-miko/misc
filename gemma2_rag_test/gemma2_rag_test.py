import logging

# ログの設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging.debug("!!!start!!!")

logging.debug("import PyPDFLoader")
from langchain_community.document_loaders import PyPDFLoader
logging.debug("import Chroma")
from langchain_chroma import Chroma
logging.debug("import OllamaEmbeddings")
from langchain_ollama import OllamaEmbeddings
logging.debug("import OllamaLLM")
from langchain_ollama import OllamaLLM
logging.debug("import VectorstoreIndexCreator")
from langchain.indexes import VectorstoreIndexCreator
logging.debug("import logging")

logging.debug("call PyPDFLoader")
loader = PyPDFLoader("menyu-reishuu.pdf")

logging.debug("call OllamaEmbeddings")
embeddings = OllamaEmbeddings(model="gemma2")
llm = OllamaLLM(model="gemma2")

logging.debug("call VectorstoreIndexCreator")
index = VectorstoreIndexCreator(
    vectorstore_cls=Chroma,
    embedding=embeddings
).from_loaders([loader])

# query = "しぼルトメニューとは何ですか?日本語で回答して下さい。"
logging.debug("set query text")
query = "しぼルトメニューについて、具体的なメニューを5点ほど教えてください"

logging.debug("call index.query")
answer = index.query(query, llm=llm)
print(answer)
logging.debug("!!!end!!!")

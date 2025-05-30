from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    Settings,
    get_response_synthesizer)
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode, MetadataMode
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.retrievers import VectorIndexRetriever
import qdrant_client
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# モデル名の設定
llm_model_name = "gemma2:2b"
embedding_model_name = "nomic-embed-text:latest"

# ローカルデータディレクトリを読み込み、データをチャンクに分割
docs = SimpleDirectoryReader(input_dir=".", required_exts=[".pdf"]).load_data(show_progress=True)
text_parser = SentenceSplitter(chunk_size=512, chunk_overlap=100)

# ローカルのQdrantベクトルストアを作成
logger.info("initializing the vector store related objects")
client = qdrant_client.QdrantClient(url="http://127.0.0.1:6333/")
vector_store = QdrantVectorStore(client=client, collection_name="research_papers")

# ローカルのベクトル埋め込みモデルを初期化
logger.info("initializing the OllamaEmbedding")
embed_model = OllamaEmbedding(model_name=embedding_model_name, base_url='http://127.0.0.1:11434')

# グローバル設定の初期化
logger.info("initializing the global settings")
Settings.embed_model = embed_model
Settings.llm = Ollama(model=llm_model_name, base_url='http://127.0.0.1:11434', request_timeout=600)
Settings.transformations = [text_parser]

text_chunks = []
doc_ids = []
nodes = []

# ドキュメントを列挙
logger.info("enumerating docs")
for doc_idx, doc in enumerate(docs):
    curr_text_chunks = text_parser.split_text(doc.text)
    text_chunks.extend(curr_text_chunks)
    doc_ids.extend([doc_idx] * len(curr_text_chunks))

# テキストチャンクを列挙
logger.info("enumerating text_chunks")
for idx, text_chunk in enumerate(text_chunks):
    node = TextNode(text=text_chunk)
    src_doc = docs[doc_ids[idx]]
    node.metadata = src_doc.metadata
    nodes.append(node)

# ノードを列挙
logger.info("enumerating nodes")
for node in nodes:
    node_embedding = embed_model.get_text_embedding(
        node.get_content(metadata_mode=MetadataMode.ALL)
    )
    node.embedding = node_embedding

# ストレージコンテキストの初期化
logger.info("initializing the storage context")
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# ノードをVectorStoreIndexにインデックス
logger.info("indexing the nodes in VectorStoreIndex")
index = VectorStoreIndex(
    nodes=nodes,
    storage_context=storage_context,
    transformations=Settings.transformations,
)

# VectorIndexRetrieverを初期化（top_kを5に設定）
logger.info("initializing the VectorIndexRetriever with top_k as 5")
vector_retriever = VectorIndexRetriever(index=index, similarity_top_k=5)
response_synthesizer = get_response_synthesizer()

# RetrieverQueryEngineインスタンスを作成
logger.info("creating the RetrieverQueryEngine instance")
vector_query_engine = RetrieverQueryEngine(
    retriever=vector_retriever,
    response_synthesizer=response_synthesizer,
)

# クエリに対する応答を取得
logger.info("retrieving the response to the query")

# ユーザーからの入力を継続的に取得するループを開始
while True:
    # ユーザーからのクエリを取得
    user_query = input("Enter your query [type 'bye' to 'exit']: ")

    # ユーザーがループを終了したいかどうかを確認
    if user_query.lower() == "bye" or user_query.lower() == "exit":
        break

    response = vector_query_engine.query(str_or_query_bundle=user_query)
    print(response)

# クライアントを閉じる
client.close()
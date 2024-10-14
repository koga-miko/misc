import logging
from langchain_community.llms import Ollama

# ログの設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# gemma2を使用して質問に回答する機能を持つクラス
class Gemma2Accessor:
    def __init__(self):
        # Ollamaオブジェクトを初期化
#        model="gemma2:2b"
        model="lucas2024/gemma-2-2b-jpn-it:q8_0" # Googleが作成した日本語版のGemma2-2bモデル
        self.llm = Ollama(model=model)
        logging.info(f"Ollama model initialized with ${model}")

    # 質問に回答するメソッド
    def answer(self, question):
        logging.info(f"Answering question: {question}")
        response = self.llm.invoke(question)
        logging.debug(f"Response: {response}")
        return response
    
    # 翻訳するメソッド
    # 引数のlangは翻訳先の言語を指定する
    # 例), 日本語の場合は "日本語"とか"Japanese"とか、英語の場合は"英語"とか"English"とか
    def translate(self, text, lang_name = '英語'):
        logging.info(f"Translating text: {text} to language: {lang_name}")
        prev_text = f"次のテキストを {lang_name} へ変換してください。 "
        response = self.answer(prev_text + " " + text)
        logging.debug(f"Translated text: {response}")
        return response

# メイン関数
def main():
    logging.info("Main function started")
    gemma2_accessor = Gemma2Accessor()
    logging.info("Gemma2Accessor instance created")
    
    question = "What is the capital of Japan?"
    logging.info(f"Asking question: {question}")
    print(gemma2_accessor.answer(question))
    
    text_to_translate = "東京の気温はどれくらいですか？"
    logging.info(f"Translating text: {text_to_translate}")
    print(gemma2_accessor.translate(text_to_translate))
    
    text_to_translate = "What is the capital of Japan?"
    lang = 'ja'
    logging.info(f"Translating text: {text_to_translate} to language: {lang}")
    print(gemma2_accessor.translate(text_to_translate, lang_name=lang))

if __name__ == "__main__":
    main()
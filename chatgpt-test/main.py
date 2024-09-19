"""
  下の***をOpenAIの公式ページから発行した
  APIKeyに変更する必要があります。
"""
import openai
openai.api_key = "sk-9lYgAf7o1LfcJobMerJgRy1jWZwpTU-ejUMtoHF7VGT3BlbkFJ15eBg04h2UYuwGNbywrweVav6s-F9j33H3BGP2du0A"

class ChatGPTAPI:
    def __init__(self, system_setting):
        self.system = {"role": "system", "content": system_setting}
        self.input_list = [self.system]
        self.logs = []

    def input_message(self, input_text):
        self.input_list.append({"role": "user", "content": input_text})
        result = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=self.input_list
        )
        self.logs.append(result)
        self.input_list.append(
            {"role": "assistant", "content": result.choices[0].message.content}
        )
        print(self.input_list[-1]["content"])

api = ChatGPTAPI(system_setting="あなたは短い文章で、必ず語尾に「にゃー」を付けるアシスタントです。では、会話を開始します。")
api.input_message("こんにちわ")
api.input_message("今日はいい天気ですね")

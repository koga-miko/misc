import sys
import os
import re
import pdf_to_linearray

'''
役職抽出クラス
'''
class RolesPicker:
    #   役職の階層を定義する
    roles_hierarchy = [
        { "hierarchy_names_regex": r"事業部", "role_name_regex": r"事業部長" },
        { "hierarchy_names_regex": r"部", "role_name_regex": r"部長" },
        { "hierarchy_names_regex": r"室", "role_name_regex": r"(?:室長|主査)" },
        { "hierarchy_names_regex": r"課", "role_name_regex": r"(?:課長|係長|主任|リーダー)"},
    ]

    #   <～(事業部or部or室or課など)> <役職> <氏名> [メモ] という形式の文字列を抽出する
    templete_regex = r"^\s*(\S.+?\S%hierarchy_names_regex%)\s+(%role_name_regex%)\s+(\S+\s+\S+).*$"
    #   <役職> <空白> <氏名> [メモ] という形式の文字列を抽出する
    templete_no_groupname_regex = r"^\s*(%role_name_regex%)\s+(\S+\s+\S+).*$"

    '''
    コンストラクタ
    '''
    def __init__(self):
        self.date_reset()
    
    '''
    出力データを初期化する
    '''
    def date_reset(self):
        self.output_data = []
        self.group_names = ["" for i in range(len(RolesPicker.roles_hierarchy))]

    '''
    グループ名、役職、氏名、メモをタブ区切りで出力データに追加する
    '''
    def append_data(self, group_names, role_name, name, memo):
        self.output_data.append({"グループ名":group_names, "役割名":role_name, "氏名":name, "メモ":memo})

    '''
    出力データをファイルに出力する
    '''
    def output_to_file(self, output_file, title = ""):
        with open(output_file, "w", encoding="utf-8") as f:
            if title != "":
                f.write(title + "\n")
            f.write(self.output_data_to_string())
    
    '''
    出力データを文字列に変換する
    '''
    def output_data_to_string(self):
        output_str = ""
        for data in self.output_data:
            output_str += "\t".join(data["グループ名"]) + "\t" + data["役割名"] + "\t" + data["氏名"] + "\t" + data["メモ"] + "\n"
        return output_str

    '''
    正規表現のマッチ結果から氏名とメモを取得する
    '''
    def get_name_and_memo(self, match, name_index):
        name = match.group(name_index)
        # 氏名の後ろにメモがあるかどうかを判定
        if match.regs[name_index][1] < len(match.string):
            # 氏名の後にメモがある場合
            memo = match.string[match.regs[name_index][1]:].strip()
        else:
            memo = ""
        return name, memo

    '''
    PDFファイルからデータを抽出する
    '''
    def pickup_data_from_pdf(self, input_file):
        role_name = ""
        name = ""
        memo = ""
        for line in pdf_to_linearray.exec(input_file):
            for index, role_item in enumerate(RolesPicker.roles_hierarchy):
                format_text = RolesPicker.templete_regex.replace(
                    "%hierarchy_names_regex%"
                    , role_item["hierarchy_names_regex"])
                format_text = format_text.replace(
                    "%role_name_regex%"
                    , role_item["role_name_regex"])
                match = re.match(format_text, line)
                if match:
                    self.group_names[index] = match.group(1)
                    # 一つ下以降の階層のグループ名をクリア
                    for i in range(index + 1, len(RolesPicker.roles_hierarchy)):
                        self.group_names[i] = ""
                    role_name = match.group(2)
                    # 氏名と氏名の後ろにメモがあればそれも取得
                    (name, memo) = self.get_name_and_memo(match, 3)
                    self.append_data(self.group_names, role_name, name, memo)
                else:
                    format_no_groupname_text = RolesPicker.templete_no_groupname_regex.replace(
                            "%role_name_regex%"
                            , role_item["role_name_regex"])
                    match = re.match(format_no_groupname_text, line)
                    if match:
                        role_name = match.group(1)
                        # 氏名と氏名の後ろにメモがあればそれも取得
                        (name, memo) = self.get_name_and_memo(match, 2)
                        self.append_data(self.group_names, role_name, name, memo)

    '''
    PDFファイルからデータを抽出してファイルに出力する
    '''
    def make_pickup_data_and_output(input_files):
        rp = RolesPicker()
        for input_file in input_files:
            output_file = input_file + '.txt'
            rp.pickup_data_from_pdf(input_file)
            rp.output_to_file(output_file, "Source file name: " + os.path.basename(input_file))
            rp.date_reset()

#   メイン処理
def main(argv):
    if len(argv) == 0 or argv[0] == "-h" or argv[0] == "--help":
        print("Usage: python roles.py [input_pdf_file1] [input_pdf_file2] ... [input_pdf_fileN]")
        exit(0)
    RolesPicker.make_pickup_data_and_output(argv)

if __name__ == '__main__':
    main(sys.argv[1:])
# [Github copilotに依頼した内容]
# pdfファイルを開いて、内容のテキストを取り出し、行単位の配列としてreturnする関数を作成する
import PyPDF2
import sys

def exec(file_path):
    lines = []
    
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        for page in reader.pages:
            text = page.extract_text()
            lines.extend(text.split('\n'))
    
    return lines

if __name__ == '__main__':
    # Example usage
    file_path = sys.argv[1]
    lines = exec(file_path)
    for line in lines:
        print(line)

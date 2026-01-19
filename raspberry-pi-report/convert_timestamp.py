import sys
from datetime import datetime

def convert_timestamp(line):
    """
    yyyy/mm/dd HH:MM:SS.ssssss形式の文字列を
    UNIX時間の秒.ミリ秒形式に変換する
    """
    line = line.strip()
    if not line:
        return None
    
    try:
        # 日時部分とマイクロ秒部分を分離
        # yyyy/mm/dd HH:MM:SS と .ssssss に分ける
        datetime_part, microsec_part = line.rsplit('.', 1)
        
        # datetime部分をパース (yyyy/mm/dd HH:MM:SS)
        dt = datetime.strptime(datetime_part, '%Y/%m/%d %H:%M:%S')
        
        # UNIX時間（秒）を取得
        unix_timestamp = int(dt.timestamp())
        
        # マイクロ秒部分から最初の3桁（ミリ秒）を取得
        millisec = microsec_part[:3]
        
        # 結果を結合
        result = f"{unix_timestamp}.{millisec}"
        
        return result
    
    except Exception as e:
        print(f"Error processing line: {line}", file=sys.stderr)
        print(f"Error details: {e}", file=sys.stderr)
        return None

def main():
    # 標準入力から読み込む場合
    for line in sys.stdin:
        result = convert_timestamp(line)
        if result:
            print(result)

if __name__ == "__main__":
    main()

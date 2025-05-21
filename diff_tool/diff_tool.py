'''
２つのテキストファイルを比較して、その結果をExcelファイルに出力するツールです。
入力： 2つのテキストファイルのパス
出力： Excelファイル（差分を含む）
処理：２つのテキストファイルを比較して、追加のある行、削除のある行、変更のある行を抽出し、Excelファイルに出力します。
使用ライブラリ：difflib, openpyxl, pandas
使用方法：diff_tool.py <file1> <file2> <output_file>
'''

import difflib
import openpyxl
import pandas as pd
import sys
import os
import re
import logging

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("diff_tool.log"),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging is set up.")

def read_file(file_path):
    """Read a file and return its content as a list of lines."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        logging.info(f"File {file_path} read successfully.")
        return lines
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        raise

def write_to_excel(diff_data, output_file):
    """Write the diff data to an Excel file."""
    try:
        df = pd.DataFrame(diff_data)
        df.to_excel(output_file, index=False)
        logging.info(f"Diff data written to {output_file} successfully.")
    except Exception as e:
        logging.error(f"Error writing to Excel file {output_file}: {e}")
        raise

def compare_files(file1_lines, file2_lines):
    """Compare two lists of lines and return the differences."""
    d = difflib.Differ()
    diff = list(d.compare(file1_lines, file2_lines))

    added_lines = []
    removed_lines = []
    modified_lines = []

    for line in diff:
        if line.startswith('+ '):
            added_lines.append(line[2:])
        elif line.startswith('- '):
            removed_lines.append(line[2:])
        elif line.startswith('? '):
            modified_lines.append(line[2:])

    return added_lines, removed_lines, modified_lines

def main(file1, file2, output_file):
    """Main function to execute the diff tool."""
    setup_logging()

    # Read files
    file1_lines = read_file(file1)
    file2_lines = read_file(file2)

    # Compare files
    added_lines, removed_lines, modified_lines = compare_files(file1_lines, file2_lines)

    # Prepare data for Excel
    diff_data = {
        'Added Lines': added_lines,
        'Removed Lines': removed_lines,
        'Modified Lines': modified_lines
    }

    # Write to Excel
    write_to_excel(diff_data, output_file)
    logging.info("Diff tool completed successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python diff_tool.py <file1> <file2> <output_file>")
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]
    output_file = sys.argv[3]

    # Check if files exist
    if not os.path.isfile(file1):
        print(f"File {file1} does not exist.")
        sys.exit(1)
    if not os.path.isfile(file2):
        print(f"File {file2} does not exist.")
        sys.exit(1)

    main(file1, file2, output_file)
    logging.info("Diff tool started.")
    logging.info(f"Files to compare: {file1} and {file2}")
    logging.info(f"Output file: {output_file}")
    logging.info("Diff tool finished.")
    logging.info("End of log.")
    logging.info("======================================")
    
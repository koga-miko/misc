import os
import re

def rename_files(directory, pattern, replacement):
    for filename in os.listdir(directory):
        new_filename = re.sub(pattern, replacement, filename)
        if new_filename != filename:
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
            print(f'Renamed: {filename} -> {new_filename}')

if __name__ == "__main__":
    directory = '/c:/Users/yoshi/OneDrive/work/misc/small_tools'
    pattern = r'your_regex_pattern_here'  # Replace with your regex pattern
    replacement = 'your_replacement_here'  # Replace with your replacement string
    rename_files(directory, pattern, replacement)
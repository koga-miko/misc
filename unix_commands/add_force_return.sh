#!bin/bash
file_path=Window.java
sed -i -E "s#^(\s+)(public void setFlags\(int flags, int mask\) \{$)#\1\2 //Add forced termination during FLAG_SECURE(8192)\n\1     if (flags == 8192) {\n\1        return;\n\1    }#" $file_path


sed -i -E "s#^(\s+)($search_re)#\1\2 //Add forced termination during FLAG_SECURE(8192)\n\1     if (flags == 8192) {\n\1        return;\n\1    }#" $file_path
sed -i -E 's/^(\s+)(public void setFlags\(int flags, int mask\) \{)$/\1\2\n\1    if\(ABC\) \{\n\1        return;\n    }\/' your_file.txt

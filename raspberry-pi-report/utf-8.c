// 事前設定：
// ・コンパイラにソースコード内にあるリテラル文字列をutf-8として解釈・保持するように指示するため、
// 　プロジェクトのプロパティ > C/C++ > コマンド ライン > 追加のプロパティに/utf-8を追加してください

#include <stdio.h>

// 文字数を数える
int getUtf8StringLength(char* str)
{
	int length = 0;
	while (*str)
	{
		if ((*str & 0x80) == 0) // ASCII
		{
			length++;
		}
		else if ((*str & 0xE0) == 0xC0) // 2-byte character
		{
			length++;
			str++;
		}
		else if ((*str & 0xF0) == 0xE0) // 3-byte character
		{
			length++;
			str += 2;
		}
		else if ((*str & 0xF8) == 0xF0) // 4-byte character
		{
			length++;
			str += 3;
		}
		str++;
	}
	return length;
}

const unsigned char str1[] = "UTF-8は可変長";
const unsigned char str2[] = "UTF-8はヌル終端";

int main()
{
	int len = 0;
	unsigned char str[20] = {0};

	system("chcp 65001");	// Windowsのコマンドプロンプトの表示をUTF-8にする

	strncpy(str, str1, sizeof(str) - 1);
	len = getUtf8StringLength(str);
	printf("str1=%s: len=%d\n", str, len);

	strncpy(str, str2, sizeof(str) - 1);
	len = getUtf8StringLength(str);
	printf("str2=%s: len=%d\n", str, len);
}

// 【問題】
//    このコードを実行すると、str2の内容と文字数が不正となります。
//    1. なぜstr2の内容は不正になるのか？
//    2. なぜstr2の文字数は不正になるのか？
//    3. このような不正を発生させないために考えられる対策は？
//    以上3点を自由にデバッグしてみて考えてください。

// take-ten.c

#include<stdio.h>
#include<stdlib.h>
#include<stdbool.h>
#include<string.h>

#define OPE_POS1	(0)
#define OPE_POS2	(1)
#define OPE_POS3	(2)
#define OPE_LEN		(3)
#define DIGIT_POS1	(OPE_LEN)
#define DIGIT_POS2	(OPE_LEN + 1)
#define DIGIT_POS3	(OPE_LEN + 2)
#define DIGIT_POS4	(OPE_LEN + 3)
#define DIGIT_LEN	(4)
#define TOTAL_LEN	(OPE_LEN + DIGIT_LEN)
#define FULL_USED_PTN (0x7F)
#define DISPSTR_LEN	(32)

static const char ope_chars[] = { '+', '-', '*', '/' };

static int get_val(char* out_chars, int out_chars_len, int curpos, int* val);
static bool calc(char ope_char, int val1, int val2, int* outval);
static int calc_r(char* out_chars, int out_chars_len, int curpos, int* outval);
static void shuffle_and_calc_r(char* combi_chars, int curpos, char* out_chars, unsigned char used_index_bits);
void shuffle_and_calc(char* combi_chars);
static int get_val_dispstr(char* out_chars, int out_chars_len, int curpos, char* dispstr, char* ope);
static int display_r(char* out_chars, int out_chars_len, int curpos, char* dispstr);

static int get_val(char* out_chars, int out_chars_len, int curpos, int* val) {
	// 最低限計算可能なデータが残っていない
	if (curpos >= out_chars_len) {
		return 0;
	}
	switch (out_chars[curpos]) {
	case '+':
	case '-':
	case '*':
	case '/':
		curpos = calc_r(out_chars, out_chars_len, curpos, val);
		if (curpos == 0) {
			return 0;
		}
		break;
	default:
		if ('1' <= out_chars[curpos] && out_chars[curpos] <= '9') {
			*val = out_chars[curpos] - '0';
			curpos++;
		}
		else {
			return 0;
		}
	}
	return curpos;
}

static bool calc(char ope_char, int val1, int val2, int *outval) {
	switch (ope_char) {
	case '+':
		*outval = val1 + val2;
		break;
	case '-':
		*outval = val1 - val2;
		break;
	case '*':
		*outval = val1 * val2;
		break;
	case '/':
		if ((val2 == 0) || ((val1 % val2) != 0)) {
			return false;
		}
		*outval = val1 / val2;
		break;
	default:
		return false;
	}
	return true;
}

static int calc_r(char* out_chars, int out_chars_len, int curpos, int *outval) {
	// 最低限計算可能なデータが残っていない
	if (curpos + 2 >= out_chars_len) {
		return 0;
	}
	int val1, val2;
	switch (out_chars[curpos]) {
	case '+':
	case '-':
	case '*':
	case '/':
		{
			char ope_char = out_chars[curpos];
			curpos++;
			curpos = get_val(out_chars, out_chars_len, curpos, &val1);
			if (curpos == 0) {
				return 0;
			}
			curpos = get_val(out_chars, out_chars_len, curpos, &val2);
			if (curpos == 0) {
				return 0;
			}
			if (false == calc(ope_char, val1, val2, outval)) {
				return 0;
			}
		}
		break;
	default:
		return 0;
	}
	return curpos;
}

static void shuffle_and_calc_r(char* combi_chars, int curpos, char* out_chars, unsigned char used_index_bits) {
	if (curpos < TOTAL_LEN) {
		for (int i = 0; i < TOTAL_LEN; i++) {
			out_chars[curpos] = combi_chars[i];
			shuffle_and_calc_r(combi_chars, curpos + 1, out_chars, used_index_bits | (unsigned char)(0x01 << i));
		}
	}
	else {
		// combi_charsを満遍なく使用している場合
		if ((used_index_bits & FULL_USED_PTN) == FULL_USED_PTN) {
			int outval = 0;
			if ((TOTAL_LEN == calc_r(out_chars, TOTAL_LEN, 0, &outval)) && (outval == 10)) {
				char dispstr[DISPSTR_LEN];
				display_r(out_chars, TOTAL_LEN, 0, dispstr);
				printf("%s = %d\n", dispstr, outval);
			}
		}
	}

}

void shuffle_and_calc(char* combi_chars) {
	// ※combi_charsのNULL終端を除く(制御対象の)長さはTOTAL_LEN固定の想定
	char out_chars[TOTAL_LEN + 1];
	char used_index_bits = 0x00;
	memset(out_chars, 0, sizeof(out_chars));
	shuffle_and_calc_r(combi_chars, 0, out_chars, used_index_bits);
}

// 関数使用者は引数dispstrのために、使用上最大長となる、演算子3文字・数値7文字・括弧4文字・その間の(3+7+4-1の)13文字とNULL終端1文字を含む28文字を含む32バイト(DISPSTR_LEN)の領域を用意すること
// opeが示す領域には、関数内で式だった場合はその際の演算子を、そうでない場合はヌル文字(0)を設定して返す
static int get_val_dispstr(char* out_chars, int out_chars_len, int curpos, char *dispstr, char *ope) {
	// 最低限計算可能なデータが残っていない
	if (curpos >= out_chars_len) {
		return 0;
	}
	switch (out_chars[curpos]) {
	case '+':
	case '-':
	case '*':
	case '/':
	{
		char tmpstr[DISPSTR_LEN];
		char ope_char = out_chars[curpos];
		curpos = display_r(out_chars, out_chars_len, curpos, tmpstr);
		if (curpos == 0) {
			return 0;
		}
		*ope = ope_char;
		snprintf(dispstr, DISPSTR_LEN, "%s", tmpstr);
	}
		break;
	default:
		if ('1' <= out_chars[curpos] && out_chars[curpos] <= '9') {
			snprintf(dispstr, DISPSTR_LEN, "%c", out_chars[curpos]);
			*ope = 0;
			curpos++;
		}
		else {
			return 0;
		}
	}
	return curpos;
}

static int display_r(char* out_chars, int out_chars_len, int curpos, char* dispstr) {
	// 最低限計算可能なデータが残っていない
	if (curpos + 2 >= out_chars_len) {
		return 0;
	}
	switch (out_chars[curpos]) {
	case '+':
	case '-':
	case '*':
	case '/':
	{
		char child_str[DISPSTR_LEN], disp_str1[DISPSTR_LEN], disp_str2[DISPSTR_LEN];
		char child_ope;
		char ope_char = out_chars[curpos];
		curpos++;
		curpos = get_val_dispstr(out_chars, out_chars_len, curpos, child_str, &child_ope);
		if (curpos == 0) {
			return 0;
		}
		if ((ope_char == '*' || ope_char == '/') && (child_ope == '+' || child_ope == '-')) {
			snprintf(disp_str1, DISPSTR_LEN, "( %s )", child_str);
		}
		else {
			snprintf(disp_str1, DISPSTR_LEN, "%s", child_str);
		}
		curpos = get_val_dispstr(out_chars, out_chars_len, curpos, child_str, &child_ope);
		if (curpos == 0) {
			return 0;
		}
		if ((ope_char == '*' || ope_char == '/' || ope_char == '-') && (child_ope == '+' || child_ope == '-')) {
			snprintf(disp_str2, DISPSTR_LEN, "( %s )", child_str);
		}
		else {
			snprintf(disp_str2, DISPSTR_LEN, "%s", child_str);
		}
		snprintf(dispstr, DISPSTR_LEN, "%s %c %s", disp_str1, ope_char, disp_str2);
	}
	break;
	default:
		return 0;
	}
	return curpos;
}

void take_ten(char num1, char num2, char num3, char num4) {
	char combi_chars[TOTAL_LEN+1];
	combi_chars[DIGIT_POS1] = num1;
	combi_chars[DIGIT_POS2] = num2;
	combi_chars[DIGIT_POS3] = num3;
	combi_chars[DIGIT_POS4] = num4;
	combi_chars[TOTAL_LEN] = 0;
	for (int i = 0; i < sizeof(ope_chars); i++) {
		combi_chars[OPE_POS1] = ope_chars[i];
		for (int j = i; j < sizeof(ope_chars); j++) {
			combi_chars[OPE_POS2] = ope_chars[j];
			for (int k = j; k < sizeof(ope_chars); k++) {
				combi_chars[OPE_POS3] = ope_chars[k];
				shuffle_and_calc(combi_chars);
			}
		}
	}
}
int main(void) {
	take_ten('1', '2', '3', '8');
}
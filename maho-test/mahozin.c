#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N       (5)                     // N: 魔法陣の次元数を表す ※5だと重すぎて戻ってこない・・・
#define TOTAL_OF_LINE   ((N*N*N + N)/2) // 行あたりの合計値 ※1～Nの総和の公式 (N*N)(N*N+N)/2 を N で割った値
#define MIN_NUM (1)
#define MAX_NUM (N*N)
#define DEFAULT_NUMSETS_CAPA    (20000)
#define DEFAULT_MAHOSETS_CAPA   (10000)

typedef struct {
    int data[N];
} numset_t;

typedef struct {
    numset_t numsets[N];
} mahoset_t;

static numset_t *util_numsets;
static int util_numsets_capa;
static int util_numsets_num;

static mahoset_t *util_mahosets;
static int util_mahosets_capa;
static int util_mahosets_num;

static int created_mahozin_counter = 0;

void util_init(void){
    util_numsets_capa = 0;
    util_numsets_num = 0;
    util_numsets = malloc(sizeof(numset_t) * DEFAULT_NUMSETS_CAPA);
    if (util_numsets == NULL) {
        printf("numsets_init: error: alloc() is failed.");
        return;
    }
    util_numsets_capa = DEFAULT_NUMSETS_CAPA;

    util_mahosets_capa = 0;
    util_mahosets_num = 0;
    util_mahosets = malloc(sizeof(mahoset_t) * DEFAULT_MAHOSETS_CAPA);
    if (util_mahosets == NULL) {
        printf("mahosets_init: error: alloc() is failed.");
        return;
    }
    util_mahosets_capa = DEFAULT_MAHOSETS_CAPA;

}

void util_deinit(void) {
    if (util_mahosets != NULL) {
        free(util_mahosets);
        util_mahosets = NULL;
        util_mahosets_capa = 0;
        util_mahosets_num = 0;
    }
    if (util_numsets != NULL) {
        free(util_numsets);
        util_numsets = NULL;
        util_numsets_capa = 0;
        util_numsets_num = 0;
    }
}

int util_numsets_get_total_numsets(void) {
    return util_numsets_num;
}

int util_mahosets_get_total_mahosets(void) {
    return util_mahosets_num;
}

int util_mahosets_get_created_mahozin_counter(void) {
    return created_mahozin_counter;
}

void util_numsets_register_data(numset_t *numset){
    if (util_numsets == NULL) {
        printf("numsets_register_data(): error: util_numsets == NULL");
        return;
    }
    if (util_numsets_num >= util_numsets_capa) {
        int tmp_numsets_capa = (util_numsets_capa == 0 ? DEFAULT_NUMSETS_CAPA: util_numsets_capa * 2);
        numset_t *tmp_numsets = realloc(util_numsets, sizeof(numset_t) * tmp_numsets_capa);
        if (tmp_numsets == NULL) {
            printf("numsets_register_data(): error: realloc() is failed.");
            return;
        }
        util_numsets = tmp_numsets;
        util_numsets_capa = tmp_numsets_capa;
    }
    memcpy(&util_numsets[util_numsets_num], numset, sizeof(numset_t));
    util_numsets_num++;
}

void util_numsets_print(numset_t *numsets,int num) {
    if (numsets != NULL) {
        for (int i = 0; i < num; i++) {
            if (num > 1) {
                printf("[%d] ", i);
            }
            for (int j = 0; j < N; j++) {
                printf("%d", numsets[i].data[j]);
                if (j < N - 1) {
                    printf(", ");
                }
            }
            printf("\n");
        }
    }
}

void util_numsets_printall(void) {
    util_numsets_print(util_numsets, util_numsets_num);
}

static void util_numsets_make_r(numset_t *numset_buf, int curpos, int start_val) {
    if (curpos < N) {
        for (int i = start_val; i <= MAX_NUM; i++) {
            numset_buf->data[curpos] = i;
            util_numsets_make_r(numset_buf, curpos + 1, i + 1);
        }
    } else {
        int total = 0;
        for (int i = 0; i < N; i++) {
            total += numset_buf->data[i];
        }
        if (total == TOTAL_OF_LINE) {
            util_numsets_register_data(numset_buf);
            util_numsets_print(numset_buf, 1);
        }
    }
}

void util_numsets_make(void) {
    numset_t numset = {0};
    util_numsets_make_r(&numset, 0, MIN_NUM);
}

void util_mahosets_print(mahoset_t *mahosets, int num) {
    if (mahosets != NULL) {
        for (int i = 0; i < num; i++) {
            if (num > 1) {
                printf("*** mahosets[%d] ***\n", i);
            }
            for (int j = 0; j < N; j++) {
                printf("  ");
                for (int k = 0; k < N; k++) {
                    printf("%3d ", mahosets[i].numsets[j].data[k]);
                }
                printf("\n");
            }
            printf("\n");
        }
    }
}

void util_mahosets_printall(void) {
    util_mahosets_print(util_mahosets, util_mahosets_num);
}

void util_mahosets_register_data(mahoset_t *mahoset){
    if (util_mahosets == NULL) {
        printf("mahosets_register_data(): error: util_mahosets == NULL");
        return;
    }
    if (util_mahosets_num >= util_mahosets_capa) {
        int tmp_mahosets_capa = (util_mahosets_capa == 0 ? DEFAULT_MAHOSETS_CAPA: util_mahosets_capa * 2);
        mahoset_t *tmp_mahosets = realloc(util_mahosets, sizeof(mahoset_t) * tmp_mahosets_capa);
        if (tmp_mahosets == NULL) {
            printf("mahosets_register_data(): error: realloc() is failed.");
            return;
        }
        util_mahosets = tmp_mahosets;
        util_mahosets_capa = tmp_mahosets_capa;
    }
    // util_mahosets_print(mahoset, 1);
    memcpy(&util_mahosets[util_mahosets_num], mahoset, sizeof(mahoset_t));
    util_mahosets_num++;
    printf("made mahosets ... %d\n", util_mahosets_num);
}

//int g_cnt = 0;
void util_mahosets_make_r(mahoset_t *mahoset_buf, int curpos, int start_val) {
    if (curpos < N) {
        for (int i = start_val; i < util_numsets_num; i++) {
            memcpy(&(mahoset_buf->numsets[curpos]), &util_numsets[i], sizeof(numset_t));
            util_mahosets_make_r(mahoset_buf, curpos + 1, i + 1);
        }
    } else {
//        printf("\n", g_cnt++);
        int i;
        int check_table[MAX_NUM];
        memset(check_table, 0, sizeof(check_table));
        for (i = 0; i < N; i++) {
            for (int j = 0; j < N; j++) {
                check_table[mahoset_buf->numsets[i].data[j] - 1] = 1;
            }
        }
        for (i = 0; i < MAX_NUM; i++) {
            if (check_table[i] == 0) {
                // ※デバッグでチェックテーブルを表示したいときだけ有効化する
                // for (int j = 0; j < MAX_NUM;j++) printf("%d", check_table[j]);
                // printf("\n");
                break;
            }
        }
        if (i >= MAX_NUM) {
            util_mahosets_register_data(mahoset_buf);
        }
    }
}
void util_mahosets_make(void) {
    mahoset_t mahoset = {0};
    util_mahosets_make_r(&mahoset, 0, 0);
}

void util_mahosets_shuffle_and_derive_for_data(mahoset_t *mahoset, mahoset_t *mahoset_buf, int row_pos, int col_pos, int *used_idxes, int used_idxes_num) {
    if (row_pos < N) {
        if (col_pos < N) {
            for (int i = 0; i < N; i++) {
                int j;
                for (j = 0; j < used_idxes_num; j++) {
                    if (used_idxes[j] == i) {
                        break;
                    }
                }
                if (j < used_idxes_num) {
                    continue;
                }
                used_idxes[used_idxes_num] = i;
                mahoset_buf->numsets[row_pos].data[col_pos] = mahoset->numsets[row_pos].data[i];
                util_mahosets_shuffle_and_derive_for_data(mahoset, mahoset_buf, row_pos, col_pos + 1, used_idxes, used_idxes_num + 1);
            }
        } else {
            util_mahosets_shuffle_and_derive_for_data(mahoset, mahoset_buf, row_pos + 1, 0, used_idxes, 0);
        }
    } else {
        int i, j;
        int v_total[N];
        int x_total[2];
        memset(v_total, 0, sizeof(v_total));
        memset(x_total, 0, sizeof(x_total));        
        for (i = 0; i < N; i++) {
            for (j = 0; j < N; j++) {
                v_total[i] += mahoset_buf->numsets[j].data[i];
            }
            x_total[0] += mahoset_buf->numsets[i].data[i];
            x_total[1] += mahoset_buf->numsets[N-i-1].data[i];
        }
        if (x_total[0] != TOTAL_OF_LINE || x_total[1] != TOTAL_OF_LINE) {
            return;
        }
        for (i = 0; i < N; i++) {
            if (v_total[i] != TOTAL_OF_LINE) {
                return;
            }
        }
        created_mahozin_counter++;
        printf("*** Mahozin:%04d ***\n", created_mahozin_counter);
        util_mahosets_print(mahoset_buf, 1);
    }
}

void util_mahosets_shuffle_and_derive_for_numset(mahoset_t *mahoset, mahoset_t *mahoset_buf, int numset_pos, int *used_idxes, int used_idxes_num) {
    if (numset_pos < N) {
        for (int i = 0; i < N; i++) {
            int j;
            for (j = 0; j < used_idxes_num; j++) {
                if (used_idxes[j] == i) {
                    break;
                }
            }
            if (j < used_idxes_num) {
                continue;
            }
            used_idxes[used_idxes_num] = i;
            memcpy(&mahoset_buf->numsets[numset_pos], &mahoset->numsets[i], sizeof(numset_t));
            util_mahosets_shuffle_and_derive_for_numset(mahoset, mahoset_buf, numset_pos + 1, used_idxes, used_idxes_num + 1);
        }
    } else {
        mahoset_t mahoset_bufbuf = {0};
        int used_idxes_for_data[N];
        memset(used_idxes_for_data, 0, sizeof(used_idxes_for_data));
        util_mahosets_shuffle_and_derive_for_data(mahoset_buf, &mahoset_bufbuf, 0, 0, used_idxes_for_data, 0);
    }
}

void util_mahosets_shuffle_and_derive(void) {
    mahoset_t mahoset_buf = {0};
    int used_idxes[N];
    for (int i = 0; i <util_mahosets_num; i++) {
        memset(used_idxes, 0, sizeof(used_idxes));
        util_mahosets_shuffle_and_derive_for_numset(&util_mahosets[i], &mahoset_buf, 0, used_idxes, 0);
    }
}

int main() {
    printf("+++ mahozin +++: Creating %dx%d Mahozin.\n", N, N);
    util_init();
    // ①util_numsets_make: 行として合計値が正しい数値セットを作成する処理
    printf("+++ mahozin +++: making numsets.\n");
    util_numsets_make();
    printf("+++ mahozin +++: made %d numsets.\n", util_numsets_get_total_numsets());
    // util_numsets_printall();
    // ②util_mahosets_make: 上記①で抽出した数値セットを組み合わせて（縦や斜めの計算は一旦無視して）数値重複が無い魔法陣候補(NxN)を作成する処理
    printf("+++ mahozin +++: making mahosets.\n");
    util_mahosets_make();
    printf("+++ mahozin +++: made %d mahosets.\n", util_mahosets_get_total_mahosets());
    // util_mahosets_printall();
    // ③util_mahosets_shuffle_and_derive: 上記②の魔法陣候補群に対して、行ごとシャッフル、および行内シャッフルをおこない、それぞれで縦と斜めの合計値が正しいものを標準出力する処理。
    printf("+++ mahozin +++: shuffle mahosets and derive valid mahozin.\n");
    util_mahosets_shuffle_and_derive();
    util_deinit();
    printf("+++ mahozin +++: Created %d Mahozin.\n", util_mahosets_get_created_mahozin_counter());
    return 0;
}


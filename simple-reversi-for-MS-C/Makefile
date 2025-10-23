# Makefile for Simple Reversi (Windows)

# コンパイラとフラグ
CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c11
LDFLAGS = -lws2_32

# ターゲット実行ファイル
TARGET = reversi.exe

# ソースファイルとオブジェクトファイル
SOURCES = main.c reversi.c network.c
OBJECTS = $(SOURCES:.c=.o)
HEADERS = reversi.h network.h

# デフォルトターゲット
all: $(TARGET)

# 実行ファイルのビルド
$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -o $(TARGET) $(LDFLAGS)
	@echo "ビルド完了: $(TARGET)"

# オブジェクトファイルのビルド
%.o: %.c $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@

# クリーンアップ
clean:
	del /Q $(OBJECTS) $(TARGET) 2>nul || echo "Already clean"

# 再ビルド
rebuild: clean all

# 実行（サーバーモード）
run-server: $(TARGET)
	./$(TARGET)

# 実行（クライアントモード）
run-client: $(TARGET)
	./$(TARGET)

.PHONY: all clean rebuild run-server run-client

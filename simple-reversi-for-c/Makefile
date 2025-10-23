CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O2
TARGET = reversi
SOURCES = main.c reversi.c network.c
HEADERS = reversi.h network.h
OBJECTS = $(SOURCES:.c=.o)

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJECTS)

%.o: %.c $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET)

run-server: $(TARGET)
	./$(TARGET) server 8888

run-client: $(TARGET)
	./$(TARGET) client 127.0.0.1 8888

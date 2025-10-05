CC = gcc
CFLAGS = -Wall -Wextra -std=c11
TARGET = mahozin

all: $(TARGET)

$(TARGET): mahozin.c
	$(CC) $(CFLAGS) -o $(TARGET) mahozin.c

clean:
	rm -f $(TARGET)

run: $(TARGET)
	./$(TARGET)

.PHONY: all clean run

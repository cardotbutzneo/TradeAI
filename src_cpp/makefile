# Variables
CC = g++
CFLAGS = -Wall -Wextra -Werror -Iinclude -std=c++17
SRC_DIR = src
OBJ_DIR = obj
INC_DIR = include

# Détection automatique des fichiers
SRCS = $(wildcard $(SRC_DIR)/*.cpp)
OBJS = $(patsubst $(SRC_DIR)/%.cpp,$(OBJ_DIR)/%.o,$(SRCS))
DEPS = $(wildcard $(INC_DIR)/*.h)
TARGET = main

# Règles
all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

# Chaque .o dépend de son .cpp et des .h
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp $(DEPS) | $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Création du dossier obj s'il n'existe pas
$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

clean:
	rm -rf $(OBJ_DIR) $(TARGET)
	> bourse.log

.PHONY: all clean
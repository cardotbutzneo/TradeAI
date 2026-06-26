#ifndef PARSER_H
#define PARSER_H

#include "main.h"

#include "bourse.h"

FinancialNDArray *read_file(char *filename, char *separators, IndexMap *index_actions, IndexMap *index_dates, int *nb_actions, int *nb_dates);
int obtenir_index(IndexMap *table, int *taille_actuelle, char *texte);

#endif
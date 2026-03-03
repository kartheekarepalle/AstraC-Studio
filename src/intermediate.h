#ifndef INTERMEDIATE_H
#define INTERMEDIATE_H

#define MAX_TAC 1024

extern char tac[MAX_TAC][100];
extern int tac_count;
extern int temp_counter;
extern int label_counter;

char* new_temp();
char* new_label();
void add_tac(const char *code);
void generateIR();

#endif // INTERMEDIATE_H

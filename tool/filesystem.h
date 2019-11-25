#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include <string.h>
#include <malloc.h>

#ifndef _UINT
    #define _UINT(in,position) *((uint32_t*)&in[position])
#endif

typedef struct entry
{
	uint32_t name_len;
    uint8_t *name;
    uint32_t start_pos;
    uint32_t size;
} entry;

typedef struct table
{
	uint8_t keyval;
	uint32_t size;
	entry* entries;
} table;

// loads and unpacks filesystem
uint32_t unpack_fs(uint8_t *fcontent, long fsize, uint8_t unpack);
long decode(uint8_t *data, long pos, const long size, uint8_t *key);
long load_entry_encoded(uint8_t* data, entry* eentry, uint8_t* key);

long load_entry_raw(uint8_t* data, entry* eentry);
table load_fs_table(uint8_t* data);

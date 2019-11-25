#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>

#ifndef _LZW_
#define _LZW_

/* ----------- LZW stuff -------------- */
typedef uint8_t byte;
typedef uint16_t ushort;

#define MAX_BITS 16
#define START_BITS 9

#define M_CLR 258 /* 258 clear table marker */
#define M_EXD 257 /* 257 extend table marker */
#define M_EOD 256 /* 256 end-of-data marker */
#define M_NEW 259 /* 259 new code index marker */
#define SHIFT 512 /* 512 by default */

/* encode and decode dictionary structures.
   for encoding, entry at code index is a list of indices that follow current one,
   i.e. if code 97 is 'a', code 387 is 'ab', and code 1022 is 'abc',
   then dict[97].next['b'] = 387, dict[387].next['c'] = 1022, etc. */
typedef struct {
  ushort next[256];
} lzw_enc_t;

/* for decoding, dictionary contains index of whatever prefix index plus trailing
   byte.  i.e. like previous example,
    dict[1022] = { c: 'c', prev: 387 },
    dict[387]  = { c: 'b', prev: 97 },
    dict[97]   = { c: 'a', prev: 0 }
   the "back" element is used for temporarily chaining indices when resolving
   a code to bytes
 */
typedef struct {
  uint32_t prev, back;
  byte c;
} lzw_dec_t;

/* -------- aux stuff ---------- */
void* mem_alloc(size_t item_size, size_t n_item);
void* mem_extend(void *m, size_t new_n);
void _clear(void *m);

#define _new(type, n) mem_alloc(sizeof(type), n)
#define _del(m)   { free((size_t*)(m) - 2); m = 0; }
#define _len(m)   *((size_t*)m - 1)
#define _setsize(m, n)  m = mem_extend(m, n)
#define _extend(m)  m = mem_extend(m, _len(m) * 2)


byte* lzw_decode(byte *in, int32_t in_len);

#endif

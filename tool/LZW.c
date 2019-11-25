#include "LZW.h"

/* -------- aux stuff ---------- */
void* mem_alloc(size_t item_size, size_t n_item)
{
  size_t *x = calloc(1, sizeof(size_t)*2 + n_item * item_size);
  x[0] = item_size;
  x[1] = n_item;
  return x + 2;
}

void* mem_extend(void *m, size_t new_n)
{
  size_t *x = (size_t*)m - 2;
  x = realloc(x, sizeof(size_t) * 2 + *x * new_n);
  if (new_n > x[1])
    memset((char*)(x + 2) + x[0] * x[1], 0, x[0] * (new_n - x[1]));
  x[1] = new_n;
  return x + 2;
}

void _clear(void *m)
{
  size_t *x = (size_t*)m - 2;
  memset(m, 0, x[0] * x[1]);
}


 void print_dict(lzw_dec_t *d)
{
	size_t j, len = _len(d);
	for (j = 0; j < len; j++)
	{
		if(d[j].prev)
		printf("%d prev: %hu back: %hu, byte: %hhu %c\n",	d[j].prev, d[j].back, d[j].c, d[j].c);
	}

}

byte* lzw_encode(byte *in, int max_bits)
{
  int len = _len(in), bits = START_BITS, next_shift = SHIFT;
  ushort code, c, nc, next_code = M_NEW;
  lzw_enc_t *d = _new(lzw_enc_t, SHIFT);

  if (max_bits > 15) max_bits = 15;
  if (max_bits < START_BITS ) max_bits = 12;

  byte *out = _new(ushort, 4);
  int out_len = 0, o_bits = 0;
  uint32_t tmp = 0;

  inline void write_bits(ushort x) {
    tmp = (tmp << bits) | x;
    o_bits += bits;
    if (_len(out) <= out_len) _extend(out);
    while (o_bits >= 8) {
      o_bits -= 8;
      out[out_len++] = tmp >> o_bits;
      tmp &= (1 << o_bits) - 1;
    }
  }

  //write_bits(M_CLR);
  for (code = *(in++); --len; ) {
    c = *(in++);
    if ((nc = d[code].next[c]))
      code = nc;
    else {
      write_bits(code);
      nc = d[code].next[c] = next_code++;
      code = c;
    }

    /* next new code would be too long for current table */
    if (next_code == next_shift) {
      /* either reset table back to 9 bits */
      if (++bits > max_bits) {
        /* table clear marker must occur before bit reset */
        write_bits(M_CLR);

        bits = START_BITS;
        next_shift = SHIFT;
        next_code = M_NEW;
        _clear(d);
      } else  /* or extend table */
        _setsize(d, next_shift *= 2);
    }
  }

  write_bits(code);
  write_bits(M_EOD);
  if (tmp) write_bits(tmp);

  _del(d);

  _setsize(out, out_len);
  return out;
}
 /////////////////////////////////////////////////////////////////////////////////////////////
byte* lzw_decode(byte *in, int32_t in_len)
{
  byte *out = _new(byte, 4);
  int out_len = 0;
  if (in_len < 0)
    in_len = _len(in);

  inline void write_out(byte c)
  {
    while (out_len >= _len(out)) _extend(out);
    out[out_len++] = c;
  }

  lzw_dec_t *d = _new(lzw_dec_t, SHIFT);
  int len, j, next_shift = SHIFT, bits = START_BITS, n_bits = 0;
  uint32_t code, c, t, next_code = M_NEW;

  uint32_t tmp = 0;
  inline void get_code() {
    while(n_bits < bits) {
      if (len > 0) {
        len --;
        tmp = (tmp << 8) | *(in++);
        n_bits += 8;
      } else {
        tmp = tmp << (bits - n_bits);
        n_bits = bits;
      }
    }
    n_bits -= bits;
    code = tmp >> n_bits;
	//printf("Code9:%hu code:%hu\n", tmp >> 9, code);
    tmp &= (1 << n_bits) - 1;
  }

  inline void clear_table() {
    _clear(d);
    for (j = 0; j < 256; j++) d[j].c = j;
    next_code = M_NEW;
    next_shift = SHIFT;
    bits = START_BITS;
  };

  inline void extend_table() {
    if (++bits > MAX_BITS) {
        /* if input was correct, we'd have hit M_CLR before this */
        fprintf(stderr, "Too many bits\n");
      }
      printf("Extending bits to: %d\n", bits);
      _setsize(d, (next_shift *= 2));
  };

  //MAIN LOOP
  clear_table(); /* in case encoded bits didn't start with M_CLR */
  for (len = in_len; len;) {
    get_code();

    if (code == M_EOD) { printf("DATA OK %d\n", out_len); break;}
    if (code == M_EXD) {
	  extend_table();
      continue;
    }
    if(code == M_CLR){
        clear_table();
        continue;
    }
    if (code >= next_code) {
      fprintf(stderr, "Bad sequence at: %d. Code: %hu next code: %hu.\n",
              in_len - len, code, next_code);
      //_del(out);
      goto bail;
    }

    d[next_code].prev = c = code;
    while (c > 255) {
      t = d[c].prev;
	  d[t].back = c;
	  c = t;
    }

    d[next_code - 1].c = c;

    while (d[c].back) {
      write_out(d[c].c);
      t = d[c].back; d[c].back = 0; c = t;
    }
    write_out(d[c].c);

    ++next_code;
  }

  /* might be ok, so just whine, don't be drastic */
  if (code != M_EOD) fputs("Bits did not end in EOD\n", stderr);

bail:
  _setsize(out, out_len);
  //print_dict(d);
  _del(d);

  return out;
}


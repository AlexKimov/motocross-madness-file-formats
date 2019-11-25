#include "image.h"
#include <malloc.h>
#include "filesystem.h"

int main(int argc, char* argv[])
{
  int fd;
  if(argc < 3)
  {
      printf("MCM2 files tool.\nUsage: <action flag> <input filename>\nFlags: e - extract archive, l - only list archive files, c - convert TGA image into BMP\n");
      return 0;
  }

  fd = open(argv[2], O_RDONLY);
  if (fd == -1) {
    fprintf(stderr, "Can't read file: %s\n", argv[2]);
    return 1;
  };

  struct stat st;
  fstat(fd, &st);

  byte *out, *in = _new(char, st.st_size);
  read(fd, in, st.st_size);
  _setsize(in, st.st_size);
  close(fd);

  printf("input size:  %zd\n", _len(in));

  //archive stuff
  if(argv[1][0] == 'e' || argv[1][0] == 'l')
  {
      unpack_fs(in, _len(in), argv[1][0] == 'l' ? 0:1);
     _del(in);
  }
  // conversion stuff
  else
  {
      size_t out_len = load_image(in, &out);
      _del(in);
      if(!out_len)
      {
        fprintf(stderr, "Error during conversion\n");
        return 1;
      }
      //write decoded
      char *out_filename = _new(char,strlen(argv[2])+1);
      strcpy(out_filename, argv[2]);
      strcpy(&out_filename[strlen(out_filename)-3], "bmp");
      fd = open(out_filename, O_RDWR | O_CREAT, 0666);
      if (fd == -1) {
        fprintf(stderr, "Can't write file\n");
      }
      else
      {
          write(fd, out, out_len);
          printf("Written %zd bytes.\n", out_len);
          close(fd);
      }
      _del(out_filename);
      _del(out);
  }
  return 0;
}

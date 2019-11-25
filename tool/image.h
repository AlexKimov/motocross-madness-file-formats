#include "LZW.h"

#define DEBUG

#define _UINT(in,position) *((uint32_t*)&in[position])

size_t load_image(byte *in, byte** out);

size_t to_bmp(byte* in, byte** out,size_t, size_t, uint8_t deepth, uint8_t pixel_format);

#pragma pack(push, 1)

typedef struct {
    unsigned short type;                 /* Magic identifier            */
    unsigned int size;                       /* File size in bytes          */
    unsigned int reserved;
    unsigned int offset;                     /* Offset to image data, bytes */
} BMPHEADER;

typedef struct {
    unsigned int size;               /* Header size in bytes      */
    int width,height;                /* Width and height of image */
    unsigned short planes;       /* Number of colour planes   */
    unsigned short bits;         /* Bits per pixel            */
    unsigned int compression;        /* Compression type          */
    unsigned int imagesize;          /* Image size in bytes       */
    int xresolution,yresolution;     /* Pixels per meter          */
    unsigned int ncolours;           /* Number of colours         */
    unsigned int importantcolours;   /* Important colours         */
    //additional for 16 bit bitmaps
    unsigned int colorsMask[4];     /* Typically rgba    */
    unsigned int colorsSpaceType;
    unsigned char others[64];
} BMPINFOHEADER;

typedef struct {
    unsigned char r,g,b;
} BMPCOLOURINDEX;

#pragma pack(pop)

void reverse_array(byte arr[], size_t);

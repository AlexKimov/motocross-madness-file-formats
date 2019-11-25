#include "image.h"

size_t load_image(byte *in, byte** out)
{
    size_t input_len =  _len(in);
    size_t position = 8, data_len;
    uint32_t kind = *in;
    uint32_t width, height, tmp;
    uint8_t bits_pp, pformat;
    char* palette_filename;
    byte *encoded_data, *decoded_data;
    width = _UINT(in,position);
    position += 4;
    height = _UINT(in,position);
    position += 4;

    //string len
    tmp = _UINT(in,position);
    position += 4;
    palette_filename = (char*)&in[position];
    position += tmp;

    // 0x7 is 16 bit, 0x9 is 24 bit
    bits_pp = 24;
    pformat = 0;
    if(kind == 0xF || kind == 0x16)
    {
        bits_pp = 16;
    }
    else if(kind == 0x7 || kind == 0xB || kind == 0x1A)
    {
        // RGBA 4444
        bits_pp = 16;
        pformat = 4;
    }

    if(kind != 0x0B)
    { 
        if (width == 256)
        {
            position += 4*8;
            tmp = _UINT(in,position);
            position += tmp;
        }
        else if (width == 128)
        {
            position += 4*7;
            tmp = _UINT(in,position);
            position += tmp;
        }
        else
        {
            position += 4*6;
            tmp = _UINT(in,position);
            position += tmp;
        }
    }

    //read amount of data encoded
    tmp = _UINT(in,position);
    position += 4;
    tmp -= 4;

    encoded_data = &in[position];
    printf("Palette: %s byte: %hhu\n", palette_filename, encoded_data[0]);

    size_t expected_len = width*height*bits_pp/8+1;
    decoded_data = lzw_decode(encoded_data, tmp);
    if(_len(decoded_data) != expected_len)
    {
        printf("Decoded size: %zd expected size: %zd\n",
               _len(decoded_data), expected_len);
        #ifdef DEBUG
        int fd = open("decompressed.bin", O_WRONLY | O_CREAT, 0666);
        write(fd, decoded_data, _len(decoded_data));
        close(fd);
        #else
        return 0;
        #endif // DEBUG
    }

    data_len = to_bmp(decoded_data, out, width, height, bits_pp, pformat);
    _del(decoded_data);
    return data_len;
}

size_t to_bmp(byte* in, byte** out, size_t width, size_t height, uint8_t bits, uint8_t pixel_format)
{
    uint8_t offset = sizeof(BMPHEADER)+sizeof(BMPINFOHEADER);
    size_t bytes_per_line = width*(bits/8);
    uint8_t padding = 4 - (bytes_per_line % 4);
    if( padding == 4) padding = 0;
    size_t data_size = bytes_per_line*height + (height*padding);
    size_t file_size = data_size+offset;


    *out = _new(byte,file_size+256);

    BMPHEADER *hdr = (BMPHEADER*)*out;
    BMPINFOHEADER *hdrinfo = (BMPINFOHEADER*)&(*out)[14];
    hdr->type = 0x4d42;
    hdr->offset = offset;
    hdr->reserved = 0x00;

    hdrinfo->size = sizeof(BMPINFOHEADER);
    hdrinfo->width = width;
    hdrinfo->height = height;
    hdrinfo->planes = 1;
    hdrinfo->bits = bits;
    hdrinfo->compression = bits == 16 ? 0x3: 0x0;
    hdrinfo->imagesize = file_size;
    hdrinfo->xresolution = 0;
    hdrinfo->yresolution = 0;
    hdrinfo->ncolours = 0;
    hdrinfo->importantcolours = 0;
    hdrinfo->colorsMask[0] = 0x7c00;
    hdrinfo->colorsMask[1] = 0x3e0;
    hdrinfo->colorsMask[2] = 0x1f;
    hdrinfo->colorsMask[3] = 0x0;
    if (pixel_format == 4)
    {
        hdrinfo->colorsMask[0] = 0xf00;
        hdrinfo->colorsMask[1] = 0xf0;
        hdrinfo->colorsMask[2] = 0xf;
        hdrinfo->colorsMask[3] = 0xf000;
    }

    hdrinfo->colorsSpaceType = 0x73524742;

    hdr->size = file_size;

    size_t line, row;

    if(bits == 8)
    {
        uint8_t* clr_in = (uint8_t*)in;
        uint8_t *clr_out = (uint8_t*)&(*out)[offset];
        clr_in += (width*height-width);
        for(line = 0; line <height; ++line)
        {
           for(row = 0; row < width; ++row)
           {
               *clr_out = *clr_in; ++clr_in;
               ++clr_out;
           }
           uint8_t* pad = (uint8_t*)clr_out;
           uint8_t i;
           for(i=0; i < padding; ++i, ++pad)
              *pad = 0x00;
           clr_out = (uint8_t*) pad;
           clr_in -= width*2*sizeof(uint8_t);
        }
    }
    else if(bits == 16)
    {
        uint16_t* clr_in = (uint16_t*)in;
        uint16_t *clr_out = (uint16_t*)&(*out)[offset];
        clr_in += (width*height-width);
        for(line = 0; line <height; ++line)
        {
           for(row = 0; row < width; ++row)
           {
               *clr_out = *clr_in;
               ++clr_in;
               ++clr_out;
           }
           uint8_t* pad = (uint8_t*)clr_out;
           uint8_t i;
           for(i=0; i < padding; ++i, ++pad)
              *pad = 0x00;
           clr_out = (uint16_t*) pad;
           clr_in -= width*2;
        }
    }
    else
    {
        uint8_t* clr_in = (uint8_t*)in;
        BMPCOLOURINDEX *clr_out = (BMPCOLOURINDEX*)&(*out)[offset];
        clr_in += (width*height-width)*3;
        for(line = 0; line <height; ++line)
        {
           for(row = 0; row < width; ++row)
           {
               clr_out->b = *clr_in; ++clr_in;
               clr_out->g = *clr_in; ++clr_in;
               clr_out->r = *clr_in; ++clr_in;
               ++clr_out;
           }
           uint8_t* pad = (uint8_t*)clr_out;
           uint8_t i;
           for(i=0; i < padding; ++i, ++pad)
              *pad = 0x00;
           clr_out = (BMPCOLOURINDEX*) pad;
           clr_in -= width*2*sizeof(BMPCOLOURINDEX);
        }
    }
    return file_size;
}

void reverse_array(byte arr[], size_t size)
{
    int i;
    for (i = 0; i < size/2; ++i)
    {
        int temp = arr[i];
        arr[i] = arr[size - 1 - i];
        arr[size - 1 - i] = temp;
    }
}

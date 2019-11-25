#include "filesystem.h"

long decode(uint8_t *data, long pos, const long size, uint8_t *key)
{
   long end;
   uint8_t next_key;
   //key = 0x80;
   for(end=pos+size; pos < end; ++pos)
   {
      next_key = data[pos] + *key;
      data[pos] = data[pos] ^*key;
      *key = next_key;
   }
   return size;
}

long load_entry_encoded(uint8_t* data, entry* eentry, uint8_t* key)
{
	long pos = 0;
	//load number of chars in name
	pos += decode(data, pos, 4, key);
	eentry->name_len = *((uint32_t*)data);

	//decode name string
	eentry->name = &data[pos];
	pos += decode(data, pos, eentry->name_len, key);
	// get start pos of file chunk
	decode(data, pos, 4, key);
	eentry->start_pos = _UINT(data, pos);
	pos += 4;
	// get file size
	decode(data, pos, 4, key);
	eentry->size = _UINT(data, pos);
	pos += 4;
	return pos;
}

long load_entry_raw(uint8_t* data, entry* eentry)
{
	long pos = 4;
	eentry->name_len = *((uint32_t*)data);
	//name string
	eentry->name = &data[pos];
	pos += eentry->name_len;
	// get start pos of file chunk
	eentry->start_pos = _UINT(data, pos);
	pos += 4;
	// get file size
	eentry->size = _UINT(data, pos);
	pos += 4;
	return pos;
}

table load_fs_table(uint8_t* data)
{
	uint32_t files_count, i;
	entry* fs_entries;
	table tbl; //result
	uint8_t key;
	// start decoding from 4th byte
	long position = 4;
	// read 8 bytes at beginning
	long to_read = 8;

	// check whether file is encrypted or not
	if(*((uint32_t*)data) == 0x454F4146) // faoe
	{
		// figure out key value for decryption
		key = data[4] ^ 0x52; // R
		tbl.keyval = key;

		//load number of files in virtual file system
		decode(data, position, to_read, &key);
		files_count = _UINT(data, 8);
		position += to_read;
		//printf("%s\n", data);
		//allocate memory for fs table
		fs_entries = (entry*) malloc(files_count*sizeof(entry));
		for(i = 0; i < files_count; ++i)
		{
			position += load_entry_encoded(&data[position], &fs_entries[i], &key);
		}
	}
	else // try read decrypted
	{
		if(*((uint32_t*)data) == 0x00325352) // rs2
		{
			tbl.keyval = 0;
			//load number of files in virtual file system
			files_count = _UINT(data, 4);
			position = to_read;
			//allocate memory for fs table
			fs_entries = (entry*) malloc(files_count*sizeof(entry));
			for(i = 0; i < files_count; ++i)
			{
				position += load_entry_raw(&data[position], &fs_entries[i]);
			}
		}
		else // non valid file
		{
			tbl.entries = NULL;
			return tbl;
		}
	}
	tbl.size = files_count;
	tbl.entries = fs_entries;
	return tbl;
}

uint32_t unpack_fs(uint8_t *fcontent, long fsize, uint8_t unpack)
{
	FILE *f;
	table fs_table;
	//lazy static buffer
	uint8_t name_buff[256];
	uint32_t i;

	fs_table = load_fs_table(fcontent);
	if(!fs_table.entries)
	{
		printf("%s", "This is probably not a valid file from MCM2 archive.");
		return 0;
	}
	printf("Packed files: %u\n", fs_table.size);
	for(i = 0; i < fs_table.size; ++i)
	{
		entry ent = fs_table.entries[i];
		uint8_t key = fs_table.keyval;
		uint32_t position = ent.start_pos;
		uint32_t to_read = ent.size;
		strcpy(name_buff, "OUTPUT/");
		strcat(name_buff,  ent.name);
		printf("File %u: %s\n", i+1, ent.name);

		// list fs content only
		if(!unpack)
			continue;

		if(key)
		{
			// entries in fs_table are offset 4 bytes from file origin
			position += 4;
			// decode file
			decode(fcontent, position, to_read, &key);
		}
		// dump file
		f = fopen(name_buff, "wb");
		if(!f)
		{
			printf("Failed to open file: %s for writing!\n", name_buff);
			continue;
		}
		fwrite(&fcontent[position], to_read, 1, f);
		fclose(f);
	}
	free(fs_table.entries);
	return i;
}

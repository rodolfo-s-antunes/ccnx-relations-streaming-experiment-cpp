/**
 * @file Buffer.c
 */

#include <iostream>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <atomic>
#include <condition_variable>
#include "MetaBuffer.h"

using namespace std;

/**
 * Buffer constructor
 * 
 * @param bufid buffer identifier 
 * @param maxsize buffer's maximum size
 */
MetaBuffer::MetaBuffer()
{
	currentsize = 0;
	metabuffer = NULL;
}

/**
 * Gets buffer size
 *
 * @return currentsize buffer size
 */
unsigned int MetaBuffer::size()
{
	return currentsize;
}

/**
 * Appends data to the buffer
 *
 * @param size size of additional data
 * @param data data to be inserted
 */
void MetaBuffer::insertData(unsigned int size, char* data)
{
	unsigned int newsize = currentsize + size;
	if (currentsize > 0) metabuffer = (char*)realloc(metabuffer, sizeof(char)*newsize);
	else metabuffer = (char*)malloc(sizeof(char)*size);
	memcpy(metabuffer+currentsize,data,size);
	currentsize = newsize;
}

/**
 * Gets a pointer to the buffer's first element
 *
 * @return buffer pointer to the first element of the buffer array
 */
char* MetaBuffer::getDataPointer()
{
	return metabuffer;
}

/**
 * Clears buffer
 */
void MetaBuffer::clearMetaBuffer()
{
	currentsize = 0;
	free(metabuffer);
	metabuffer = NULL;
}


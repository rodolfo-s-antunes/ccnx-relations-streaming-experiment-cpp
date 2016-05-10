/**
 * @file Buffer.c
 */

#include <iostream>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <atomic>
#include <condition_variable>
#include <time.h>
#include "Buffer.h"

using namespace std;

/**
 * Buffer constructor
 * 
 * @param bufid buffer identifier 
 * @param maxsize buffer's maximum size
 */
Buffer::Buffer(string bufid, unsigned int maxsize, unsigned int pblocksize)
{
	currentsize = 0;
	threshold = maxsize;
	buffer = NULL;
	blocksize = pblocksize;
	isempty = true;
	beginning = true;
	//isfull = false;
	id = bufid;
	producing = false;
	finished = false;
}

/**
 * Gets buffer size
 *
 * @return currentsize buffer size
 */
unsigned int Buffer::size()
{
	return currentsize;
}

/**
 * Appends data to the buffer
 *
 * @param size size of additional data
 * @param data data to be inserted
 */
void Buffer::insertData(unsigned int size, char* data)	
{
	unique_lock<mutex> lock(mtxcond);
	if (size == 0) {
		producing = false;
		notempty.notify_all();
		return;
	}
	else 
	{
		//if (isfull)
		//{
		//	notfull.wait(lock);
		//}
		mtx.lock();
		int newsize = currentsize + size;
		if (!isempty) buffer = (char*)realloc(buffer, sizeof(char)*newsize);
		else buffer = (char*)malloc(sizeof(char)*size);
		memcpy(buffer+currentsize,data,size); 
		currentsize = newsize;
		if (isempty) isempty=false;
		if (currentsize >= threshold) 
		{
			//isfull = true;
			notempty.notify_all();
		}
		mtx.unlock();
	}
}

/**
 * Pops a given quantity of data from the buffer
 *
 * @param size size of the data to pop
 */
void Buffer::popDataChunk(unsigned int size)
{
	unique_lock<mutex> lock(mtxcond);
	timespec bts, ets;
	double bmsec, emsec, dmsec;

	if (isempty || beginning)
	{
		if (!producing)
		{
			finished = true;
			return;
		}
		printf("%s: Buffer is empty! Awaiting for it to fill!\n", id.c_str());
		notfull.notify_all();
		clock_gettime(CLOCK_MONOTONIC, &bts);
		notempty.wait(lock);
		clock_gettime(CLOCK_MONOTONIC, &ets);
		bmsec = ((double)(long)bts.tv_sec)*1000. + ((double)(long)bts.tv_nsec)/1000000.;
		emsec = ((double)(long)ets.tv_sec)*1000. + ((double)(long)ets.tv_nsec)/1000000.;
		dmsec = emsec-bmsec;
		printf("%s: Buffer filled! Lock released.\n", id.c_str());
		printf("%s: Waiting time until filled: %f ms.\n", id.c_str(), dmsec);
		if (beginning) beginning = false;
	}

	mtx.lock();
	int newsize = currentsize - size;
	if (newsize <= 0)
	{
		clearBuffer();
		isempty = true;
	}
	else
	{
		memmove(buffer, buffer+size, newsize);
		buffer = (char*)realloc(buffer, sizeof(char)*newsize);
		currentsize = newsize;
	}
	//if (newsize >= 0 && threshold - newsize >= blocksize)
	//{
	//	isfull = false;
	//	notfull.notify_all();
	//}
	mtx.unlock();
}

/**
 * Gets a copy of buffer data
 *
 * @return result copy of buffer data
 */
char* Buffer::getDataCopy()
{
	char *result = (char*)malloc(sizeof(char)*currentsize);
	memcpy(result,buffer,currentsize);
	return result;
}

/**
 * Gets a pointer to the buffer's first element
 *
 * @return buffer pointer to the first element of the buffer array
 */
char* Buffer::getDataPointer()
{
	return buffer;
}

/**
 * Clears buffer
 */
void Buffer::clearBuffer()
{
	currentsize = 0;
	free(buffer);
	buffer = NULL;
}

/**
 * Clears buffer if it is full
 */
void Buffer::clearBufferIfFull()
{
	if ((threshold > 0) && (currentsize >= threshold))
		clearBuffer();
}

/*
void Buffer::insertData(size_t size, const unsigned char *data)
{
	unique_lock<mutex> lock(mtx);
	unsigned int newsize = currentsize + size;
	while (isfull)
	{
		notfull.wait(lock); //pega lock
	}
	if (!isempty) buffer = (char*)realloc(buffer, sizeof(char)*newsize);
	else buffer = (char*)malloc(sizeof(char)*size);
	memcpy(buffer+currentsize,data,size);
	currentsize = newsize;
	if (isempty) isempty = false;
	if (newsize == threshold) isfull = true;
	notempty.notify_all(); //signal notempty, libera lock
}
 */

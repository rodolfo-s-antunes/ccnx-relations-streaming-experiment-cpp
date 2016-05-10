/* 
 * @file Buffer.h
 */

#ifndef BUFFER_H_
#define BUFFER_H_

#include <string>
#include <mutex>
#include <atomic>
#include <condition_variable>

using namespace std;

class Buffer
{
	char* buffer;
	string id;
	unsigned int currentsize, blocksize;
	unsigned int threshold;
	mutex mtxcond, mtx;
	condition_variable notfull, notempty;
public:
	Buffer(string bufid, unsigned int maxsize, unsigned int pblocksize);
	bool beginning, isempty, producing, finished; //isfull,
	void insertData(unsigned int size, char* data);
	//void insertData(size_t size, const unsigned char *data);
	void popDataChunk(unsigned int size);
	char* getDataCopy();
	char* getDataPointer();
	unsigned int size();
	void clearBufferIfFull();
	void clearBuffer();
};

#endif /* BUFFER_H_ */

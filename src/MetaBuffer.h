/* 
 * @file Buffer.h
 */

#ifndef METABUFFER_H_
#define METABUFFER_H_

#include <string>

using namespace std;

class MetaBuffer
{
	char* metabuffer;
	unsigned int currentsize;
public:
	MetaBuffer();
	void insertData(unsigned int size, char* data);
	char* getDataPointer();
	unsigned int size();
	void clearMetaBuffer();
};

#endif /* METABUFFER_H_ */


//void insertData(size_t size, const unsigned char *data);

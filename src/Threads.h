/* 
 * @file Threads.h
 */

#ifndef THREADS_H
#define	THREADS_H

#include <string>
#include <thread>
#include "CCNComm.h"

using namespace std;

class StreamThreads
{
    string objname, id;
    Buffer *buf;
    int pipeline, blocksize, streamrate;
    unsigned long stepmicros;
    thread *producer;
    thread *consumer;
    CCNGet *ccnget;
    static void doDownload(string id, Buffer *buf, int blocksize, CCNGet *ccnget);
    static void consumeDownload(string id, Buffer *buf, int streamrate);
public:
    StreamThreads(string pid, string pobjname, unsigned int pbuffersize, unsigned int ppipeline, unsigned int pblocksize, unsigned int pstreamrate);
    bool createThreads();
    void waitForThreads();
};

#endif	/* THREADS_H */


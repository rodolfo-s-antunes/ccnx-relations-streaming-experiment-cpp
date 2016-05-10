/**
 * @file Threads.cpp
 */

#include <cstdio>
#include <iostream>
#include <string>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <time.h>
#include "Buffer.h"
#include "CCNComm.h"
#include "Threads.h"
#include <unistd.h>

 /**
 * Constructor for a download thread
 *
 * @param pid id of the object to download
 * @param pobjname name of the object to download
 * @param pbuffersize size of download buffer
 * @param ppipeline number of parallel requisitions for chunks
 * @param pblocksize size of each read block
 */
StreamThreads::StreamThreads(string pid, string pobjname, unsigned int pbuffersize, unsigned int ppipeline, unsigned int pblocksize, unsigned int pstreamrate)
{
	id = pid;
    objname = pobjname;
    buf = new Buffer(pid, pbuffersize, pblocksize);
    pipeline = ppipeline;
    blocksize = pblocksize;
    streamrate = pstreamrate;
    stepmicros = 0;
    producer = NULL;
    consumer = NULL;
    ccnget = NULL;
}

 /**
 * Downloads the required data (produces content to be consumed)
 *
 * @param id id of the object to download
 * @param buf buffer into which insert data
 * @param blocksize size os each read block
 * @param *ccnget pointer to a ccnget object which fetchs data from ccn
 */
void StreamThreads::doDownload(string id, Buffer *buf, int blocksize, CCNGet *ccnget) {
    int res;
    double tempdowntime;
    double downloadtime = 0;
    buf->producing = true;
    while ((res = ccnget->getBytes(buf, blocksize, &tempdowntime)) != 0) {
    	downloadtime += tempdowntime;
        if (res < 0) {
            printf("%s: Download FAILED!\n", id.c_str());
        }
    }
    if (res == 0) 
    {
        buf->insertData(res, NULL);
        printf("%s: Producer finished!\n", id.c_str());
        printf("%s: Download Success!\n", id.c_str());
        printf("%s: Download Time: %.2f ms\n", id.c_str(), downloadtime);
    }
}

 /**
 * Consumes the produced data
 *
 * @param id id of the object to download
 * @param buffer from which to remove data
 * @param streamrate rate at which data is consumed
 */
void StreamThreads::consumeDownload(string id, Buffer *buf, int streamrate) {
    timespec bts, ets;
    double bmsec, emsec, dmsec;
    double sec = 1000000000;
    while (!buf->finished)
    {
        clock_gettime(CLOCK_REALTIME, &bts);
        buf->popDataChunk(streamrate); 
        clock_gettime(CLOCK_REALTIME, &ets);  
        bmsec = ((double)(long)bts.tv_sec)*1000. + ((double)(long)bts.tv_nsec)/1000000.;
        emsec = ((double)(long)ets.tv_sec)*1000. + ((double)(long)ets.tv_nsec)/1000000.;
        dmsec = emsec-bmsec;
        if (dmsec < sec) usleep((sec-dmsec)/1000);
    }
    printf("%s: Consumer finished!\n", id.c_str());
    printf("%s: Streaming Success!\n", id.c_str());
}

 /**
 * Creates a thread for download
 * 
 * @return true if thread successfully created, false otherwise
 */
bool StreamThreads::createThreads() {
    ccnget = new CCNGet;
    if (!ccnget->initStream(objname, objname, pipeline)) {
        printf("%s: initStream FAILED!!\n", id.c_str());
        return false;
    }
    buf->producing = true;
    producer = new thread(doDownload,id,buf,blocksize,ccnget);
    consumer = new thread(consumeDownload, id, buf, streamrate);
    return true;
}

 /**
 * Waits for thread to end
 */
void StreamThreads::waitForThreads()
{
    producer->join();
    consumer->join();
}

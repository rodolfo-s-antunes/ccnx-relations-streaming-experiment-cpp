/* 
 * @file Windowing.h
 */
/*
#ifndef WINDOWING_H_
#define WINDOWING_H_

#include <string>
#include <queue>

#include "Buffer.h"

extern "C" {
#include <ccn/ccn.h>
#include <ccn/charbuf.h>
#include <ccn/uri.h>
#include <ccn/fetch.h>
#include <ccn/schedule.h>
#include <ccn/header.h>
}

using namespace std;

class CCNPipeline;

class CCNGetChunk
{
private:
	struct ccn *ccn;
	struct ccn_charbuf *name;
	struct ccn_closure *closure;
	CCNPipeline *ccnp;
	static enum ccn_upcall_res incomingData(
			struct ccn_closure *selfp,
			enum ccn_upcall_kind kind,
			struct ccn_upcall_info *info);
public:
	uintmax_t chunk;
	bool done;
	char *buffer;
	unsigned long bufsize;
	CCNGetChunk(CCNPipeline *pccnp, struct ccn *pccn, struct ccn_charbuf *pname, uintmax_t pchunk);
	~CCNGetChunk();
	bool doRequest();
};

class CCNPipeline
{
private:
	Buffer *buffer;
	struct ccn *ccn;
	struct ccn_charbuf *name;
	struct ccn_header *header;
	struct ccn_schedule *schedule;
	struct ccn_scheduled_event *chunk_downloader;
	struct ccn_scheduled_event *result_getter;
	queue<CCNGetChunk*> window;
	uintmax_t nextchunk;
	static int getChunks(
			struct ccn_schedule *sched,
			void *clienth,
			struct ccn_scheduled_event *ev,
			int flags);
	static int getResults(
			struct ccn_schedule *sched,
			void *clienth,
			struct ccn_scheduled_event *ev,
			int flags);
public:
	unsigned int winsize, toreceive, received;
	bool requestsdone, receivedone;
	CCNPipeline();
	bool initCCN();
	void runEvents();
	bool initStream(string pname, unsigned int pwinsize);
	void scheduleReceipt();
	void saveToFile(string fname);
};

#endif / * WINDOWING_H_ */

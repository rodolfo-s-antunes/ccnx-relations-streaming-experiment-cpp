/**
 * @file Windowing.cpp
 */
/*
#include <sys/time.h>
#include <cstdlib>
#include <cstring>
#include "Windowing.h"

#define WAIT_DELAY 1000

static void mygettime(const struct ccn_gettime *self, struct ccn_timeval *result)
{
	struct timeval now = {0};
	gettimeofday(&now, 0);
	result->s = now.tv_sec;
	result->micros = now.tv_usec;
}

static struct ccn_gettime myticker = {
		"timer",
		&mygettime,
		1000000,
		NULL
};

CCNGetChunk::CCNGetChunk(CCNPipeline *pccnp, struct ccn *pccn, struct ccn_charbuf *pname, uintmax_t pchunk)
{
	ccnp = pccnp;
	ccn = pccn;
	chunk = pchunk;
	name = ccn_charbuf_create();
	ccn_charbuf_append_charbuf(name, pname);
	ccn_name_append_numeric(name, CCN_MARKER_SEQNUM, pchunk);
	buffer = NULL;
	bufsize = 0;
	closure = NULL;
	done = false;
}

CCNGetChunk::~CCNGetChunk()
{
	ccn_charbuf_destroy(&name);
	free(buffer);
}

bool CCNGetChunk::doRequest()
{
	closure = new struct ccn_closure;
	closure->p = &incomingData;
	closure->data = this;
	closure->intdata = 0;
	int res = ccn_express_interest(ccn, name, closure, NULL);
	//printf("express_interest: %d\n", res);
	if (res < 0) return false;
	else return true;
}

enum ccn_upcall_res CCNGetChunk::incomingData(
		struct ccn_closure *selfp,
		enum ccn_upcall_kind kind,
		struct ccn_upcall_info *info)
{
	CCNGetChunk *ccngc = (CCNGetChunk*) selfp->data;
	if (kind == CCN_UPCALL_FINAL) {
		delete selfp;
		return(CCN_UPCALL_RESULT_OK);
	} else if (kind == CCN_UPCALL_CONTENT) {
		const unsigned char *ccnb = NULL;
		size_t ccnb_size = 0;
		const unsigned char *data = NULL;
		size_t data_size = 0;
		ccnb = info->content_ccnb;
		ccnb_size = info->pco->offset[CCN_PCO_E];
		printf("--> Recovering result for chunk: %lu\n", ccngc->chunk);
		ccn_content_get_value(ccnb, ccnb_size, info->pco, &data, &data_size);
		ccngc->bufsize = data_size;
		ccngc->buffer = (char*)malloc(sizeof(char)*ccngc->bufsize);
		memcpy(ccngc->buffer,data,ccngc->bufsize);
		ccngc->done = true;
		ccngc->ccnp->received++;
		if (ccngc->ccnp->received >= ccngc->ccnp->toreceive)
			ccngc->ccnp->scheduleReceipt();
		return(CCN_UPCALL_RESULT_OK);
	} else if (kind == CCN_UPCALL_INTEREST_TIMED_OUT) {
		printf("--> TIMEOUT: Chunk %lu - resending interest...", ccngc->chunk);
		return(CCN_UPCALL_RESULT_REEXPRESS);
	} else {
		printf("--> Unknown upcall in CCNGetChunk::incomingData: %d\n", kind);
		return(CCN_UPCALL_RESULT_ERR);
	}
}

CCNPipeline::CCNPipeline()
{
	ccn = NULL;
	name = NULL;
	header = NULL;
	schedule = NULL;
	chunk_downloader = NULL;
	result_getter = NULL;
	buffer = NULL;
	nextchunk = 0;
	winsize = 0;
	toreceive = 0;
	received = 0;
	requestsdone = false;
	receivedone = false;
}

bool CCNPipeline::initCCN()
{
	ccn = ccn_create();
	if (ccn_connect(ccn,NULL) == -1) return false;
	else return true;
}

bool CCNPipeline::initStream(string pname, unsigned int pwinsize)
{
	int res;
	winsize = pwinsize;
	buffer = new Buffer(0);
	name = ccn_charbuf_create();
	ccn_name_from_uri(name, pname.c_str());
	res = ccn_resolve_version(ccn, name, CCN_V_HIGHEST, 1000);
	if (res < 1) return false;
	header = ccn_get_header(ccn, name, 1000);
	if (header == NULL) return false;
	schedule = ccn_schedule_create(this, &myticker);
	chunk_downloader = ccn_schedule_event(schedule, 0, &(this->getChunks), NULL, 0);
	return true;
}

int CCNPipeline::getChunks(
		struct ccn_schedule *sched,
		void *clienth,
		struct ccn_scheduled_event *ev,
		int flags)
{
	CCNPipeline *ccnp = (CCNPipeline*) clienth;

	if ((flags & CCN_SCHEDULE_CANCEL) != 0) {
		return 0;
	}
	//printf("--> Requesting chunk %ju\n", ccnp->nextchunk);
	CCNGetChunk *ccngc = new CCNGetChunk(ccnp, ccnp->ccn, ccnp->name, ccnp->nextchunk);
	ccnp->window.push(ccngc);
	ccngc->doRequest();
	ccnp->toreceive++;
	ccnp->nextchunk++;
	if (ccnp->nextchunk >= ccnp->header->count) ccnp->requestsdone = true;
	if ((ccnp->window.size() >= ccnp->winsize) || (ccnp->nextchunk >= ccnp->header->count)) {
		ccn_schedule_cancel(ccnp->schedule, ccnp->chunk_downloader);
	}
	return 1;
}

int CCNPipeline::getResults(
		struct ccn_schedule *sched,
		void *clienth,
		struct ccn_scheduled_event *ev,
		int flags)
{
	if ((flags & CCN_SCHEDULE_CANCEL) != 0) {
		return 0;
	}
	CCNPipeline *ccnp = (CCNPipeline*) clienth;
	while ((ccnp->window.size() > 0) && (ccnp->window.front()->done)) {
		CCNGetChunk *ccngc = ccnp->window.front();
		printf("--> chunknumber: %lu\n", (unsigned long)ccngc->chunk);
		ccnp->window.pop();
		ccnp->buffer->insertData(ccngc->bufsize, ccngc->buffer);
		delete ccngc;
	}
	if (ccnp->window.size() == 0) {
		ccn_schedule_cancel(ccnp->schedule, ccnp->result_getter);
		if (ccnp->requestsdone)
			ccnp->receivedone = true;
		else
			ccnp->chunk_downloader = ccn_schedule_event(ccnp->schedule, 0, &(ccnp->getChunks), NULL, 0);
	}
	return 1;
}

void CCNPipeline::scheduleReceipt()
{
	result_getter = ccn_schedule_event(schedule, 0, &(this->getResults), NULL, 0);
}

void CCNPipeline::runEvents()
{
	ccn_run(ccn, 1);
	ccn_schedule_run(schedule);
}

void CCNPipeline::saveToFile(string fname)
{
	int res;
	FILE *fp = fopen(fname.c_str(), "wb");
	char *buf = (char*)malloc(sizeof(char)*4096);
	while ((res = buffer->popDataChunk(4096,buf)) > 0) {
		fwrite(buf, sizeof(char), res, fp);
	}
	free(buf);
	fclose(fp);
	buffer->clearBuffer();
}
*/

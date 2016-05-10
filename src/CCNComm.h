/* 
 * @file CCNComm.h
 */

#ifndef CCNCOMM_H_
#define CCNCOMM_H_

#include <string>
#include "Buffer.h"
#include "MetaBuffer.h"
extern "C" {
#include <ccn/ccn.h>
#include <ccn/charbuf.h>
#include <ccn/uri.h>
#include <ccn/fetch.h>
}

using namespace std;

class CCNGet {
	struct ccn *ccn;
	struct ccn_fetch *fetch;
	struct ccn_fetch_stream *stream;
	struct ccn_charbuf *name;
	struct ccn_charbuf *templ;
	struct ccn_charbuf* make_template(int allow_stale, int scope);
public:
	CCNGet();
	bool initStream(string id, string name, int pipeline);
	bool initMetaStream(string id, string name, string metaname, int pipeline);
	int getBytes(Buffer *buffer, int blocksize, double *downloadtime);
	int getBytes(Buffer *buffer, int blocksize);
	int getMetaBytes(MetaBuffer *metabuff, int blocksize);
	void endStream();
};


#endif /* CCNCOMM_H_ */

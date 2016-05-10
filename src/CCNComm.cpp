/**
 * @file CCNComm.c
 */

#include <cstdlib>
#include <iostream>
#include <cstring>
#include <time.h>
#include "Buffer.h"
#include "CCNComm.h"
extern "C" {
#include <ccn/ccn.h>
#include <ccn/charbuf.h>
#include <ccn/uri.h>
#include <ccn/fetch.h>
}

#define ASSUMEFIXED 0
const unsigned char meta[8] = {CCN_MARKER_CONTROL, '.', 'M', 'E', 'T', 'A', '.', 'M'};

/**
* Constructor for CCNGet class
*/
CCNGet::CCNGet()
{
	name = NULL;
	templ = NULL;
	fetch = NULL;
	ccn = NULL;
	stream = NULL;
}

/**
* Initiates a stream to download data
*
* @param id identifier of the ccn stream
* @param pname name of the object to download
* @param pipeline number of parallel requisitions for chunks
*/
bool CCNGet::initStream(string id, string pname, int pipeline)
{
	name = ccn_charbuf_create();
	name->length = 0;
	ccn_name_from_uri(name, pname.c_str());
	templ = make_template(0,-1);
	ccn = ccn_create();
	if (ccn_connect(ccn,NULL) == -1) return false;
	fetch = ccn_fetch_new(ccn);
	stream = ccn_fetch_open(fetch, name, id.c_str(), templ, pipeline, CCN_V_HIGHEST, ASSUMEFIXED);
	if (stream == NULL) return false;
	else return true;
}

/**
* Initiates a stream to download metadata (relations)
*
* @param id identifier of the ccn stream
* @param pname name of the object containing the metadata
* @param pmetaname name of the meta object to download
* @param pipeline number of parallel requisitions for chunks
*/
bool CCNGet::initMetaStream(string id, string pname, string pmetaname, int pipeline)
{
	name = ccn_charbuf_create();
	name->length = 0;
	ccn_name_from_uri(name, pname.c_str());
	templ = make_template(0,-1);
	ccn = ccn_create();
	if (ccn_connect(ccn,NULL) == -1) return false;
	if (ccn_resolve_version(ccn, name, CCN_V_HIGHEST, 1000) < 1) return false;
	ccn_name_append(name, meta, sizeof(meta));
	ccn_name_append_str(name, pmetaname.c_str());
	fetch = ccn_fetch_new(ccn);
	stream = ccn_fetch_open(fetch, name, id.c_str(), templ, pipeline, CCN_V_HIGHEST, ASSUMEFIXED);
	if (stream == NULL) return false;
	else return true;
}

/**
* Ends the download stream
*/
void CCNGet::endStream()
{
	stream = ccn_fetch_close(stream);
	ccn_destroy(&ccn);
	ccn_charbuf_destroy(&templ);
	ccn_charbuf_destroy(&name);
}

/**
* Reads a given quantity of data and put it into a buffer
*
* @param *buffer buffer to store read data
* @param blocksize size of read block
* @return res number of bytes read but not appended to buffer... if 0, finished getting bytes
*/
int CCNGet::getBytes(Buffer *buffer, int blocksize, double *downloadtime)
{
	timespec bts, ets;
    double bmsec, emsec;
	int res;
	char *auxbuf = (char*)malloc(sizeof(char)*blocksize);
	do {
		clock_gettime(CLOCK_REALTIME, &bts);
		res = ccn_fetch_read(stream, auxbuf, blocksize);
		clock_gettime(CLOCK_REALTIME, &ets);
		if (res > 0) {
			buffer->insertData(res,auxbuf);		// leitura OK, coloca no buffer
			break;
		}
		else if (res == CCN_FETCH_READ_NONE)
		{
			if (ccn_run(ccn, 1000) < 0) break;
		}
		else if (res == CCN_FETCH_READ_END) 
		{
			break;
		}
		else if (res == CCN_FETCH_READ_TIMEOUT)
		{
			ccn_reset_timeout(stream);
			if (ccn_run(ccn, 1000) < 0) break;
		}
		else break;
	} while (res != 0);
	bmsec = ((double)(long)bts.tv_sec)*1000. + ((double)(long)bts.tv_nsec)/1000000.;
    emsec = ((double)(long)ets.tv_sec)*1000. + ((double)(long)ets.tv_nsec)/1000000.;
    *downloadtime = emsec-bmsec;
	free(auxbuf);
	//if (res==0) buffer->producing = false;
	return res;	
}

int CCNGet::getBytes(Buffer *buffer, int blocksize)
{
	int res;
	char *auxbuf = (char*)malloc(sizeof(char)*blocksize);
	while ((res = ccn_fetch_read(stream, auxbuf, blocksize)) != 0)
	{
		if (res > 0) {
			buffer->insertData(res,auxbuf);		// leitura OK, coloca no buffer
			break;
		}
		else if (res == CCN_FETCH_READ_NONE)
		{
			if (ccn_run(ccn, 1000) < 0) break;
		}
		else if (res == CCN_FETCH_READ_END)
		{
			break;
		}
		else if (res == CCN_FETCH_READ_TIMEOUT)
		{
			ccn_reset_timeout(stream);
			if (ccn_run(ccn, 1000) < 0) break;
		}
		else break;
	}
	free(auxbuf);
	//if (res==0) buffer->producing = false;
	return res;
}

/**
* Reads a given quantity of metadata and puts it into a buffer
*
* @param *buffer buffer to store read data
* @param blocksize size of read block
* @return res number of bytes read but not appended to buffer
*/
int CCNGet::getMetaBytes(MetaBuffer *metabuff, int blocksize)
{
	int res;
	char *auxbuf = (char*)malloc(sizeof(char)*blocksize);
	while ((res = ccn_fetch_read(stream, auxbuf, blocksize)) != 0)
	{
		if (res > 0) {
			metabuff->insertData(res, auxbuf);
			break;
		}
		else if (res == CCN_FETCH_READ_NONE)
		{
			if (ccn_run(ccn, 1000) < 0) break;
		}
		else if (res == CCN_FETCH_READ_END)
		{
			break;
		}
		else if (res == CCN_FETCH_READ_TIMEOUT)
		{
			ccn_reset_timeout(stream);
			if (ccn_run(ccn, 1000) < 0) break;
		}
		else
		{
			break;
		}
	}
	free(auxbuf);
	return res;	
}

/**
* Creates a template for ccn interest fetch
*
* @param allow_stale
* @param scope
*/
struct ccn_charbuf* CCNGet::make_template(int allow_stale, int scope)
{
	struct ccn_charbuf *templ = ccn_charbuf_create();
	ccn_charbuf_append_tt(templ, CCN_DTAG_Interest, CCN_DTAG);
	ccn_charbuf_append_tt(templ, CCN_DTAG_Name, CCN_DTAG);
	ccn_charbuf_append_closer(templ); /* </Name> */
	ccn_charbuf_append_tt(templ, CCN_DTAG_MaxSuffixComponents, CCN_DTAG);
	ccnb_append_number(templ, 1);
	ccn_charbuf_append_closer(templ); /* </MaxSuffixComponents> */
	if (allow_stale) {
		ccn_charbuf_append_tt(templ, CCN_DTAG_AnswerOriginKind, CCN_DTAG);
		ccnb_append_number(templ, CCN_AOK_DEFAULT | CCN_AOK_STALE);
		ccn_charbuf_append_closer(templ); /* </AnswerOriginKind> */
	}
	if (scope >= 0 && scope <= 2) {
		ccnb_tagged_putf(templ, CCN_DTAG_Scope, "%d", scope);
	}
	ccn_charbuf_append_closer(templ); /* </Interest> */
	return(templ);
}

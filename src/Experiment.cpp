/**
 * @file Experiment.cpp
 */

#include <cstdlib>
#include <cstdio>
#include <unistd.h>
#include <getopt.h>
#include "Buffer.h"
#include "CCNComm.h"
#include "Experiment.h"
#include "CCNRelations.h"
#include "Threads.h"
#include <iostream>

#define BUFFERSIZE 60000 // [bytes]	--	180224 * 6
#define BLOCKSIZE 10000	// [bytes]
#define PIPELINE 16
#define OBJECT_STREAM_RATE 10000 // [bytes per second] -- 1,5 Mbits/s = 0,1875 Mbytes/s = 192 Kbytes/s = 196608 bytes/s
#define VIDEO_STREAM_RATE 10000  	// [bytes per second] -- 1536 kbits/s - 128 kbits/s = 1408 kbits/s = 176 kbytes/s = 180224 bytes/s
 //tamanho do arquivo de vídeo = 180224 * 60
#define AUDIO_STREAM_RATE 1000 	// [bytes per second] -- 128 kbits/s = 16 kbytes/s = 16384 bytes/s
#define SUBTITLE_STREAM_RATE 1000	// [bytes per second] -- aleatório


/**
 * Constructor for a basic download experiment
 */
BasicStreamExperiment::BasicStreamExperiment()
{
	pipeline = -1;
	buffersize = -1;
	blocksize = -1;
	streamrate = -1;
	runid = -1;
	experimentid = "";
	objname = "";
}

/**
 * Gets command line arguments for a basic stream experiment and sets all associated variables
 * Command line:
 *  -b <blocksize> Size of content blocks to be streamed
 *  -r <streamrate> Stream rate in bytes per second
 *  -B <buffersize> Buffer size in bytes
 *  -P <pipeline> Window size (max 16 because of CCNx limitation)
 *  -v <videoobject> Name of the video object to be streamed
 *  -E <experimentid> Experiment identifier
 *  -R <runnumber> Run identifier
 *
 * @param argc number of arguments on command line
 * @param argv command line
 * @return true if found all information needed, false otherwise
 */
bool BasicStreamExperiment::parseOpts(int argc, char **argv)
{
	bool allargs = true;
	int opt;
	while ((opt = getopt(argc, argv, "b:B:P:r:v:E:R:")) != -1) {
		switch (opt) {
		case 'b':
			blocksize = atoi(optarg);
			break;
		case 'B':
			buffersize = atoi(optarg);
			break;
		case 'P':
			pipeline = atoi(optarg);
			break;
		case 'r':
			streamrate = atoi(optarg);
			break;
		case 'v':
			objname = optarg;
			break;
		case 'E':
			experimentid = optarg;
			break;
		case 'R':
			runid = atoi(optarg);
			break;
		default:
			printf("Unknown argument: %s\n", argv[optopt]);
			return false;
		}
	}
	if (objname.size() < 1) allargs = false;
	if (experimentid.size() < 1) allargs = false;
	if (blocksize < 0) allargs = false;
	if (buffersize < 0) allargs = false;
	if (pipeline < 0) allargs = false;
	if (streamrate < 0) allargs = false;
	if (runid < 0) allargs = false;
	if (!allargs) {
		printf("One or more arguments missing!\n");
		return false;
	}
	return true;
}

/**
 * Creates a thread to stream the object in a basic experiment
 *
 * @return true if successful download, false otherwise
 */
bool BasicStreamExperiment::runExperiment()
{
	printf("objname=%s buffersize=%d pipeline=%d\n", objname.c_str(), buffersize, pipeline);
	StreamThreads dt("OBJECT", objname, buffersize, pipeline, blocksize, streamrate);
	if (!dt.createThreads()) {
		return false;
	}
	else {
		dt.waitForThreads();
		return true;
	}
}

/**
 * Constructor for a stream experiment with relations
 */
RelationStreamExperiment::RelationStreamExperiment()
{
	objname = "";
	audioid = "";
	experimentid = "";
	runid = -1;
	pipeline = -1;
	vbuffersize = -1;
	abuffersize = -1;
	vblocksize = -1;
	ablocksize = -1;
	vstreamrate = -1;
	astreamrate = -1;
	sstreamrate = -1;
	subtitled = false;
}

/**
 * Gets command line arguments for a stream experiment with relations and sets all associates variables
 * Command line: -B <buffersize> -P <pipeline> -S <subtitle> <videoobject> <audioobject> <experimentid>
 * subtitle is optional
 *
 * @param argc number of arguments on command line
 * @param argv command line 
 * @return true if found all information needed, false otherwise
 */
bool RelationStreamExperiment::parseOpts(int argc, char **argv)
{
	bool allargs = true;
	int opt;
	while ((opt = getopt(argc, argv, "b:m:B:M:P:V:A:v:a:E:R:")) != -1) {
		switch (opt) {
		case 'b':
			vblocksize = atoi(optarg);
			break;
		case 'm':
			ablocksize = atoi(optarg);
			break;
		case 'B':
			vbuffersize = atoi(optarg);
			break;
		case 'M':
			abuffersize = atoi(optarg);
			break;
		case 'P':
			pipeline = atoi(optarg);
			break;
		case 'V':
			vstreamrate = atoi(optarg);
			break;
		case 'A':
			astreamrate = atoi(optarg);
			break;
		case 'v':
			objname = optarg;
			break;
		case 'a':
			audioid = optarg;
			break;
		case 'E':
			experimentid = optarg;
			break;
		case 'R':
			runid = atoi(optarg);
			break;
		default:
			printf("Unknown argument: %s\n", argv[optopt]);
			return false;
		}
	}
	if (objname.size() < 1) allargs = false;
	if (audioid.size() < 1) allargs = false;
	if (experimentid.size() < 1) allargs = false;
	if (vblocksize < 0) allargs = false;
	if (ablocksize < 0) allargs = false;
	if (vbuffersize < 0) allargs = false;
	if (abuffersize < 0) allargs = false;
	if (pipeline < 0) allargs = false;
	if (vstreamrate < 0) allargs = false;
	if (astreamrate < 0) allargs = false;
	if (runid < 0) allargs = false;
	if (!allargs) {
		printf("One or more arguments missing!\n");
		return false;
	}
	return true;
}

/**
 * Creates threads to download the main object and the related ones
 *
 * @return true if successful download, false otherwise
 */
bool RelationStreamExperiment::runExperiment()
{
	if (subtitled) printf("experiment=%s objname=%s audioid=%s subtitleid=%s vbuffersize=%d abuffersize=%d pipeline=%d\n", experimentid.c_str(), objname.c_str(), audioid.c_str(), subtitleid.c_str(), vbuffersize, abuffersize, pipeline);
	else printf("experiment=%s objname=%s audioid=%s vbuffersize=%d abuffersize=%d pipeline=%d\n", experimentid.c_str(), objname.c_str(), audioid.c_str(), vbuffersize, abuffersize, pipeline);
	CCNRelations ccnrel(objname);
	string audioobj;
	string subtitleobj;
	if (!ccnrel.fetchRelations())
	{
		printf("fetchRelations FAILED!\n");
		return false;
	}
	audioobj = ccnrel.getRelation(audioid);
	subtitleobj = ccnrel.getRelation(subtitleid);
	//ccnrel.printData();

	StreamThreads videodt("VIDEO", objname, vbuffersize, pipeline, vblocksize, vstreamrate);
	StreamThreads audiodt("AUDIO", audioobj, abuffersize, pipeline, ablocksize, astreamrate);
	StreamThreads subtitledt("SUBTITLE", subtitleobj, abuffersize, pipeline, ablocksize, sstreamrate);
	if (subtitled) 
	{
		if (!subtitledt.createThreads())
		{
			return false;
		}
	}
	
	if ((!videodt.createThreads()) || (!audiodt.createThreads()))
	{
		return false;
	}
	else 
	{
		videodt.waitForThreads();
		audiodt.waitForThreads();
		if (subtitled) {
			subtitledt.waitForThreads();
		}
		return true;
	}
}

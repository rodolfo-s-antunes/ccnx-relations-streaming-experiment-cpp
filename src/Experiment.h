/* 
 * @file Experiment.h
 */

#ifndef EXPERIMENT_H_
#define EXPERIMENT_H_

#include <string>

using namespace std;

class BasicStreamExperiment
{
	string experimentid, objname;
	int buffersize, pipeline, blocksize, streamrate, runid;
public:
	BasicStreamExperiment();
	bool runExperiment();
	bool parseOpts(int argc, char **argv);
};

class RelationStreamExperiment
{
	string experimentid, objname, audioid, subtitleid;
	int vbuffersize, abuffersize, pipeline, vblocksize, ablocksize, vstreamrate, astreamrate, sstreamrate, runid;
	bool subtitled;
public:
	RelationStreamExperiment();
	bool runExperiment();
	bool parseOpts(int argc, char **argv);
};

#endif /* EXPERIMENT_H_ */

/**
 * @file BasicDownloadExperiment.cpp
 */

#include <cstdio>
#include <unistd.h>
#include <sys/time.h>
#include "Experiment.h"
extern "C" {
#include <ccn/ccn.h>
#include <ccn/charbuf.h>
#include <ccn/uri.h>
#include <ccn/fetch.h>
}

using namespace std;

int main(int argc, char **argv)
{
	bool result;
	BasicStreamExperiment exp;
	result = exp.parseOpts(argc,argv);

	if (!result) return 1;
	else
	{
		result = exp.runExperiment();
		if (result) printf("SUCCESS!\n");
		else printf("FAILURE!\n");
		return 0;
	}
}

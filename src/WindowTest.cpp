#include <string>
#include <cstdlib>
#include <cstdio>
#include <cstring>

extern "C" {
#include <ccn/ccn.h>
#include <ccn/charbuf.h>
#include <ccn/uri.h>
#include <ccn/fetch.h>
#include <ccn/schedule.h>
}

#include "Windowing.h"

using namespace std;

/*
int main(int argc, char **argv)
{
	CCNPipeline ccnp;
	ccnp.initCCN();
	ccnp.initStream(argv[1], atol(argv[2]));
	while (!ccnp.receivedone) {
		ccnp.runEvents();
	}
	ccnp.saveToFile("out.dat");
	return 0;
}
*/

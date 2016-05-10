/**
 * @file CCNRelations.cpp
 */

#include <cstdlib>
#include <cstring>
#include <iostream>
#include <unistd.h>
#include <map>
#include <string>
#include "CCNRelations.h"
#include "CCNComm.h"

#define PIPELINE 4

string RELATIONS = "relations";

using namespace std;

/**
 * CCNRelations constructor
 *
 * @param poname name of main object
 */
CCNRelations::CCNRelations(string poname) : metabuff()
{
	objname = poname;
}

/**
 * Prints all object relations 
 */
void CCNRelations::printData()
{
	for( map<string,string>::iterator ii=relations.begin(); ii!=relations.end(); ++ii)
	{
		cout << (*ii).first << " -> " << (*ii).second << endl;
	}
}

/**
 * Given a relation id, gets related object name
 *
 * @param relname main object name
 */
string CCNRelations::getRelation(string relname)
{
	if (relations.count(relname) > 0)
		return relations[relname];
	else
		return ""; 
}

/**
 * Fetch object relations
 *
 * @return true if successfully fetched relations, false otherwise
 */
bool CCNRelations::fetchRelations()
{
	bool result = false;
	CCNGet ccnget;
	ccnget.initMetaStream(RELATIONS, objname, RELATIONS, PIPELINE);
	int readsize = sysconf(_SC_PAGESIZE);
	int res;
	do
	{
		res = ccnget.getMetaBytes(&metabuff,readsize);	// le 'readsize' bytes do metadado relations
		if (res == 0)
		{
			result = true;		// se for 0, acabou
		}
	}
	while (res > 0);
	ccnget.endStream();
	if (result) parseRelations();
	return result;
}

/**
 * Reads fetched relations metadata and stores relations IDs and respective names in the relations map
 */
void CCNRelations::parseRelations()
{
	char *pos = metabuff.getDataPointer();
	char *auxbuff = (char*)malloc(sizeof(char)*4096);
	char *auxpos = auxbuff;
	int auxsize = 0;
	string relid, relobj;
	for (unsigned int i=0; i<metabuff.size(); i++)
	{
		if (*pos == '\n')
		{
			if (auxsize > 0)
			{
				*auxpos = '\0';
				relobj = auxbuff;	//saves the object name related to the 'relid' (relation id)
				relations[relid] = relobj;
				auxpos = auxbuff;
				auxsize = 0;
			}
			pos++;
		}
		else if (*pos == '\t')
		{
			*auxpos = '\0';
			relid = auxbuff;	//saves relation id
			auxpos = auxbuff;
			auxsize = 0;
			pos++;
		}
		else
		{
			*auxpos = *pos;	
			auxsize++;
			auxpos++;
			pos++;
		}
	}
	free(auxbuff);
	metabuff.clearMetaBuffer();
}

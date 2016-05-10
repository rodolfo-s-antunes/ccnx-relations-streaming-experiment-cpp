/* 
 * @file CCNRelations.h
 */

#ifndef CCNRELATIONS_H_
#define CCNRELATIONS_H_

#include <map>
#include <string>
#include "MetaBuffer.h"

using namespace std;

class CCNRelations
{
	string objname;
	MetaBuffer metabuff;
	map<string,string> relations;
	void parseRelations();
public:
	CCNRelations(string poname);
	bool fetchRelations();
	string getRelation(string relname);
	void printData();
};

#endif /* CCNRELATIONS_H_ */

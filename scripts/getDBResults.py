#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, time
import psycopg2
import numpy as np
import scipy as sp
import scipy.stats as sps

CONFVAL = 0.95
DBHOST = 'localhost'
DBPORT = 5432
DBUSER = 'gticn'
DBPASS = 'gticn'
DBDB = 'results'

FACES = dict(bte_uk='192.168.11.2:9695', bte_es='192.168.1.2:9695', bte_nl='192.168.0.1:9695', bte_de='192.168.2.2:9695', bte_it='192.168.3.2:9695', bte_fr='192.168.101:9695', )

class DBManager:
   def __init__(self):
      self.con = psycopg2.connect(host=DBHOST, user=DBUSER, password=DBPASS, dbname=DBDB, port=DBPORT)
      return
   def getFaceVariable(self, varname, storeat, rd):
      querytemp = "select routerinfo.experiment,routerinfo.run,routerinfo.routername,faceinfo.addr,%s "
      querytemp += "from routerinfo,faceinfo "
      querytemp += "where routerinfo.id = faceinfo.routerid "
      querytemp += "group by routerinfo.experiment,routerinfo.run,routerinfo.routername,faceinfo.addr;"
      cur = self.con.cursor()
      varpart = "max(faceinfo.%s)"%varname
      cur.execute(querytemp%varpart)
      for row in cur.fetchall():
         if (row[2] in FACES.keys() and (FACES[row[2]] == row[3])):
            rd.addValue(row[0], row[1], row[2], '%s_max'%storeat, long(row[4]))
      varpart = "min(faceinfo.%s)"%varname
      cur.execute(querytemp%varpart)
      for row in cur.fetchall():
         if (row[2] in FACES.keys() and (FACES[row[2]] == row[3])):
            rd.addValue(row[0], row[1], row[2], '%s_min'%storeat, long(row[4]))
      cur.close()
      return
   def getRouterVariable(self, varname, storeat, rd):
      querytemp = "select routerinfo.experiment,routerinfo.run,routerinfo.routername,%s "
      querytemp += "from routerinfo "
      querytemp += "group by routerinfo.experiment,routerinfo.run,routerinfo.routername;"
      cur = self.con.cursor()
      varpart = "max(routerinfo.%s)"%varname
      cur.execute(querytemp%varpart)
      for row in cur.fetchall():
         if (row[2] in FACES.keys()):
            rd.addValue(row[0], row[1], row[2], '%s_max'%storeat, long(row[3]))
      varpart = "min(routerinfo.%s)"%varname
      cur.execute(querytemp%varpart)
      for row in cur.fetchall():
         if (row[2] in FACES.keys()):
            rd.addValue(row[0], row[1], row[2], '%s_min'%storeat, long(row[3]))
      cur.close()
      return

class ResultDict:
   def __init__(self):
      self.dd = dict()
      return
   def __confInt(self, vector, confidence=CONFVAL):
      if len(vector) == 0:
         return 0
      else: 
         data = np.array(vector)
         m = np.mean(data)
         return sp.stats.sem(data) * sps.t._ppf((1.0+confidence)/2.0, len(data)-1)
   def insertValue(self, experiment, run, router, variable, value):
      if experiment not in self.dd:
         self.dd[experiment] = dict()
      if run not in self.dd[experiment]:
         self.dd[experiment][run] = dict()
      if router not in self.dd[experiment][run]:
         self.dd[experiment][run][router] = dict()
      self.dd[experiment][run][router][variable] = value
      return
   def addValue(self, experiment, run, router, variable, value):
      if experiment not in self.dd:
         self.dd[experiment] = dict()
      if run not in self.dd[experiment]:
         self.dd[experiment][run] = dict()
      if router not in self.dd[experiment][run]:
         self.dd[experiment][run][router] = dict()
      if variable not in self.dd[experiment][run][router]:
         self.dd[experiment][run][router][variable] = 0
      self.dd[experiment][run][router][variable] += value
      return
   def __getRouterVarDiff(self, varname):
      tdict = dict()
      for ke in self.dd:
         runs = self.dd[ke]
         for krun in runs:
            routers = runs[krun]
            for krout in routers:
               tk = '%s-%s'%(ke,krout)
               if tk not in tdict: tdict[tk] = list()
               routres = routers[krout]
               tdict[tk].append(float(routres['%s_max'%varname]-routres['%s_min'%varname]))
      rdict = dict()
      for tk in tdict:
         rdict[tk] = dict()
         rdict[tk]['avg'] = np.average(np.array(tdict[tk]))
         rdict[tk]['stddev'] = np.std(np.array(tdict[tk]))
         rdict[tk]['conf'] = self.__confInt(tdict[tk])
      return rdict
   def __getExperimentVarDiff(self, varname):
      tdict = dict()
      for ke in self.dd:
         tdict[ke] = list()
         runs = self.dd[ke]
         for krun in runs:
            sumrun = 0.0
            routers = runs[krun]
            for krout in routers:
               routres = routers[krout]
               sumrun += float(routres['%s_max'%varname]-routres['%s_min'%varname])
            tdict[ke].append(sumrun)
      rdict = dict()
      for tk in tdict:
         rdict[tk] = dict()
         rdict[tk]['avg'] = np.average(np.array(tdict[tk]))
         rdict[tk]['stddev'] = np.std(np.array(tdict[tk]))
         rdict[tk]['conf'] = self.__confInt(tdict[tk])
      return rdict      
   def getExperimentByteIn(self):
      return self.__getExperimentVarDiff('bytein')
   def getExperimentByteOut(self):
      return self.__getExperimentVarDiff('byteout')
   def getExperimentIntrIn(self):
      return self.__getExperimentVarDiff('intrin')
   def getExperimentIntrOut(self):
      return self.__getExperimentVarDiff('introut')
   def getExperimentStoredObjects(self):
      return self.__getExperimentVarDiff('storedobjects')
   def getExperimentCacheHit(self):
      tdict = dict()
      for ke in self.dd:
         tdict[ke] = list()
         runs = self.dd[ke]
         for krun in runs:
            hitssumrun = 0.0
            acceptedsumrun = 0.0
            routers = runs[krun]
            for krout in routers:
               routres = routers[krout]
               routsentintr = float(routres['sentintr_max']-routres['sentintr_min'])
               routacceptedintr = float(routres['acceptedintr_max']-routres['acceptedintr_min'])
               cachehits = routacceptedintr-routsentintr
               if cachehits > 0:
                    hitssumrun += cachehits
                    acceptedsumrun += routacceptedintr
            if acceptedsumrun > 0:
               tdict[ke].append(hitssumrun/acceptedsumrun)
            else:
               tdict[ke].append(0)
      rdict = dict()
      for tk in tdict:
         rdict[tk] = dict()
         rdict[tk]['avg'] = np.average(np.array(tdict[tk]))
         rdict[tk]['stddev'] = np.std(np.array(tdict[tk]))
         rdict[tk]['conf'] = self.__confInt(tdict[tk])
      return rdict

class Main:
   def __init__(self):
      if len(sys.argv) < 2:
         print 'Missing parameter: experiment name'
         sys.exit(1)
      expname = sys.argv[1]
      rd = ResultDict()
      dbm = DBManager()
      print '*** BYTES'
      dbm.getFaceVariable('byteout_total', 'byteout', rd)
      dbm.getFaceVariable('bytein_total', 'bytein', rd)
      self.generateResultFilePerClients(expname, 'bytein', rd.getExperimentByteIn(), convmb=True)
      self.generateResultFilePerClients(expname, 'byteout', rd.getExperimentByteOut(), convmb=True)
      print '*** INTR'
      dbm.getFaceVariable('introut_total', 'introut', rd)
      dbm.getFaceVariable('intrin_total', 'intrin', rd)
      self.generateResultFilePerClients(expname, 'intrin', rd.getExperimentIntrIn())
      self.generateResultFilePerClients(expname, 'introut', rd.getExperimentIntrOut())
      #print '*** STOREDOBJECTS'
      #dbm.getRouterVariable('cobs_accessioned', 'storedobjects', rd)
      #dbm.getAllRoutersStoredObjects(rd)
      #self.generateResultFilePerClients(expname, 'storedobjects', rd.getExperimentStoredObjects())
      print '*** CACHEHITS'
      dbm.getRouterVariable('interests_accepted', 'acceptedintr', rd)
      dbm.getRouterVariable('interests_sent', 'sentintr', rd)
      self.generateResultFilePerClients(expname, 'cachehits', rd.getExperimentCacheHit())
      return
   def generateResultFilePerFiles(self, expname, varname, dd, convmb=False):
      orgd = dict()
      for ek in dd:
         auxQ = ek.split('_')
         print auxQ
         if auxQ[0] == expname:
            exp = auxQ[0]
            flq = int(auxQ[2])
            cln = int(auxQ[4])
            if exp not in orgd: orgd[exp] = dict()
            if cln not in orgd[exp]: orgd[exp][cln] = dict()
            orgd[exp][cln][flq] = dd[ek]
      for ek in orgd:
         for clnk in sorted(orgd[ek]):
            outarq = open('%s-%s-cln%d.dat'%(varname,ek,clnk), 'w')
            for flqk in sorted(orgd[ek][clnk]):
               res = orgd[ek][clnk][flqk]
               if convmb:
                  outarq.write('%d %f %f %f\n'%(flqk, self.b2mb(res['avg']), self.b2mb(res['stddev']), self.b2mb(res['conf'])))
               else:
                  outarq.write('%d %f %f %f\n'%(flqk, res['avg'], res['stddev'], res['conf']))
            outarq.close()
      return
   def generateResultFilePerClients(self, expname, varname, dd, convmb=False):
      orgd = dict()
      for ek in dd:
         auxQ = ek.split('_')
         if auxQ[0] == expname:
            print auxQ
            exp = auxQ[0]
            flq = int(auxQ[2])
            cln = int(auxQ[4])
            if exp not in orgd: orgd[exp] = dict()
            if flq not in orgd[exp]: orgd[exp][flq] = dict()
            orgd[exp][flq][cln] = dd[ek]
      for ek in orgd:
         for flqk in sorted(orgd[ek]):
            outarq = open('%s-%s-flq%d.dat'%(varname,ek,flqk), 'w')
            for clnk in sorted(orgd[ek][flqk]):
               res = orgd[ek][flqk][clnk]
               if convmb:
                  outarq.write('%d %f %f %f\n'%(clnk, self.b2mb(res['avg']), self.b2mb(res['stddev']), self.b2mb(res['conf'])))
               else:
                  outarq.write('%d %f %f %f\n'%(clnk, res['avg'], res['stddev'], res['conf']))
            outarq.close()
      return
   def prettyPrint(self, dic):
      for k in sorted(dic):
         print '%s: %s %s %s'%(k,dic[k]['avg'],dic[k]['stddev'],dic[k]['conf'])
      return
   def prettyMBPrint(self, dic):
      for k in sorted(dic):
         print '%s: %s %s %s'%(k,self.b2mb(dic[k]['avg']),self.b2mb(dic[k]['stddev']),self.b2mb(dic[k]['conf']))
      return
   def b2mb(self, value): return float(value)/1048576.0

if __name__ == '__main__': Main()

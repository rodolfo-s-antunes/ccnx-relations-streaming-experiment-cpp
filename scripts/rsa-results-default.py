#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, time
import numpy as np
import scipy as sp
import scipy.stats as sps

def confInt(vector, confidence=0.95):
   if len(vector) == 0:
      return 0
   else: 
      data = np.array(vector)
      m = np.mean(data)
      return sp.stats.sem(data) * sps.t._ppf((1.0+confidence)/2.0, len(data)-1)

class RawData:
   def __init__(self, datadir, filterstr):
      self.datadir = datadir
      self.fs = filterstr
      self.rawdata = None
      return
   def getRawData(self):
      if self.rawdata == None:
         self.rawdata = dict()
         self.__getRawData()
      return self.rawdata
   def __getOutFiles(self):
      result = dict()
      for item in os.walk(self.datadir):
         if (len(item[1]) < 1) and (item[0].find(self.fs) > 0):
            auxoutfiles = list()
            for outi in item[2]:
               if outi [-4:] == '.out':
                  auxoutfiles.append(outi)
            result[item[0]] = auxoutfiles
      return result
   def __getRawData(self):
      outfiles = self.__getOutFiles()
      for item in outfiles:
         for oitem in outfiles[item]:
            self.__parseOutFile(item, oitem)
      return
   def __parseOutFile(self, dirname, arqname):
      arq = open(dirname+'/'+arqname, 'r')
      run = dirname.split('/')[5]
      for linha in arq:
         auxQ = linha.strip().split()
         client = auxQ[0][:-1]+'_'+run
         if len(auxQ) > 2:
            if client not in self.rawdata: self.rawdata[client] = dict(stalls=0, stallduration=list(), buffering=-1)
            if auxQ[2] == 'Waiting':
               if self.rawdata[client]['buffering'] < 0:
                  self.rawdata[client]['buffering'] = float(auxQ[6])
               else:
                  self.rawdata[client]['stallduration'].append(float(auxQ[6]))
                  self.rawdata[client]['stalls'] += 1

      arq.close()
      return

class ExperimentMetric:
   def __init__(self, rawdata):
      self.rd = rawdata
      self.ed = dict()
      return
   def __varMetrics(self, dd):
      result = dict()
      for k in dd:
         result[k] = dict()
         result[k]['avg'] = np.average(np.array(dd[k]))
         result[k]['stddev'] = np.std(np.array(dd[k]))
         result[k]['conf'] = confInt(dd[k])
      return result
   def getMetrics(self, classfunc):
      ignored = 0.0
      total = 0.0
      auxdict = dict()
      for item in self.rd:
         total += 1
         if self.rd[item]['buffering'] > 0:
            case, var = classfunc(item)
            if case not in auxdict: auxdict[case] = dict()
            if var not in auxdict[case]: auxdict[case][var] = dict(buffering=list(), stallduration=list(), stalls=list())
            auxdict[case][var]['buffering'].append(self.rd[item]['buffering'])
            auxdict[case][var]['stalls'].append(self.rd[item]['stalls'])
            auxdict[case][var]['stallduration'] += self.rd[item]['stallduration']
         else:
            ignored += 1
      for ck in auxdict:
         self.ed[ck] = dict()
         for vk in auxdict[ck]:
            self.ed[ck][vk] = self.__varMetrics(auxdict[ck][vk])
      print str.format("Ignored raw result ratio: {}/{} = {}", ignored, total, ignored/total)
      return self.ed
   def byClients(self, client):
      auxQ = client.split('_')
      casename = str.format('{}-flq{}', auxQ[0], auxQ[2])
      casevar = int(auxQ[4])
      return (casename, casevar)

class Main:
   def __init__(self):
      rd = RawData('/home/gticn/results', 'defaultum')
      rawdata = rd.getRawData()
      em = ExperimentMetric(rawdata)
      mbc = em.getMetrics(em.byClients)
      self.__writeOutput(mbc, 'buffering')
      self.__writeOutput(mbc, 'stallduration')
      self.__writeOutput(mbc, 'stalls')
      return
   def __writeOutput(self, dd, varname):
      for ic in dd:
         outname = ic+'-'+varname+'.txt'
         arq = open(outname, 'w')
         for vc in sorted(dd[ic]):
            d = dd[ic][vc][varname]
            arq.write(str.format('{}: {} {} {}\n', vc, d['avg'], d['stddev'], d['conf']))
         arq.close()
      return
   def __showData(self, dd):
      for ic in dd:
         print ic
         for vc in sorted(dd[ic]):
            print vc
            for mc in sorted(dd[ic][vc]):
               print mc
               print dd[ic][vc][mc]
      return

if __name__ == '__main__':
   Main()
#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, time
import subprocess as sp
from threading import Thread

EXECUTABLE = 'workspace/CppRelations/RelationStreamExperiment'

class ClientThread(Thread):
   def __init__(self, name, runnumber, client, starttime):
      Thread.__init__(self)
      self.name = name
      self.runnumber = runnumber
      self.starttime = starttime
      self.client = client
      self.out = None
      self.err = None
      self.parameters = ""
      return
   def run(self):
      print "Running client %s-%s-%s..."%(self.name, self.runnumber, self.client)
      cmd = "nice -n 19 %s %s"%(EXECUTABLE, self.parameters)
      print cmd
      waittime = self.starttime - int(time.time())
      if waittime > 0:
         print "Awaiting %ld seconds..."%waittime
         time.sleep(waittime)
      proc = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
      self.out, self.err = proc.communicate()
      if proc.returncode != 0:
         print 'Process %s-%s-%s return value: %d\n'%(self.name, self.runnumber, self.client, proc.returncode)
      return
   def setParameters(self, parmlist):
   	  for pi in parmlist:
   	     self.parameters += "%s "%pi
   	  self.parameters = self.parameters[:-1]
   	  return

class ExperimentControl:
   def __init__(self, experiment, run):
      self.experiment = experiment
      self.run = run
      self.threaddict = dict()
      return
   def parseOptions(self, conffile):
      arqc = open(conffile, 'r')
      for linha in arqc:
         auxQ = linha.strip().split()
         if len(auxQ) > 0:
            clname = auxQ[0]
            clstarttime = int(auxQ[1])
            auxthread = ClientThread(self.experiment,self.run,clname,clstarttime)
            auxthread.setParameters(auxQ[2:])
            self.threaddict[clname] = auxthread
      arqc.close()
      return
   def startThreads(self):
      for tk in sorted(self.threaddict):
         self.threaddict[tk].start()
      return
   def waitAndCollectResults(self):
      outarqname = '%s-%s.out'%(self.experiment,self.run)
      errarqname = '%s-%s.err'%(self.experiment,self.run)
      outarq = open(outarqname,'w')
      errarq = open(errarqname,'w')
      for tk in sorted(self.threaddict):
         self.threaddict[tk].join()
         if self.threaddict[tk].out != None:
            auxlines = self.threaddict[tk].out.split('\n')
            for linha in auxlines:
               if linha != "":
                  outarq.write('%s: %s\n'%(tk,linha))
         if self.threaddict[tk].err != None:
            auxlines = self.threaddict[tk].err.split('\n')
            for linha in auxlines:
               if linha != "":
                  errarq.write('%s: %s\n'%(tk,linha))
         os.system('sync')
      outarq.write("End.\n")
      return

class Main:
   def __init__(self):
      pass
   def main(self):
      basename = sys.argv[1]
      runnumber = int(sys.argv[2])
      conffile = sys.argv[3]
      ec = ExperimentControl(basename, runnumber)
      ec.parseOptions(conffile)
      ec.startThreads()
      ec.waitAndCollectResults()
      return

if __name__ == '__main__':
   m = Main()
   m.main()

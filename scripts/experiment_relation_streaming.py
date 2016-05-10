#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, time
import random, bisect, math 
import subprocess as sp
import numpy as np

# Esta lista contém o nome dos clientes na ordem em que eles serão
# preenchidos. Esta ordem segue a ideia de distribuir os clientes
# em largura dentro da árvore de transmissão centrada em MG.
#STATES = ['ce', 'df', 'sp', 'ba', 'ma', 'rn', 'go', 'rj', 'am', 'pr', 'rr', 'sc', 'es', 'se', 'pa', 'pb', 'mt', 'to', 'ms', 'rs', 'al', 'ap', 'pi', 'ro', 'pe', 'ac']
#STATES = ['de', 'it', 'fr', 'nl', 'uk', 'es']
STATES = ['uk']
CLIENTS = ['bte_'+x for x in STATES]
PUBLISHER = 'bte_pub'

def genHosts():
   result = ""
   for cl in CLIENTS:
      result += "%s,"%cl
   return result[:-1]

class ZipfGenerator: 
   def __init__(self, n, alpha): 
      # Calculate Zeta values from 1 to n: 
      tmp = [1. / (math.pow(float(i), alpha)) for i in range(1, n+1)] 
      zeta = reduce(lambda sums, x: sums + [sums[-1] + x], tmp, [0]) 
      # Store the translation map: 
      self.distMap = [x / zeta[-1] for x in zeta] 
   def next(self): 
      # Take a uniform 0-1 pseudo-random value: 
      u = random.random()
      # Translate the Zipf variable: 
      return bisect.bisect(self.distMap, u)-1

class ExperimentRun:
   def __init__(self, cd):
      self.name = cd['name']
      self.ccnprefix = cd['ccnprefix']
      self.clients = cd['clients']
      self.objlist = cd['objlist']
      self.run = cd['run']
      self.cd = cd
      self.conffile = 'experiment.conf'
      self.warmfile = 'warmup.conf'
      self.vstreamrate = cd['vblksize']*cd['streamrate']
      self.vbuffersize = cd['vblksize']*cd['buffersize']
      self.astreamrate = cd['ablksize']*cd['streamrate']
      self.abuffersize = cd['ablksize']*cd['buffersize']
      return
   def __initClientDict(self):
      result = dict()
      for cl in CLIENTS:
         result[cl] = list()
      return result
   def __generateConfs(self):
      warmup = self.__initClientDict()
      forreal = self.__initClientDict()
      objdist = ZipfGenerator(len(self.objlist),cd['contentalpha'])
      clcount = 0
      clpos = 0
      nextlaunch = int(time.time())+np.random.poisson()
      while clcount < self.clients:
         auxconf = '%s_%d '%(self.name,clcount)
         auxconf += '%d '%nextlaunch
         auxconf += '-P %d '%self.cd['window']
         auxconf += '-b %d '%self.cd['vblksize']
         auxconf += '-m %d '%self.cd['ablksize']
         auxconf += '-V %d '%self.vstreamrate
         auxconf += '-A %d '%self.astreamrate
         auxconf += '-B %d '%self.vbuffersize
         auxconf += '-M %d '%self.abuffersize
         clobj = objdist.next()
         auxconf += '-v %s/%s-video '%(self.ccnprefix,self.objlist[clobj])
         auxconf += '-a %s '%(STATES[clpos])
         auxconf += '-E %s_%d '%(self.name,clcount)
         auxconf += '-R %d'%self.cd['run']
         warmup[CLIENTS[clpos]].append(auxconf)
         clcount += 1
         clpos = (clpos+1)%(len(CLIENTS))
         nextlaunch += np.random.poisson()
      clcount = 0
      clpos = 0
      nextlaunch = int(time.time())+np.random.poisson()
      while clcount < self.clients:
         auxconf = '%s_%d '%(self.name,clcount)
         auxconf += '%d '%nextlaunch
         auxconf += '-P %d '%self.cd['window']
         auxconf += '-b %d '%self.cd['vblksize']
         auxconf += '-m %d '%self.cd['ablksize']
         auxconf += '-V %d '%self.vstreamrate
         auxconf += '-A %d '%self.astreamrate
         auxconf += '-B %d '%self.vbuffersize
         auxconf += '-M %d '%self.abuffersize
         clobj = objdist.next()
         auxconf += '-v %s/%s-video '%(self.ccnprefix,self.objlist[clobj])
         auxconf += '-a %s '%(STATES[clpos])
         auxconf += '-E %s_%d '%(self.name,clcount)
         auxconf += '-R %d'%self.cd['run']
         forreal[CLIENTS[clpos]].append(auxconf)
         clcount += 1
         clpos = (clpos+1)%(len(CLIENTS))
         nextlaunch += np.random.poisson()
      return dict(warmup=warmup, forreal=forreal)
   def deployConfs(self):
      results = self.__generateConfs()
      clients = results['warmup']
      for clk in clients:
         carq = open('/tmp/%s'%self.warmfile, 'w')
         for linha in clients[clk]:
            carq.write('%s\n'%linha)
         carq.close()
         os.system('fab -H %s copy_configuration:/tmp/%s'%(clk,self.warmfile))
      clients = results['forreal']
      for clk in clients:
         carq = open('/tmp/%s'%self.conffile, 'w')
         for linha in clients[clk]:
            carq.write('%s\n'%linha)
         carq.close()
         os.system('fab -H %s copy_configuration:/tmp/%s'%(clk,self.conffile))
      return
   def runWarmUp(self):
      os.system('fab -H %s experiment_relation_streaming:%s,%d,%s'%(genHosts(),self.name,self.run,self.warmfile))
      return
   def runExperiment(self):
      os.system('fab -H %s experiment_relation_streaming:%s,%d,%s'%(genHosts(),self.name,self.run,self.conffile))
      return
   def getResults(self):
      os.system('fab -H %s get_results:%s,%d'%(genHosts(),self.name,self.run))
      return

class ContentFiles:
   def __init__(self, cd):
      self.name = cd['name']
      self.run = cd['run']
      self.relfile = 'relations'
      self.ccnprefix = cd['ccnprefix']
      self.filequant = cd['filequant']
      self.absize = cd['ablksize']
      self.vbsize = cd['vblksize']
      self.blocks = cd['streamsize']
      self.filelist = self.__getFileList()
      return
   def __getFileList(self):
      result = list()
      count = 1
      while count <= self.filequant:
         result.append('%s-run%s-file%s'%(self.name,self.run,count))
         count += 1
      return result
   def __publishMeta(self, obj, rels):
      relpath = '/tmp/%s'%self.relfile
      relarq = open(relpath, 'w')
      for rel in rels:
         relarq.write('%s\t%s\n'%(rel, rels[rel]))
      relarq.close()
      os.system('fab -H %s publish_meta:%s,%s,%s'%(PUBLISHER, relpath, obj, self.relfile))
      return
   def publishFiles(self):
      for fname in self.filelist:
         auxfname = '%s-video'%(fname)
         pvname = '%s/%s'%(self.ccnprefix,auxfname)
         os.system('fab -H %s publish_file:%s,%s,%d,%d'%(PUBLISHER,auxfname,pvname,self.vbsize,self.blocks))
         relations = dict()
         for country in STATES:
            auxfname = '%s-audio-%s'%(fname,country)
            paname = '%s/%s'%(self.ccnprefix,auxfname)
            relations[country] = paname
            os.system('fab -H %s publish_file:%s,%s,%d,%d'%(PUBLISHER,auxfname,paname,self.absize,self.blocks))
         self.__publishMeta(pvname, relations)
      return
   def resetRepo(self):
      os.system('fab -H %s reset_repo'%PUBLISHER)
      return

class Configs:
   def __init__(self,name):
      self.name = name
      self.varparms = dict()
      self.fixparms = dict()
      return
   def addVarParm(self, pname, vlist):
      self.varparms[pname] = vlist
      return
   def addFixParm(self, pname, value):
      self.fixparms[pname] = value
      return
   def __genConfs(self):
      result = dict()
      for vpk in self.varparms:
         if len(result) == 0:
            for value in self.varparms[vpk]:
               rk = '{}_{}_{}'.format(self.name,vpk,value)
               result[rk] = dict()
               result[rk][vpk] = value
         else:
            auxres = dict()
            for oldrk in result:
               for value in self.varparms[vpk]:
                  rk = oldrk + '_{}_{}'.format(vpk,value)
                  auxres[rk] = dict(result[oldrk])
                  auxres[rk][vpk] = value
            result = auxres
      return result
   def __insertFixParms(self,confdict):
      for ck in confdict:
         for pk in self.fixparms:
            confdict[ck][pk] = self.fixparms[pk]
      return
   def getConfigs(self):
      result = self.__genConfs()
      self.__insertFixParms(result)
      for ck in result:
         result[ck]['name'] = ck
      return result

class Main:
   def __init__(self):
      self.__setParameters()
      confdict = self.confs.getConfigs()
      runcount = self.runmin
      while runcount <= self.runmax:
         for cdk in sorted(confdict):
            runconf = dict(confdict[cdk])
            runconf['run'] = runcount
            random.seed(runcount*1000)
            np.random.seed(runcount*1000)
            self.setClock()
            self.setCCNDParms(runconf['ccndcachesize'], runconf['ccndcachestall'])
            cf = ContentFiles(runconf)
            cf.resetRepo()
            cf.publishFiles()
            runconf['objlist'] = cf.filelist
            er = ExperimentRun(runconf)
            er.deployConfs()
            #er.runWarmUp()
            collector = self.__launchCollector(runconf['name'], runconf['run'])
            er.runExperiment()
            self.__termCollector(collector)
            er.getResults()
         runcount += 1
      return
   def __setParameters(self):
      # Um nome para o experimento
      self.confs = Configs('relations')
      # Prefixo CCN para armazenar os arquivos
      self.confs.addFixParm('ccnprefix', 'ccnx:/ufrgs')
      # Número de clientes a serem instanciados (total na rede)
      #self.confs.addVarParm('clients', [26,52,104,208,416,832,1664])
      #self.confs.addVarParm('clients', [x*6 for x in [1, 2, 4, 8, 16]]) # [26,52,78,104,130]
      self.confs.addVarParm('clients', [1, 2, 4, 8, 16])
      # Tamanho do bloco de memória utilizado para o áudio
      self.confs.addFixParm('ablksize', 25*1000)
      # Tamanho do bloco de memória utilizado para o vídeo
      self.confs.addFixParm('vblksize', 350*1000)
      # Tamanho do buffer dos clientes em blocos de memória
      self.confs.addFixParm('buffersize', 10)
      # Taxa do stream em blocos de memória por segundo
      self.confs.addFixParm('streamrate', 1)
      # Tamanho de blocos do arquivo de stream -- usado na hora de gerar os objetos a serem publicados (é o número de blocos)
      self.confs.addFixParm('streamsize', 60)
      # Número de arquivos a serem utilizados no experimento
      self.confs.addVarParm('filequant', [8]) # [24,30,36,42,48,54,60,66] #[42,48,54,60,66]
      # Tamanho do pipeline utilizado pelos clientes
      self.confs.addFixParm('window', 16) #[1,2,4,8,16,32])
      # Tamanho da cache do CCND, em número de chunks -- 192 KB * 60 s * 33 objetos = 380160 KB = 95040 chunks -- 6% = 5702
      self.confs.addFixParm('ccndcachesize', 6000)
      # Tempo para stall dos objetos (segundos)
      self.confs.addFixParm('ccndcachestall', 60)
      # Parametro alpha da distribuicao de conteudos
      self.confs.addFixParm('contentalpha', 2.0)
      # Início das rodadas
      self.runmin = 0
      # Fim das rodadas
      self.runmax = 1
      return
   def setCCNDParms(self, cachesize, staletime):
      tempconf = open('/tmp/ccndrc', 'w')
      tempconf.write('CCND_CAP=%d\n'%cachesize)
      tempconf.write('CCND_DEFAULT_TIME_TO_STALE=%d\n'%staletime)
      tempconf.write('CCND_MAX_TIME_TO_STALE=%d\n'%staletime)
      tempconf.close()
      os.system('fab -H %s insert_ccndrc'%(genHosts()))
      os.system('fab -H %s insert_ccndrc'%(PUBLISHER))
      os.system('python asgardscripts/ccnd.py start')
      return
   def setClock(self):
      os.system('fab -H %s update_clock'%(genHosts()))
      os.system('fab -H %s update_clock'%(PUBLISHER))
      return
   def __launchCollector(self, name, run):
      args = 'python getRouterData.py %s %d 1'%(name,run)
      self.collog = open('collector.log', 'a')
      collector = sp.Popen(args, shell=True, stdout=self.collog)
      return collector
   def __termCollector(self, collector):
      collector.terminate()
      self.collog.close()
      return

if __name__ == '__main__': Main()

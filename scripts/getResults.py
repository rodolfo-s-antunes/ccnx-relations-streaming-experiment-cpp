#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import numpy as np
import scipy as sp
import scipy.stats as sps

            
#***************************           
# funções globais
#***************************

def nanos2millis(time):
    return float(time)/1000000.0

#***************************           
# stats
#***************************

class Stats():
    
    @staticmethod
    def average(vector):
        if len(vector) == 0:
            return 0
        else:
            data = np.array(vector)
            return np.average(data)
        
    @staticmethod
    def stdDeviation(vector):
            if len(vector) == 0:
                return 0
            else:
                data = np.array(vector)
                return np.std(data)
            
    @staticmethod
    def stdConfInt(vector, confidence=0.95):
        if len(vector) == 0:
            return 0
        else: 
            data = np.array(vector)
            m = np.mean(data)
            return sp.stats.sem(data) * sps.t._ppf((1.0+confidence)/2.0, len(data)-1)

#***************************
# Experiment      
#***************************  

class Experiment():
    
    def __init__(self, name):
        self.name = name
        self.executions = []
        self.stalls = []
        self.bufferingtime = []
        self.numberofstalls = []
        #self.recovered = []
        
    def addExecution(self, execution):
        self.executions.append(execution)
    
    def setVectors(self):
        self.setBufferingTimeVector()
        self.setStallsVector()
        self.setNumberOfStallsVector()
        #self.setRecoveredVector()
            
    def setBufferingTimeVector(self):
        self.bufferingtime = []
        for execution in self.executions:
            self.bufferingtime = self.bufferingtime + execution.setBufferingTimeVector()   
        return self.bufferingtime           
        
    def setStallsVector(self):
        self.stalls = []
        for execution in self.executions:
            self.stalls = self.stalls + execution.setStallsVector()
        return self.stalls
    
    def setNumberOfStallsVector(self):
        self.numberofstalls = []
        for execution in self.executions:
            self.numberofstalls = self.numberofstalls + execution.setNumberOfStallsVector()
        return self.numberofstalls
    
#    def setRecoveredVector(self):
#        self.recovered = []
#        for execution in self.executions:
#            self.recovered = self.recovered + execution.setRecoveredVector()
#        return self.recovered
    
        
#***************************
# Execution      
#***************************  

class Execution():
    
    def __init__(self, name):
        self.name = name
        self.servers = []
        self.stalls = []
        self.bufferingtime = []
        self.numberofstalls = []
        #self.recovered = []
        
    def addServer(self, server):
        self.servers.append(server)

    def setBufferingTimeVector(self):
        self.bufferingtime = []
        for server in self.servers:
            self.bufferingtime = self.bufferingtime + server.getBufferingTimeVector()                
        return self.bufferingtime 
    
    def setStallsVector(self):
        if len(self.stalls) < 1:
            for server in self.servers:
                self.stalls = self.stalls + server.getStallsVector()
        return self.stalls
    
    def setNumberOfStallsVector(self):
        self.numberofstalls = []
        for server in self.servers:
            self.numberofstalls.append(server.getNumberOfStalls())
        return self.numberofstalls
    
#    def setRecoveredVector(self):
#        self.recovered = []
#        for server in self.servers:
#            self.recovered = self.recovered + server.getRecoveredVector()
#        return self.recovered

#***************************
# Server      
#***************************  

class Server():

    def __init__(self, name):
        self.name = name
        self.clientscount = 0
        self.stalls = []
        self.bufferingtime = []
        #self.recovered = []
        
    def appendStallOccurrence(self, duration):
        self.stalls.append(duration)  
    
    def appendBufferingTime(self, duration):
        self.bufferingtime.append(duration) 
    
    def appendRecoveredDuration(self, duration):  
        self.recovered.append(duration)   
        
    def getBufferingTimeVector(self):
        return self.bufferingtime
    
    def getStallsVector(self):
        return self.stalls
    
    def getNumberOfStalls(self):
        return float(len(self.stalls))
    
#    def getRecoveredVector(self):
#        return self.recovered

#***************************
# Main      
#***************************     
   
class Main():
    def __init__(self):
        self.experiments = {}
        self.setStructure()
    
    def setStructure(self):
        #percorre a hierarquia de pastas e cria uma estrutura para armazená-la
        #lê dados de cada cliente
        
        # experiment = basico-720-cln12-flq2 
        # execution = 1
        # server = ccn_ac
        
        for experiment in os.listdir('results'):
            if experiment[0:5].find("teste") != -1:
                currentexperiment = Experiment(experiment)
                self.experiments[experiment] = currentexperiment
                for execution in os.listdir('results/%s' %experiment):
                    if execution[0] != '.':
                        currentexecution = Execution(execution)
                        currentexperiment.addExecution(currentexecution)
                        for server in os.listdir('results/%s/%s' %(experiment, execution)):
                            if server[0] != '.':
                                currentserver = Server(server)
                                currentexecution.addServer(currentserver)
                                for file in os.listdir('results/%s/%s/%s' %(experiment, execution, server)):
                                    if (file[-3:] == "out"):
                                        output = self.getClientsOutput('results/%s/%s/%s' %(experiment, execution, server), file)
                                        self.processClientsOutput(currentserver, output)
                currentexperiment.setVectors() 
        print self.experiments
        self.generateOutput()

#         #buffering time
#         print("\n\t\t\t\t\t buffering avg \t buffering std dev \t buffering conf int")    
#         for ke in sorted(self.experiments):
#             currentexperiment = self.experiments[ke]
#             print("* %s * \t %3.2f \t %3.2f \t\t %3.2f " %(currentexperiment.name, Stats.average(currentexperiment.bufferingtime), Stats.stdDeviation(currentexperiment.bufferingtime), Stats.stdConfInt(currentexperiment.bufferingtime)))
#                   
#          #stall - time
#         print("\n\t\t\t\t\t stall avg \t stall std dev \t stall std conf int")              
#         for ke in sorted(self.experiments):
#             currentexperiment = self.experiments[ke]
#             print("* %s * \t %3.2f  \t %3.2f \t %3.2f" %(currentexperiment.name, Stats.average(currentexperiment.stalls), Stats.stdDeviation(currentexperiment.stalls), Stats.stdConfInt(currentexperiment.stalls)))
#               
#          #stall - number
#         print("\n\t\t\t\t\t no stalls avg \t no of stalls std dev \t no of stalls std conf int")              
#         for ke in sorted(self.experiments):
#             currentexperiment = self.experiments[ke]
#             print("* %s *\t %6.2f  %12.2f %23.2f" %(currentexperiment.name, Stats.average(currentexperiment.numberofstalls), Stats.stdDeviation(currentexperiment.numberofstalls), Stats.stdConfInt(currentexperiment.numberofstalls)))

    def getClientsOutput(self, path, file):
        try: 
            f = open(path+"/"+file, 'r')
            lines = f.readlines()
            f.close()
            return lines     
        except IOError:
            print("Error: could not find output file %s in dir %s"%(file,path))
    
    def processClientsOutput(self, server, lines):
        for line in lines:
            words = line.split()
            if line.find("objname=") != -1:
                server.clientscount += 1
                primeiro = True
            elif line.find("Waiting time until filled") != -1:
                if primeiro:
                    server.appendBufferingTime(float(words[6]))
                    primeiro = False
                else:
                    server.appendStallOccurrence(float(words[6]))
            #elif line.find("recovered") != -1:
                #server.appendRecoveredDuration(nanos2millis(words[5]))
            elif line.find("End.") != -1:
                return  
        
    def generateOutput(self):                 
        #stall     
        stallsdict = dict()             
        for ke in self.experiments:
            statsdict = dict()
            statsdict['avg'] = Stats.average(self.experiments[ke].stalls)
            statsdict['stddev'] = Stats.stdDeviation(self.experiments[ke].stalls) 
            statsdict['conf'] = Stats.stdConfInt(self.experiments[ke].stalls)
            stallsdict[ke] = statsdict
        self.generateResultFilePerUsers("stall_duration", stallsdict)    
        
        #buffering     
        bufferingdict = dict()             
        for ke in self.experiments:
            statsdict = dict()
            statsdict['avg'] = Stats.average(self.experiments[ke].bufferingtime)
            statsdict['stddev'] = Stats.stdDeviation(self.experiments[ke].bufferingtime) 
            statsdict['conf'] = Stats.stdConfInt(self.experiments[ke].bufferingtime)
            bufferingdict[ke] = statsdict
        self.generateResultFilePerUsers("buffering", bufferingdict)
        
        #number of stalls     
        numberofstallsdict = dict()             
        for ke in self.experiments:
            statsdict = dict()
            statsdict['avg'] = Stats.average(self.experiments[ke].numberofstalls)
            statsdict['stddev'] = Stats.stdDeviation(self.experiments[ke].numberofstalls) 
            statsdict['conf'] = Stats.stdConfInt(self.experiments[ke].numberofstalls)
            numberofstallsdict[ke] = statsdict
        self.generateResultFilePerUsers("number_of_stalls", numberofstallsdict)
        return    
        
#        #recovered     
#         recovereddict = dict()                        
#         for ke in sorted(self.experiments):
#             statsdict = dict()
#             statsdict['avg'] = Stats.average(self.experiments[ke].recovered)
#             statsdict['stddev'] = Stats.stdDeviation(self.experiments[ke].recovered) 
#             statsdict['conf'] = Stats.stdConfInt(self.experiments[ke].recovered)
#             recovereddict[ke] = statsdict
#         self.generateResultFile("recovered", recovereddict)  

    #exemplo de nome: defaultum_filequant_33_clients_104

    def generateResultFilePerUsers(self, varname, dd, convmb=False):
      orgd = dict()
      for ek in dd: # ek = defaultX_filequant_Y_clients_Z
         auxQ = ek.split('_')
         exp = '%s'%(auxQ[0])   # exp = defaultX
         cln = int(auxQ[4])
         flq = int(auxQ[2])
         if exp not in orgd: orgd[exp] = dict()
         if flq not in orgd[exp]: orgd[exp][flq] = dict()
         orgd[exp][flq][cln] = dd[ek]
      for ek in orgd:   # orgd[ek] = <exp> = defaultX
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

    def generateResultFilePerFiles(self, varname, dd, convmb=False):
      orgd = dict()
      for ek in dd:
         auxQ = ek.split('_')
         exp = '%s'%(auxQ[0])
         cln = int(auxQ[4])
         flq = int(auxQ[2])
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
        
    def b2mb(self, value): return float(value)/1048576.0
                      
if __name__ == "__main__": Main() 

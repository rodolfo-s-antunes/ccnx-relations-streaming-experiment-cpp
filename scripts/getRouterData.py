#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys, os, time
from datetime import datetime as dt
import xml.etree.cElementTree as et
import urllib2 as url
import psycopg2

STATES = ['pub', 'uk', 'nl', 'es', 'de', 'fr', 'it']
ROUTERS = ['bte_%s'%i for i in STATES]
URLTEMPLATE = 'http://%s:9695/?f=xml'
DBHOST = 'localhost'
DBPORT = 5432
DBUSER = 'gticn'
DBPASS = 'gticn'
DBDB = 'results'

class RouterXMLParser():
   def __init__(self):
      pass
   def getrouterdata(self, routername):
      try:
         urlinput = url.urlopen(URLTEMPLATE%routername)
         raw = urlinput.read()
         urlinput.close()
         data = self.parse(routername, raw)
      except Exception, e:
         data = None
         print e
      return data
   def parse(self, routername, data):
      result = dict(routername=routername)
      root = et.XML(data)
      self.parseidentity(root.find('identity'), result)
      self.parsegeneric(root, 'cobs', result)
      self.parsegeneric(root, 'interests', result)
      self.parsefaces(root.find('faces'), result)
      return result
   def parseidentity(self, element, data):
      unixstart = element.find('starttime').text
      unixnow = element.find('now').text
      fs = '%Y-%m-%d %H:%M:%S'
      dtstart = dt.fromtimestamp(float(unixstart))
      dtnow = dt.fromtimestamp(float(unixnow))
      data['starttime'] = dtstart.strftime(fs)
      data['nowtime'] = dtnow.strftime(fs)
      return
   def parsegeneric(self, root, ename, data):
      element = root.find(ename)
      for child in element.getchildren():
         data['%s_%s'%(ename,child.tag)] = child.text
      return
   def parsefaces(self, element, data):
      data['faces'] = dict()
      for eface in element.getchildren():
         eip = eface.find('ip')
         emeters = eface.find('meters')
         if (eip!=None) and (emeters!=None):
            facedata = dict()
            for emname in emeters.getchildren():
               for emdata in emname.getchildren():
                  facedata['%s_%s'%(emname.tag, emdata.tag)] = emdata.text
            data['faces'][eip.text] = facedata
      return

class DBManager():
   def __init__(self):
      self.con = psycopg2.connect(host=DBHOST, user=DBUSER, password=DBPASS, dbname=DBDB, port=DBPORT)
      return
   def savedata(self, experiment, run, coltime, data):
      baseid = self.saverouterinfo(experiment, run, coltime, data)
      self.savefaceinfo(baseid, data['faces'])
      return
   def commitdata(self):
      self.con.commit()
      return
   def saverouterinfo(self, experiment, run, ct, d):
      basequery = "insert into routerinfo (experiment, run, routername, collecttime, routertime, cobs_accessioned, cobs_duplicate, cobs_sent, cobs_sparse, cobs_stale, cobs_stored, interests_accepted, interests_dropped, interests_names, interests_noted, interests_pending, interests_propagating, interests_sent, interests_stuffed) values ('%s', %s, '%s', '%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning id;"
      basedata = (experiment, run, d['routername'], ct, d['nowtime'], d['cobs_accessioned'], d['cobs_duplicate'], d['cobs_sent'], d['cobs_sparse'], d['cobs_stale'], d['cobs_stored'], d['interests_accepted'], d['interests_dropped'], d['interests_names'], d['interests_noted'], d['interests_pending'], d['interests_propagating'], d['interests_sent'], d['interests_stuffed'])
      cur = self.con.cursor()
      auxres = cur.execute(basequery%basedata)
      lastrow = cur.fetchone()[0]
      cur.close()
      return lastrow
   def savefaceinfo(self, basedataid, faces):
      basequery = "insert into faceinfo (routerid, addr, bytein_persec, bytein_total, byteout_persec, byteout_total, datain_persec, datain_total, dataout_persec, dataout_total, intrin_persec, intrin_total, introut_persec, introut_total) values(%s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');"
      cur = self.con.cursor()
      for fname in sorted(faces):
         f = faces[fname]
         basedata = (basedataid, fname, f['bytein_persec'], f['bytein_total'], f['byteout_persec'], f['byteout_total'], f['datain_persec'], f['datain_total'], f['dataout_persec'], f['dataout_total'], f['intrin_persec'], f['intrin_total'], f['introut_persec'], f['introut_total'])
         cur.execute(basequery%basedata)
      cur.close()
      return

class Main():
   def __init__(self):
      self.name = sys.argv[1]
      self.run = sys.argv[2]
      self.collectinterval = float(sys.argv[3])
      print 'experiment=%s run=%s interval=%.2f'%(self.name, self.run, self.collectinterval)
      self.rxp = RouterXMLParser()
      self.dbm = DBManager()
      self.collectloop()
      return
   def collectloop(self):
      while True:
         before = time.time()
         self.collectonce()
         after = time.time()
         sleepint = (before+self.collectinterval)-after
         if sleepint > 0:
            print 'Sleeping for %.4f seconds...'%sleepint
            time.sleep(sleepint)
      return
   def collectonce(self):
      for router in ROUTERS:
         data = self.rxp.getrouterdata(router)
         coltime = dt.now().strftime('%Y-%m-%d %H:%M:%S')
         if data != None:
            self.dbm.savedata(self.name, self.run, coltime, data)
            print '%s - collected data from %s'%(coltime, router)
         else:
            print '%s - ERROR collecting data from %s'%(coltime, router)
      self.dbm.commitdata()
      return
   def printrouterdata(self, data):
      for dkey in sorted(data):
         if dkey != "faces":
            print "%s -> %s"%(dkey, data[dkey])
      print '\nFACES:'
      for fkey in sorted(data['faces']):
         print '* %s'%fkey
         dface = data['faces'][fkey]
         for dkey in sorted(dface):
            print '%s -> %s'%(dkey, dface[dkey])
      return

if __name__ == '__main__': Main()

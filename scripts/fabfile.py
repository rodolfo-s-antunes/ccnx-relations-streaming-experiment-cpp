#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
from datetime import datetime
from fabric.api import local, sudo, get, put, run, env, settings, parallel, hosts
from fabric.context_managers import cd

env.user = 'gticn'
env.password = 'gticn'

def prepare_workspace():
   run('rm -rf workspace')
   run('mkdir workspace')
   run('mkdir workspace/CppRelations')
   run('mkdir workspace/CppRelations/src')
   run('mkdir workspace/CppRelations/scripts')

def copy_scripts():
   put('/home/gticn/workspace/CppRelations/scripts/*.py', '/home/gticn/workspace/CppRelations/scripts/', mirror_local_mode=True)
   put('/home/gticn/workspace/CppRelations/scripts/*.sh', '/home/gticn/workspace/CppRelations/scripts/', mirror_local_mode=True)

def copy_experiment():
   put('/home/gticn/workspace/CppRelations/src/*.cpp', '/home/gticn/workspace/CppRelations/src/', mirror_local_mode=True)
   put('/home/gticn/workspace/CppRelations/src/*.h', '/home/gticn/workspace/CppRelations/src/', mirror_local_mode=True)
   put('/home/gticn/workspace/CppRelations/*.cpp', '/home/gticn/workspace/CppRelations/', mirror_local_mode=True)
   put('/home/gticn/workspace/CppRelations/Makefile', '/home/gticn/workspace/CppRelations/', mirror_local_mode=True)

def compile_experiment():
   with cd('workspace/CppRelations'):
      run('make')

@parallel
def experiment_basic_streaming(basename, runnumber, conffile):
   parms = '%s %s %s'%(basename, runnumber, conffile)
   run('python workspace/CppRelations/scripts/run_basic_streaming.py %s'%parms)

@parallel
def experiment_relation_streaming(basename, runnumber, conffile):
   parms = '%s %s %s'%(basename, runnumber, conffile)
   run('python workspace/CppRelations/scripts/run_relation_streaming.py %s'%parms)

#@roles('publisher')
def reset_repo():
   with cd('rsantunes_temp'):
      with settings(warn_only=True):
         run('rm -f *')
   with cd('rsantunes_repo'):
      with settings(warn_only=True):
         run('rm -r *')
      local('ssh bte_pub sh workspace/CppRelations/scripts/start_repo.sh')

'''
#@roles('publisher')
def basic_files(name, ccnprefix, bs, blocks, quant):  # bs * blocks = tamanho total do objeto
   with cd('rsantunes_temp'):
      count = 1
      while (count <= int(quant)):
         fname = '%s-%s'%(name,count)  #nome do arquivo local
         pname = '%s/%s'%(ccnprefix,fname)   #nome do arquivo no ccnx
         run('dd if=/dev/urandom of=%s bs=%s count=%s'%(fname, bs, blocks))
         run('ccnputfile %s %s'%(pname, fname))
         count += 1

#@roles('publisher')
def relation_files(name, aobjs, sobjs, ccnprefix, vbsize, absize, sbsize, blocks):
   # para cada vídeo, publica ele e os objetos de áudio e de legenda relacionados
   with cd('rsantunes_temp'):
      alist = aobjs.split(':')
      slist = sobjs.split(':')
      vfname = '%s-video'%(name)
      vpname = '%s/%s'%(ccnprefix,vfname)
      run('dd if=/dev/urandom of=%s bs=%s count=%s'%(vfname, vbsize, blocks))
      run('ccnputfile %s %s'%(vpname, vfname))
      arqr = open('/tmp/temp-relations', 'w')
      for aobj in alist:
         fname = '%s-audio-%s'%(name,aobj)
         pname = '%s/%s'%(ccnprefix,fname)
         arqr.write('%s\t%s\n'%(aobj,pname))
         run('dd if=/dev/urandom of=%s bs=%s count=%s'%(fname, absize, blocks))
         run('ccnputfile %s %s'%(pname, fname))
      for sobj in slist:
         fname = '%s-subtitle-%s'%(name,sobj)
         pname = '%s/%s'%(ccnprefix,fname)
         arqr.write('%s\t%s\n'%(sobj,pname))
         run('dd if=/dev/urandom of=%s bs=%s count=%s'%(fname, sbsize, blocks))
         run('ccnputfile %s %s'%(pname, fname))
      arqr.close()
      put('/tmp/temp-relations', 'temp-relations')
      run('ccnputmeta %s %s %s'%(vpname, 'relations', 'temp-relations'))      
'''

def publish_meta(fname, obj, metaname): #metaname = relations
   with cd('rsantunes_temp'):
      put(fname, '.')
      auxname = fname.split('/')[-1]
      run('ccnputmeta %s %s %s'%(obj, metaname, auxname))

def publish_meta2(obj, vcount, metaname): #metaname = relations
   with cd('rsantunes_temp'):
      put('/tmp/temp-relations-%s'%(vcount), 'temp-relations-%s'%(vcount))
      run('ccnputmeta %s %s %s'%(obj, metaname, 'temp-relations-%s'%(vcount)))

def publish_file(fname, pname, bsize, blocks):
   with cd('rsantunes_temp'):
      run('dd if=/dev/urandom of=%s bs=%s count=%s'%(fname, bsize, blocks))
      run('ccnputfile %s %s'%(pname, fname))

def insert_ccndrc():
  put('/tmp/ccndrc', '.ccnx/ccndrc')

def get_results(name, runnumber):
   get('%s-%s.out'%(name, runnumber), 'results/%s/%s'%(name,runnumber)+'/%(host)s/%(basename)s')
   get('%s-%s.err'%(name, runnumber), 'results/%s/%s'%(name,runnumber)+'/%(host)s/%(basename)s')

def copy_configuration(filename='/tmp/experiment.conf'):
   put(filename)

def temp():
  with settings(warn_only=True):
    sudo('rm -rf /progs/ccnx-0.7.0*')
    sudo('rm -rf /progs/pyccn')

def aptitude_full_upgrade():
   sudo('aptitude update')
   sudo('aptitude full-upgrade')
   sudo('aptitude clean')

def network_control(parm='start'):
  sudo('bash network.sh ' + parm)

def ccnd_status():
  run('ccndstatus')

def get_ip():
   run('ifconfig | grep "inet addr:143.54"')

def update_clock():
   now = datetime.now().strftime('%m%d%H%M%Y.%S')
   sudo('date %s'%now)

def ps(process='ccnr'):
  run('ps -ef | grep "%s"'%process)

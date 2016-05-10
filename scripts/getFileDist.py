#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, math

class RawData:
	def __init__(self, dp):
		self.__getData(dp)
		return
	def __procOut(self, an, res):
		arq = open(an, 'r')
		for linha in arq:
			if linha.find('objname') >= 0:
				Q = linha.strip().split()
				if Q[1][:7] == 'objname':
					Qo = Q[1].split('-')
					df = Qo[-2]+'-'+Qo[-1]
					if df not in res:
						res[df] = 1
					else:
						res[df] += 1
				elif Q[2][:7] == 'objname':
					Qvo = Q[2].split('-')
					dfv = Qvo[-2]+'-'+Qvo[-1]
					if dfv not in res:
						res[dfv] = 1
					else:
						res[dfv] += 1
					aid = Q[3][-2:]
					dfa = Qvo[-2]+'-audio-'+aid
					if dfa not in res:
						res[dfa] = 1
					else:
						res[dfa] += 1
		arq.close()
		return
	def __prettyPrint(self, fd):
		for w in sorted(fd, key=fd.get, reverse=True):
			print w, fd[w]
		return
	def __getData(self, dp):
		auxr = dict()
		for exp in os.listdir(dp):
			if exp not in auxr: auxr[exp] = dict()
			for run in os.listdir(dp+'/'+exp):
				if run not in auxr[exp]: auxr[exp][run] = dict()
				rp = dp+'/'+exp+'/'+run
				rrun = dict()
				for router in os.listdir(rp):
					for arq in os.listdir(rp+'/'+router):
						if arq[-4:] == '.out':
							ap = rp+'/'+router+'/'+arq
							self.__procOut(ap, rrun)
				print str.format('exp={},run={}', exp, run)
				self.__prettyPrint(rrun)
		return

class Main:
	def __init__(self):
		rd = RawData('.')
		return

if __name__ == '__main__': Main()
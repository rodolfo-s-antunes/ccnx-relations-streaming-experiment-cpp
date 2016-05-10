#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os

# Esta lista contém o nome dos clientes na ordem em que eles serão
# preenchidos. Esta ordem segue a ideia de distribuir os clientes
# em largura dentro da árvore de transmissão centrada em MG.
#STATES = ['mg', 'ce', 'df', 'sp', 'ba', 'ma', 'rn', 'go', 'rj', 'am', 'pr', 'rr', 'sc', 'es', 'se', 'pa', 'pb', 'mt', 'to', 'ms', 'rs', 'al', 'ap', 'pi', 'ro', 'pe', 'ac']
STATES = ['pub', 'de', 'it', 'fr', 'nl', 'uk', 'es']
CLIENTS = ['bte_'+x for x in STATES]

def genHosts():
	result = ""
	for cl in CLIENTS:
		result += "%s,"%cl
	return result[:-1]

def prepare_workspace():
	os.system('fab -H %s prepare_workspace'%genHosts())
	os.system('fab -H %s copy_scripts'%genHosts())
	os.system('fab -H %s copy_experiment'%genHosts())
	os.system('fab -H %s compile_experiment'%genHosts())
	return

def run_command(command):
   os.system('fab -H %s %s'%(genHosts(),command))
   return

def main():
	if len(sys.argv) == 1:
		prepare_workspace()
	else:
		run_command(sys.argv[1])
	return

if __name__ == '__main__': main()

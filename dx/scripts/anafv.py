#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil
from iktool import iktool

g_iu = ikutil()
g_tool = iktool()

class anafv:
    def __init__(self):
        g_tool.conn('dx')

    def __del__(self):
        pass

    def runana(self):
        lpcnt = g_tool.exesqlone('select count(*) from dx.iknow_base where nlp=1',None)
        #hpcnt = g_tool.exesqlone('select count(*) from dx.iknow_base where nhp=1',None)
        fvs = g_tool.exesqlbatch('select distinct fv from dx.iknow_base order by fv',None)
        mat = []
        ofn = os.path.join(g_home,'fvlpk.csv')
        for fv in fvs:
            print 'handling fv[%s]....'%fv[0]
            fvcnt = g_tool.exesqlone('select count(*) from dx.iknow_base where fv=%s',(fv[0],))
            fvlpcnt = g_tool.exesqlone('select count(*) from dx.iknow_base where fv=%s and nlp=1 and nk=1',(fv[0],))
            #fvhpcnt = g_tool.exesqlone('select count(*) from dx.iknow_base where fv=%s and nhp=1',(fv[0],))
            mat.append((fv[0],lpcnt[0],fvcnt[0],fvlpcnt[0],float(fvlpcnt[0])/float(fvcnt[0])))
        g_iu.dumpfile(ofn,mat)
            
if __name__ == "__main__":
    anafv().runana()
    
    
    
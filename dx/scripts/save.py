#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import urllib2
import socket
import MySQLdb
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil
from iktool import iktool

g_iu = ikutil()
g_tool = iktool()

if __name__ == "__main__":
    g_tool.conn('dx')
    dir = os.path.join(os.path.join(g_home,'tmp','save'))
    g_iu.mkdir(dir)
    codes = g_tool.exesqlbatch('select distinct code from dx.iknow_data',None)
    total = float(len(codes))
    count = 0
    for i in range(len(codes)):
        code = codes[i][0]
        ofn = os.path.join(dir,'%s.csv'%code)
        data = g_tool.exesqlbatch('select code,date,open,high,low,close,volh,volwy from dx.iknow_data where code=%s order by date',(code,))
        g_iu.dumpfile(ofn,data)
        g_iu.log(logging.INFO,'save handle progress[%0.2f%%]'%(100*((i+1)/total)))
    g_iu.log(logging.INFO,'save handle done')
        
            
            
        
        


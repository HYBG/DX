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
    dir = os.path.join(g_home,'tmp')
    #info = g_tool.exesqlbatch('select code,name,boardcode,boardname from hy.iknow_name',None)
    info = g_tool.exesqlbatch('select code,name from dx.iknow_name where code not in (select code from hs.hs_name)',None)
    total = float(len(info))
    count = 0
    for i in range(len(info)):
        sqls = []
        line = info[i]
        #sqls.append(('insert into dx.iknow_name(code,name,bdcode,bdname) values(%s,%s,%s,%s)',(line[0],line[1],line[2],line[3])))
        sqls.append(('insert into hs.hs_name(code,name) values(%s,%s)',(line[0],line[1])))
        #data = g_tool.exesqlbatch('select code,date,open,high,low,close,volh,volwy from hy.iknow_data where code=%s',(line[0],))
        #for row in data:
        #    sqls.append(('insert into dx.iknow_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',row))
        g_tool.task(sqls)
        print 'execute insert sqls[%d]....'%len(sqls)
        #g_iu.log(logging.INFO,'move data from hy to dx progress[%0.2f%%]--%d'%(100*((i+1)/total),count+len(sqls)))
        #count = count+len(sqls)
            
            
        
        


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
from bs4 import BeautifulSoup
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil
from iktool import iktool

g_iu = ikutil()
g_tool = iktool()


if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-c', '--code', action='store', dest='code',default=None, help='code')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)
        
    g_tool.conn('hy')
    mat = []
    if ops.code:
        data = g_tool.exesqlbatch('select date,k,d,macd from hy.iknow_attr where code=%s order by date',(ops.code,))
        kdrp = None
        macdrp = None
        for i in range(1,len(data)):
            date = data[i][0]
            kds = data[i][1]-data[i][2]
            kdpress = False
            if data[i][1]<data[i][2] and data[i-1][1]<data[i-1][2] and data[i][2]-data[i][1]<2:
                kdpress = True
            macds = data[i][3]-data[i-1][3]
            close = g_tool.exesqlone('select close from hy.iknow_data where code=%s and date=%s',(ops.code,date))
            close = close[0]
            macdr = round(data[i][3]/close,4)
            if macdrp:
                macdrs = macdr-macdrp
                risky = False
                if macdr < 0.002:
                    risky = True
                mat.append((date,close,macds,macdrs,risky,kdpress))
            macdrp = macdr
        fn = os.path.join(os.path.join(g_home,'bin'),'%s.csv'%ops.code)
        g_iu.dumpfile(fn,mat)
        
        cash = 1000000
        readybuy = True
        readysell = False
        pay = 0.0
        hold = 0
        mat.sort()
        for row in mat:
            #if row[0]<'2016-01-01':
            #    continue
            close = row[1]
            risky = row[4]
            kdpress = row[5]
            #print 'date[%s] kd[%0.4f] kdrs[%0.4f]'%(row[0],row[2],row[3])
            if (row[2]>0 and row[3]>0) and (not risky) and (not kdpress) and readybuy:
                hold = (int((cash/close)/100))*100
                left = cash - hold*close*1.0003
                while left<0:
                    hold = hold-100
                    left = cash - hold*close*1.0003
                cash = left
                pay = hold*close*1.0003
                readysell = True
                readybuy = False
                print 'date[%s] buy[%d] price[%0.2f] cash[%0.4f] value[%0.4f]'%(row[0],hold,close,cash,hold*close+cash)
            elif (row[2]<0 or row[3]<0) and readysell:
                get = hold*close*0.9987
                cash = cash + get
                print 'date[%s] sell[%d] price[%0.2f] cash[%0.4f] benerfit[%0.4f]'%(row[0],hold,close,cash,get-pay)
                hold = 0
                pay = 0.0
                readysell = False
                readybuy = True
        
            
            
        
        
        
        
        
        
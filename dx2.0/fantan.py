#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import random
import socket
import urllib2
import commands
import random
from datetime import timedelta
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
import MySQLdb
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil
from iktool import iktool

g_iu = ikutil()
g_tool = iktool()

class hyfantan:
    def __init__(self):
        g_tool.conn('hy')
        self._logger = g_iu.createlogger('hyfantan',os.path.join(os.path.join(g_home,'log'),'hyfantan.log'),logging.INFO)

    def __del__(self):
        pass

    def _codes(self):
        ld = g_tool.exesqlone('select date from hy.iknow_data order by date desc limit 1',None)
        ld = ld[0]
        data = g_tool.exesqlbatch('select distinct code from hy.iknow_data where date=%s',(ld,))
        codes = []
        for row in data:
            codes.append(row[0])
        return codes
        
    def fantan(self,thv):
        codes = self._codes()
        for code in codes:
            data = g_tool.exesqlbatch('select k,d,mid,std from hy.iknow_bollkd where code=%s order by date desc limit 2',(code,))
            if len(data)<2:
                continue
            if data[0][0]>data[0][1] and data[1][0]<data[1][1]:
                base = g_tool.exesqlone('select close from hy.iknow_data where code=%s order by date desc limit 1',(code,))
                close = base[0]
                up = data[0][2]+2*data[0][3]
                dn = data[0][2]-2*data[0][3]
                score = 100*((close-dn)/(up-dn))
                if score<thv:
                    print 'code[%s] price[%0.2f] score[%0.2f]'%(code,close,score)

    def baofa(self):
        codes = self._codes()
        for code in codes:
            data = g_tool.exesqlbatch('select k,d,mid,std from hy.iknow_bollkd where code=%s order by date desc limit 2',(code,))
            if len(data)<2:
                continue
            if data[0][0]>data[0][1] and data[0][1]>70:
                base = g_tool.exesqlbatch('select close from hy.iknow_data where code=%s order by date desc limit 2',(code,))
                close = base[0][0]
                yclose = base[1][0]
                up = data[0][2]+2*data[0][3]
                dn = data[0][2]-2*data[0][3]
                yup = data[1][2]+2*data[1][3]
                ydn = data[1][2]-2*data[1][3]
                if close>up and yclose <yup:
                    print 'code[%s] price[%0.2f]'%(code,close)

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-f', '--fantan', action='store_true', dest='fantan',default=False, help='fantan mode')
    parser.add_option('-b', '--baofa', action='store_true', dest='baofa',default=False, help='baofa mode')
    parser.add_option('-t', '--threshold', action='store', dest='threshold',type='float',default=None, help='threshold boll')


    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    ik = hyfantan()
    if ops.fantan and ops.threshold:
        ik.fantan(ops.threshold)
    if ops.baofa:
        ik.baofa()
            
            
        

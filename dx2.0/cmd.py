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
    parser.add_option('-v', '--fv', action='store', dest='fv',default=None, help='fv')
    parser.add_option('-r', '--vr', action='store', dest='vr',type='float',default=None, help='vr')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)
        
    vr = 1.0
    if ops.vr:
        vr = ops.vr

    if ops.fv:
        g_tool.conn('hy')
        data = g_tool.exesqlbatch('select code,date,next from hy.iknow_feature where fv=%s',(ops.fv,))
        all1 = float(len(data))
        all2 = 0.0
        dic1 = {1:0,2:0,3:0,4:0,5:0,6:0,7:0,8:0}
        dic2 = {1:0,2:0,3:0,4:0,5:0,6:0,7:0,8:0}
        for row in data:
            code = row[0]
            date = row[1]
            next = row[2]
            dic1[next] = dic1[next]+1
            vol = g_tool.exesqlone('select iknow_data.volwy,iknow_attr.vol5 from iknow_data,iknow_attr where iknow_data.code=%s and iknow_data.date=%s and iknow_attr.code=%s and iknow_attr.date=%s',(code,date,code,date))
            if float(vol[0])/(float(vol[1])/5.0)>vr:
                dic2[next] = dic2[next]+1
                all2 = all2 + 1.0
        mat1 = []
        mat2 = []
        for i in range(1,9):
            mat1.append(round(100*(dic1[i]/all1),2))
            mat2.append(round(100*(dic2[i]/all2),2))
        print mat1
        print mat2
            
             
        
    
    
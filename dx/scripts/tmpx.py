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
from bs4 import BeautifulSoup
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil

g_iu = ikutil()


if __name__ == "__main__":
    fn = '/var/data/iknow/tmp/000001.csv'
    data = g_iu.loadcsv(fn)
    mat = []
    for i in range(1,len(data)):
        print 'dealing with line[%d]....'%i
        code = data[i][1][1:]
        date = data[i][0]
        #name = data[i][2]
        open = data[i][6]
        high = data[i][4]
        low = data[i][5]
        close = data[i][3]
        volh = float(data[i][7])/100.0
        volwy = 0
        if not data[i][8]=='None':
            volwy = float(data[i][8])/10000.0
        mat.append((code,date,open,high,low,close,volh,volwy))
    g_iu.dumpfile('./zs_tmp.csv',mat)
        

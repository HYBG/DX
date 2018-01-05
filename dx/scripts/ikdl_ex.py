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


class ikdlex:
    def __init__(self):
        self._conf = g_iu.loadcsv(os.path.join(os.path.join(g_home,'etc'),'code_dl.csv'),{},0)
        self._lastdl = None
    
    def __del__(self):
        pass
        
    def _reload(self):
        self._conf = g_iu.loadcsv(os.path.join(os.path.join(g_home,'etc'),'code_dl.csv'),{},0)
    
    def _codes(self):
        codes = self._conf.keys()
        codes.sort()
        return codes

    '''**************
    return value
    0:stock name
    1:today open
    2:yestoday close
    3:lastest price
    4:today high
    5:today low
    6:buy1
    7:sell1
    8:vol gu
    9:vol yuan
    10:buy1 volume 11:buy1 price
    12:buy2 volume 13:buy2 price
    14:buy3 volume 15:buy3 price
    16:buy4 volume 17:buy4 price
    18:buy5 volmue 19:buy5 price
    20:sell1 volume 21:sell1 price
    (22, 23),(24, 25),(26,27),(28, 29)sell2-5 volume and price
    30: 2008-01-11 date
    31: 15:05:32  time
    **************'''
    def _rtprice(self,code):
        market = None
        if code[:2]=='60' or code[0]=='5':
            market = 'sh'
        else:
            market = 'sz'
        url = 'http://hq.sinajs.cn/list=%s%s'%(market,code)
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            v = None
            now = datetime.datetime.now()
            if (float(info[9])>0) and (info[30] == '%04d-%02d-%02d'%(now.year,now.month,now.day)):
                dt = info[30]
                op = float(info[1])
                hi = float(info[4])
                lo = float(info[5])
                cl = float(info[3])
                pcl = float(info[2])
                zde = cl-pcl
                zdf = ((cl-pcl)/pcl)*100
                volh = float(info[8])/100
                volwy = float(info[9])/10000
                zf = (((hi-pcl)/pcl)-((lo-pcl)/pcl))*100
                v = (code,dt,op,hi,lo,cl,'%0.2f'%zde,'%0.2f'%zdf,'%0.2f'%volh,'%0.4f'%volwy,'%0.2f'%zf)
            else:
                g_iu.log(logging.INFO,'update code[%s] no data'%(code))
            return v
        except Exception, e:
            g_iu.log(logging.INFO,'get current price code[%s] exception[%s]'%(code,e))
            return None
            
    def run(self):
        lastd = None
        while 1:
            mat = []
            codes = self._codes()
            now = datetime.datetime.now()
            wd = now.isoweekday()
            if wd!=6 and wd!=7 and now.hour>=16 and lastd != '%04d-%02d-%02d'%(now.year,now.month,now.day):
                ofn = os.path.join(os.path.join(g_home,'tmp'),'ikdl_ex_%04d%02d%02d%02d%02d%02d.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
                for code in codes:
                    v = self._rtprice(code)
                    if v:
                        mat.append(v)
                        g_iu.log(logging.INFO,'update code[%s],date[%s] done'%(code,v[1]))
                g_iu.dumpfile(ofn,mat)
                g_iu.importdata(ofn,'iknow_data_ex')
                g_iu.execmd('rm -fr %s'%ofn)
                lastd = '%04d-%02d-%02d'%(now.year,now.month,now.day)
            time.sleep(360)

            
if __name__ == "__main__":

    ikdlex().run()
    
    
    
    
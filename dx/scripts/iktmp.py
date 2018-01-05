#!/usr/bin/python

import os
import sys
import logging
import urllib2
import string
import re
import datetime
import time
import math
#import MySQLdb
import signal
from optparse import OptionParser
from bs4 import BeautifulSoup
import httplib
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil

g_iu = ikutil()

def season(month):
    sea = 4
    if month<=3:
        sea=1
    elif month<=6:
        sea=2
    elif month<=9:
        sea=3
    return sea
    
def dl():
    conf = g_iu.loadcsv(os.path.join(os.path.join(g_home,'etc'),'code_dl.csv'),{},0)
    codes = conf.keys()
    codes.sort()
    year = 2017
    sea = 4
    mat = []
    gp = 0
    for code in codes:
        try:
            url = 'http://money.finance.sina.com.cn/corp/go.php/vMS_MarketHistory/stockid/%s.phtml?year=%d&jidu=%d'%(code,year,sea)
            html=urllib2.urlopen(url).read()
            #soup = BeautifulSoup(html, 'html.parser')
            soup = BeautifulSoup(html, 'lxml')
            trs = soup.find_all('tr')
            for tr in trs:
                tds=tr.find_all('td')
                if len(tds)==7:
                    dt = tds[0].text.strip()
                    if re.match('\d{4}-\d{2}-\d{2}', dt) and dt=='2017-12-26':
                        ope = float(tds[1].text.strip())
                        high = float(tds[2].text.strip())
                        low = float(tds[4].text.strip())
                        close = float(tds[3].text.strip())
                        volh = float(tds[5].text.strip())/100.0
                        volwy = float(tds[6].text.strip())/10000.0
                        mat.append((code,dt,ope,high,low,close,volh,volwy))
                        gp = gp+1
                        print 'code[%s] date[%s] done...'%(code,dt)
                        if gp%2==0:
                            time.sleep(1)
            g_iu.log(logging.INFO,'dlone fetch from url[%s] records[%0.2f]'%(url,volwy))
        except Exception,e:
            g_iu.log(logging.INFO,'dlone fetch from url[%s] exception[%s]'%(url,e))
    ofn = os.path.join(g_home,'data_ex20180102.csv')
    g_iu.dumpdata(ofn,mat)
        
if __name__ == "__main__":
    try:
        dl()
    except Exception,e:
        g_iu.log(logging.INFO,'dlone exception[%s]....'%e)








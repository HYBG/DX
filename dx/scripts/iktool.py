#!/usr/bin/python

import os
import sys
import urllib2
import logging
import string
import re
import datetime
import time
import random
import socket
import commands
import MySQLdb
from bs4 import BeautifulSoup
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
import smtplib  
from email.mime.text import MIMEText

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')
    
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('iktool')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'iktool.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class iktool:
    def __init__(self):
        self._conn = None
        self._cursor = None
        
    def __del__(self):
        if not self._cursor:
            self._cursor.close()
        if not self._conn:
            self._conn.close()
        
    def conn(self,dbname):
        try:
            self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._conn.cursor()
            return True
        except Exception,e:
            self.log(logging.ERROR,'iktool connect db[%s] error[%s]'%(dbname,e))
        return False
        
    def reconn(self,dbname):
        try:
            self._cursor.close()
            self._conn.close()
            self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._conn.cursor()
            return True
        except Exception,e:
            self.log(logging.ERROR,'iktool reconnect db[%s] error[%s]'%(dbname,e))
        return False

    def log(self,level,str):
        g_logger.log(level,str)

    def exesqlone(self,sql,param):
        n = 0
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        ret = ()
        if n==1:
            ret = self._cursor.fetchone()
        return ret

    def exesqlbatch(self,sql,param):
        n = 0
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        n = self._cursor.execute(sql,param)
        ret = ()
        if n>0:
            ret = self._cursor.fetchall()
        return ret
        
    def task(self,sqls,log=False):
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if log:
                    g_logger.info('iktool execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                g_logger.error('iktool execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._conn.rollback()
                return False
        self._conn.commit()
        return True
        
    def _dl_season(self,month):
        sea = 4
        if month<=3:
            sea=1
        elif month<=6:
            sea=2
        elif month<=9:
            sea=3
        return sea

    def _dl_drawdigit(self,str):
        if str.isdigit():
            return int(str)
        else:
            lis = list(str)
            for i in range(len(lis)):
                if not lis[i].isdigit():
                    lis[i]=''
            return int(''.join(lis))
            
    def dl_upfrom163(self,code,start):
        td = datetime.datetime.today()
        ey = td.year
        em = td.month
        es = self._dl_season(em)
        ymd=start.split('-')
        sy = int(ymd[0])
        ss = self._dl_season(int(ymd[1]))
        s = [sy,ss]
        e = [ey,es]
        mat = []
        while s<=e:
            url = 'http://quotes.money.163.com/trade/lsjysj_%s.html?year=%s&season=%s'%(code,s[0],s[1])
            self.log(logging.INFO,'iktool ready to open url[%s]'%url)
            html=urllib2.urlopen(url).read()
            #soup = BeautifulSoup(html, 'html.parser')
            soup = BeautifulSoup(html, 'lxml')
            trs = soup.find_all('tr')
            for tr in trs:
                tds=tr.find_all('td')
                if len(tds)==11:
                    dt = tds[0].text.strip()
                    if re.match('\d{4}-\d{2}-\d{2}', dt) and dt>start:
                        open = float(tds[1].text.strip())
                        high = float(tds[2].text.strip())
                        low = float(tds[3].text.strip())
                        close = float(tds[4].text.strip())
                        vols = self._dl_drawdigit(tds[7].text.strip())
                        vole = self._dl_drawdigit(tds[8].text.strip())
                        v = (code,dt,open,high,low,close,vols,vole)
                        mat.append(v)
            self.log(logging.INFO,'iktool fetch from url[%s] records[%d] start[%s]'%(url,len(mat),start))
            if s[1]!=4:
                s[1]=s[1]+1
            else:
                s[0]=s[0]+1
                s[1]=1
        return mat


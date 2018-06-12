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

class ikrecord:
    def __init__(self,code,date,open,high,low,close,volh,volwy):
        self.code = code
        self.date = date
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volh = volh
        self.volwy = volwy
        
    def ev(self):
        return (self.open+self.high+self.low+self.close)/4.0
        
class ikdata:
    def __init__(self):
        self._data = []
        self._tool = iktool()
        self._tool.conn('hy')
        
    def load(self,code):
        data = self._tool.exesqlbatch('select date,open,high,low,close,volh,volwy from iknow_data where code=%s order by date',(code,))
        for row in data:
            self._data.append(ikrecord(code,row[0],float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6])))
            
    def load_latest(self,code,date,n):
        data = self._tool.exesqlbatch("select date,open,high,low,close,volh,volwy from iknow_data where code='%s'  and date<='%s' order by date desc limit %d"%(code,date,n),None)
        for row in data:
            self._data.append(ikrecord(code,row[0],float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6])))

    def sort(self,field,reverse):
        if len(self._data)>0:
            if hasattr(self._data[0],field):
                self._data.sort(reverse=reverse,key= lambda x:getattr(x,field))

    def length(self):
        return len(self._data)

    def get(self,index):
        return self._data[index]

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
        
    def isopenday(self):
        now = datetime.datetime.now()
        wd = now.isoweekday()
        o1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=9,minute=30,second=0)
        c2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=15,minute=0,second=0)
        if wd == 6 or wd == 7:
            return False
        if now < o1 or now > c2:
            return False
        url = 'http://hq.sinajs.cn/list=sz399001'
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            if info[30] == '%04d-%02d-%02d'%(now.year,now.month,now.day):
                return True
        except Exception, e:
            self.log(logging.WARNING,'get current url[%s] exception[%s]'%(url,e))
            return None

    def rtprice(self,code):
        market = None
        if code[:2]=='60' or code[0]=='5':
            market = 'sh'
        else:
            market = 'sz'
        url = 'http://hq.sinajs.cn/list=%s%s'%(market,code)
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            v = (info[30],info[31],code,float(info[1]),float(info[4]),float(info[5]),float(info[3]),float(info[9]),float(info[2]))
            return v
        except Exception, e:
            self.log(logging.WARNING,'get current price code[%s] exception[%s]'%(code,e))
            return None
            
    def _rtprice(self,codes):
        codeliststr = ''
        for code in codes:
            market = None
            if code[:2]=='60' or code[0]=='5':
                market = 'sh'
            else:
                market = 'sz'
            codeliststr = codeliststr + '%s%s,'%(market,code)
        url = 'http://hq.sinajs.cn/list=%s'%(codeliststr[:-1])
        #self.log(logging.INFO,'_rtprice url[%s]'%(url))
        data = urllib2.urlopen(url).readlines()
        i = 0
        lis = []
        for line in data:
            info = line.split('"')[1].split(',')
            now = datetime.datetime.now()
            if int(info[8])>0 and info[30]=='%04d-%02d-%02d'%(now.year,now.month,now.day):
                code = codes[i]
                yc = float(info[2])
                open = float(info[1])
                high = float(info[4])
                low = float(info[5])
                close = float(info[3])
                volh = float(info[8])
                volwy = float(info[9])
                v = (code,'%s %s'%(info[30],info[31]),code,open,high,low,close,volh,volwy,yc)
                lis.append(v)
            i = i+1
        return lis
            
    def rtpricebatch(self,codes):
        try:
            thv = 800
            n = (len(codes)/thv)+1
            lis = []
            for i in range(n):
                start = i*thv
                cs = codes[start:start+thv]
                l = self._rtprice(cs)
                lis = lis+l
            return lis
        except Exception, e:
            self.log(logging.WARNING,'get current price codes exception[%s]'%(e))
            return None

    def allst(self):
        try:
            url = 'http://quote.eastmoney.com/stocklist.html'
            html = urllib2.urlopen(url).read()
            soup = BeautifulSoup(html, 'lxml')
            lis = soup.find_all('li')
            stlis = []
            for li in lis:
                try:
                    a = li.find_all('a')
                    name = a[0].text.strip()
                    names = name.split('(')
                    name = names[0]
                    code = names[1][:-1]
                    if name[:2]=='ST' or name[:3]=='*ST' or name[:4]=='**ST':
                        stlis.append(code)
                except Exception,e:
                    self.log(logging.WARNING,'parse url[%s] exception[%s]...'%(url,e))
            return stlis
        except Exception,e:
            self.log(logging.ERROR,'access url[%s] exception[%s]...'%(url,e))
        return None

if __name__ == "__main__":
    tl = iktool()
    tl.conn('dx')
    code='600111'
    begin = '2018-01-01'
    need = tl.exesqlbatch('select date from dx.iknow_data where code=%s and date>%s',(code,begin))
    have = tl.exesqlbatch('select date from dx.iknow_attr where code=%s',(code))
    list(set(need).difference(set(have)))





        
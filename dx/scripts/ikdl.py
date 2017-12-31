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


class ikdl:
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
            
    def _dl_upfrom163(self,code,start):
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
            g_iu.log(logging.INFO,'ikdl ready to open url[%s]'%url)
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
                        we = float(tds[5].text.strip())
                        ww = float(tds[6].text.strip())
                        vols = self._dl_drawdigit(tds[7].text.strip())
                        vole = self._dl_drawdigit(tds[8].text.strip())
                        zf = float(tds[9].text.strip())
                        hs = float(tds[10].text.strip())
                        v = (code,dt,open,high,low,close,we,ww,vols,vole,zf,hs)
                        mat.append(v)
            g_iu.log(logging.INFO,'ikdl fetch from url[%s] records[%d]'%(url,len(mat)))
            if s[1]!=4:
                s[1]=s[1]+1
            else:
                s[0]=s[0]+1
                s[1]=1
        return mat
        
    def update(self):
        try:
            now = datetime.datetime.now()
            if self._lastdl == '%04d-%02d-%02d'%(now.year,now.month,now.day):
                return
            self._reload()
            clis = self._codes()
            allofn = os.path.join(os.path.join(g_home,'tmp'),'ikdl_data_%04d%02d%02d%02d%02d%02d_update.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
            for code in clis:
                try:
                    start = '2016-01-01'
                    if self._conf.has_key(code):
                        start = self._conf[code]
                    mat = self._dl_upfrom163(code,start)
                    if len(mat)==0:
                        continue
                    g_iu.appendmat(allofn,mat)
                except Exception,e:
                    g_iu.log(logging.INFO,'code[%s],date[%04d-%02d-%02d] update failed[%s]'%(code,now.year,now.month,now.day,e))
            if os.path.isfile(allofn):
                g_iu.importdata(allofn,'iknow_data')
                self._lastdl = '%04d-%02d-%02d'%(now.year,now.month,now.day)
                g_iu.log(logging.INFO,'import ikdl handled codes date[%04d-%02d-%02d]'%(now.year,now.month,now.day))
                g_iu.execmd('rm -fr %s'%allofn)
        except Exception,e:
            g_iu.log(logging.INFO,'import ikdl exception[%s]....'%e)

            
if __name__ == "__main__":

    bill = ikdl()
    bill.update()
    
    
    
    
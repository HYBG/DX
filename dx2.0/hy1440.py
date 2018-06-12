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
import copy
from bs4 import BeautifulSoup
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil
from iktool import iktool

g_iu = ikutil()
g_tool = iktool()

class hy1440:
    def __init__(self):
        self._codes = []
        self._data = {}
        g_tool.conn('hy1440')
        self._logger = g_iu.createlogger('hy1440',os.path.join(os.path.join(g_home,'log'),'hy1440.log'),logging.INFO)

    def __del__(self):
        pass

    def _reload(self):
        g_tool.reconn('hy1440')
        ld = g_tool.exesqlone('select date from hy.iknow_data order by date desc limit 1',None)
        ld = ld[0]
        data = g_tool.exesqlbatch('select code,open,high,low,close,(close-open)*volh from hy.iknow_data where date=%s order by code',(ld,))
        self._codes = []
        self._data = {}
        st = g_tool.allst()
        for row in data:
            if row[0] not in st:
                self._codes.append(row[0])
                self._data[row[0]] = row[1:]
        self._logger.info('hy1440 ST list length[%d] useful list length[%d]'%(len(st),len(self._codes)))

    def _standardization(self,cur,prev):
        prices = 0.0
        prices = cur[0]+cur[1]+cur[2]+cur[3]+prev[0]+prev[1]+prev[2]+prev[3]
        pev = prices/8.0
        prices = 0.0
        prices = (cur[0]-pev)**2+(cur[1]-pev)**2+(cur[2]-pev)**2+(cur[3]-pev)**2+(prev[0]-pev)**2+(prev[1]-pev)**2+(prev[2]-pev)**2+(prev[3]-pev)**2
        pstd = prices**0.5
        vector = (self._stdv(cur[0],pev,pstd),self._stdv(cur[1],pev,pstd),self._stdv(cur[2],pev,pstd),self._stdv(cur[3],pev,pstd),self._stdv(prev[0],pev,pstd),self._stdv(prev[1],pev,pstd),self._stdv(prev[2],pev,pstd),self._stdv(prev[3],pev,pstd))
        return vector

    def _stdv(self,val,ev,std):
        stdv = 0.0
        if std!=0:
            stdv = (val-ev)/std
        return float('%0.4f'%stdv)

    def _distance(self,v1,v2):
        all = 0.0
        for i in range(len(v1)):
            all = all + (v1[i]-v2[i])**2
        return all**0.5
        
    def _range(self,fv,stdvec,thv,day):
        data = g_tool.exesqlbatch('select code,date,stdo,stdh,stdl,stdc,stdo1,stdh1,stdl1,stdc1,h1 from dx.iknow_lib where date<%s and fv=%s and stdo>%s and stdo<%s and stdh>%s and stdh<%s and stdl>%s and stdl<%s and stdc>%s and stdc<%s and stdo1>%s and stdo1<%s and stdh1>%s and stdh1<%s and stdl1>%s and stdl1<%s and stdc1>%s and stdc1<%s',(day,fv,stdvec[0]-thv,stdvec[0]+thv,stdvec[1]-thv,stdvec[1]+thv,stdvec[2]-thv,stdvec[2]+thv,stdvec[3]-thv,stdvec[3]+thv,stdvec[4]-thv,stdvec[4]+thv,stdvec[5]-thv,stdvec[5]+thv,stdvec[6]-thv,stdvec[6]+thv,stdvec[7]-thv,stdvec[7]+thv))
        return list(data)

    def _middle(self,lis):
        lis.sort()
        return lis[int(len(lis)/2)]

    def _prob(self,data):
        perf = [[row[i] for row in data] for i in range(2)]
        h1m = self._middle(perf[1])
        return float('%0.4f'%h1m)
        
    def _task(self,codes):
        self._logger.info('_task codes count[%d]'%len(codes))
        data = g_tool.rtpricebatch(codes)
        matd = {}
        for row in data:
            code = row[0]
            date = row[1]
            open = float(row[2])
            high = float(row[3])
            low = float(row[4])
            close = float(row[5])
            volh = float(row[6])
            v = (close-open)*volh
            yrow = self._data[code]
            if high>float(yrow[1]) and low>float(yrow[2]) and close>open and v>float(yrow[4]):
                zdf = (close-float(yrow[3]))/float(yrow[3])
                if zdf>0.03 and zdf <= 0.109:
                    matd[code]=((open,high,low,close,v),yrow)
        self._logger.info('hy1440 filter codes[%d]...'%len(matd))
        total = float(len(matd))
        handled = 0
        thv = 0.1
        maxlen = 256
        day = datetime.date.today()
        day = day.strftime('%Y-%m-%d')
        mat = []
        for code in matd.keys():
            fv = '1011'
            stdvec = self._standardization(matd[code][0],matd[code][1])
            rng = self._range(fv,stdvec,thv,day)
            tmt = []
            for row in rng:
                d = self._distance(stdvec,row[2:-1])
                if d<thv:
                    tmt.append((d,row[-1]))
            if len(tmt)==0:
                continue
            realhit = len(tmt)
            if len(tmt)>maxlen:
                tmt.sort()
                tmt = tmt[:maxlen]
            tell = self._prob(tmt)
            mat.append((tell,code))
            self._logger.info('hy1440 handle progress[%0.2f%%] code[%s] date[%s] range[%d] hit[%d] use[%d]....'%(100*(handled/total),code,day,len(rng),realhit,len(tmt)))
        mat.sort(reverse=True)
        mat = mat[:5]
        return mat

    def _exetask(self,codes,date,task):
        self._logger.info('execute task[%s %s]....'%(date,task))
        mat = self._task(codes)
        sqls = []
        for row in mat:
            sqls.append(('insert into hy1440.hy_tell(date,task,code,h1) values(%s,%s,%s,%s)',(date,task,row[1],row[0])))
        g_tool.task(sqls)
        self._logger.info('hy1440 task[%s %s] executed sqls[%d]'%(date,task,len(sqls)))
        
    def work(self):
        while 1:
            if len(self._codes)==0:
                self._reload()
            now = datetime.datetime.now()
            start1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=11,minute=30,second=0)
            end1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=13,minute=30,second=0)
            start2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=13,minute=30,second=0)
            end2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=14,minute=0,second=0)
            start3 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=14,minute=0,second=0)
            end3 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=14,minute=30,second=0)
            start4 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=14,minute=30,second=0)
            end4 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=15,minute=0,second=0)
            status = 0
            if g_tool.isopenday():
                date = '%04d-%02d-%02d'%(now.year,now.month,now.day)
                self._logger.info('today is open,time[%s %02d:%02d:%02d]'%(date,now.hour,now.minute,now.second))
                if now.hour==9 and now.minute==30:
                    self._reload()
                if now>start1 and now <end1:
                    if status==1:
                        continue
                    self._exetask(self._codes,date,'11:30:00')
                    status = 1
                if now>start2 and now <end2:
                    if status==2:
                        continue
                    self._exetask(self._codes,date,'13:30:00')
                    status = 2
                if now>start3 and now <end3:
                    if status==3:
                        continue
                    self._exetask(self._codes,date,'14:00:00')
                    status = 3
                if now>start4 and now < end4:
                    if status==4:
                        continue
                    self._exetask(self._codes,date,'14:30:00')
                    status = 4
                if now>end3:
                    status=0
            else:
                self._logger.info('today is close')
            time.sleep(5)

    def service(self):
        pass

    def run(self):
        self.work()

if __name__ == "__main__":
    hy = hy1440()
    hy.run()
    
    
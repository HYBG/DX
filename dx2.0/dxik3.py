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
from iktool import ikdata
from iktool import ikrecord

g_iu = ikutil()
g_tool = iktool()

class dxik3:
    def __init__(self):
        self.__codes = {}
        g_tool.conn('hy')
        self._reload()
        self._mindate = '2015-01-05'
        self._logger = g_iu.createlogger('dxik3',os.path.join(os.path.join(g_home,'log'),'dxik3.log'),logging.INFO)

    def __del__(self):
        pass

    def _reload(self):
        g_tool.reconn('hy')
        data = g_tool.exesqlbatch('select code from hy.iknow_name order by code', None)
        for row in data:
            ld = g_tool.exesqlone('select date from hy.iknow_data where code=%s order by date desc limit 1',(row[0],))
            if len(ld)!=0:
                self.__codes[row[0]]=ld[0]
            else:
                self.__codes[row[0]]='1982-09-04'

    def _codes(self):
        codes = self.__codes.keys()
        codes.sort()
        return codes

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

    def _fv(self,cur,prev1,prev2):
        hb = 0
        if cur.high>prev1.high:
            hb = 1
        lb = 0
        if cur.low<prev1.low:
            lb = 1
        k = 0
        if cur.close>cur.open:
            k = 1
        hb1 = 0
        if prev1.high>prev2.high:
            hb1 = 1
        lb1 = 0
        if prev1.low<prev2.low:
            lb1 = 1
        k1 = 0
        if prev1.close>prev2.open:
            k1 = 1
        vol0 = 0
        if cur.close!=cur.open:
            vol0 = ((cur.close-cur.open)/abs((cur.close-cur.open)))*cur.volh
        vol1 = 0
        if prev1.close!=prev1.open:
            vol1 = ((prev1.close-prev1.open)/abs((prev1.close-prev1.open)))*prev1.volh
        vol2 = 0
        if prev2.close!=prev2.open:
            vol2 = ((prev2.close-prev2.open)/abs((prev2.close-prev2.open)))*prev2.volh
        v1 = 0
        if vol0-vol1>0:
            v1 = 1
        v2 = 0
        if vol0+vol2-2*vol1>0:
            v2 = 1
        return '%d%d%d%d%d%d%d%d'%(hb,lb,k,v1,hb1,lb1,k1,v2)

    def _standardization(self,cur,prev1,prev2):
        pev = (cur.ev()+prev1.ev()+prev2.ev())/3.0
        prices = 0.0
        prices = prices + (cur.open-pev)**2 + (cur.high-pev)**2 + (cur.low-pev)**2 + (cur.close-pev)**2
        prices = prices + (prev1.open-pev)**2 + (prev1.high-pev)**2 + (prev1.low-pev)**2 + (prev1.close-pev)**2
        prices = prices + (prev2.open-pev)**2 + (prev2.high-pev)**2 + (prev2.low-pev)**2 + (prev2.close-pev)**2
        pstd = prices**0.5
        lis = []
        lis.append(self._stdv(cur.open,pev,pstd))
        lis.append(self._stdv(cur.high,pev,pstd))
        lis.append(self._stdv(cur.low,pev,pstd))
        lis.append(self._stdv(cur.close,pev,pstd))
        lis.append(self._stdv(prev1.open,pev,pstd))
        lis.append(self._stdv(prev1.high,pev,pstd))
        lis.append(self._stdv(prev1.low,pev,pstd))
        lis.append(self._stdv(prev1.close,pev,pstd))
        lis.append(self._stdv(prev2.open,pev,pstd))
        lis.append(self._stdv(prev2.high,pev,pstd))
        lis.append(self._stdv(prev2.low,pev,pstd))
        lis.append(self._stdv(prev2.close,pev,pstd))
        return tuple(lis)
        
    def _range(self,fv,stdvec,thv,day):
        data = g_tool.exesqlbatch('select code,date,stdo,stdh,stdl,stdc,stdo1,stdh1,stdl1,stdc1,nfv,p1,p2,h1,l1 from dx.iknow_lib where date<%s and fv=%s and stdo>%s and stdo<%s and stdh>%s and stdh<%s and stdl>%s and stdl<%s and stdc>%s and stdc<%s and stdo1>%s and stdo1<%s and stdh1>%s and stdh1<%s and stdl1>%s and stdl1<%s and stdc1>%s and stdc1<%s',(day,fv,stdvec[0]-thv,stdvec[0]+thv,stdvec[1]-thv,stdvec[1]+thv,stdvec[2]-thv,stdvec[2]+thv,stdvec[3]-thv,stdvec[3]+thv,stdvec[4]-thv,stdvec[4]+thv,stdvec[5]-thv,stdvec[5]+thv,stdvec[6]-thv,stdvec[6]+thv,stdvec[7]-thv,stdvec[7]+thv))
        return list(data)
        
    def _guass(self,lis):
        ev = sum(lis)/float(len(lis))
        all = 0.0
        for item in lis:
            all = all + (item-ev)**2
        std = all**0.5
        return (ev,std)
        
    def _middle(self,lis):
        lis.sort()
        return lis[int(len(lis)/2)]

    def _prob(self,data):
        perf = [[row[i] for row in data] for i in range(8)]
        h1m = self._middle(perf[1])
        l1m = self._middle(perf[2])
        hbp = sum(perf[3])/float(len(data))
        lbp = sum(perf[4])/float(len(data))
        kp = sum(perf[5])/float(len(data))
        hpp = sum(perf[6])/float(len(data))
        lpp = sum(perf[7])/float(len(data))
        return (float('%0.4f'%h1m),float('%0.4f'%l1m),float('%0.4f'%hbp),float('%0.4f'%lbp),float('%0.4f'%kp),float('%0.4f'%hpp),float('%0.4f'%lpp))

    def tell(self,day):
        self._logger.info('dxik3 tell[%s] task start....'%day)
        clis = self._codes()
        total = float(len(clis))
        handled = 1
        sqls = []
        thv = 0.2
        maxlen = 256
        for code in clis:
            handled = handled+1
            data = ikdata()
            data.load_latest(code,day,3)
            if data.length()!=3:
                continue
            fv = self._fv(data.get(0),data.get(1),data.get(2))
            stdvec = self._standardization(data.get(0),data.get(1),data.get(2))
            rng = g_tool.exesqlbatch('select code,date,stdo,stdh,stdl,stdc,stdo1,stdh1,stdl1,stdc1,stdo2,stdh2,stdl2,stdc2,nfv,h1,l1 from dx.iknow_lib3 where date<%s and fv=%s and stdo>%s and stdo<%s and stdh>%s and stdh<%s and stdl>%s and stdl<%s and stdc>%s and stdc<%s and stdo1>%s and stdo1<%s and stdh1>%s and stdh1<%s and stdl1>%s and stdl1<%s and stdc1>%s and stdc1<%s and stdo2>%s and stdo2<%s and stdh2>%s and stdh2<%s and stdl2>%s and stdl2<%s and stdc2>%s and stdc2<%s',(day,fv,stdvec[0]-thv,stdvec[0]+thv,stdvec[1]-thv,stdvec[1]+thv,stdvec[2]-thv,stdvec[2]+thv,stdvec[3]-thv,stdvec[3]+thv,stdvec[4]-thv,stdvec[4]+thv,stdvec[5]-thv,stdvec[5]+thv,stdvec[6]-thv,stdvec[6]+thv,stdvec[7]-thv,stdvec[7]+thv,stdvec[8]-thv,stdvec[8]+thv,stdvec[9]-thv,stdvec[9]+thv,stdvec[10]-thv,stdvec[10]+thv,stdvec[11]-thv,stdvec[11]+thv))
            tmt = []
            for row in rng:
                d = self._distance(stdvec,row[2:-3])
                if d<thv:
                    tmt.append((d,row[-2],row[-1],int(row[-3][0]),int(row[-3][1]),int(row[-3][2]),int(row[-3][3]),int(row[-3][4])))
            if len(tmt)==0:
                continue
            realhit = len(tmt)
            if len(tmt)>maxlen:
                tmt.sort()
                tmt = tmt[:maxlen]
            tell = self._prob(tmt)
            sqls.append(('insert into dx.iknow_tell3(code,date,fv,count,h1m,l1m,hbp,lbp,kp,hpp,lpp) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,day,fv,len(tmt),)+tell))
            self._logger.info('dxik3 tell handle progress[%0.2f%%] code[%s] date[%s] range[%d] hit[%d] use[%d]....'%(100*(handled/total),code,day,len(rng),realhit,len(tmt)))
        g_tool.task(sqls)
        self._logger.info('dxik3 tell[%s] task done,executed sqls[%d]....'%(day,len(sqls)))

    def told(self,start,end):
        self._logger.info('dxik3 handle tell[%s-%s] start....'%(start,end))
        dts = g_tool.exesqlbatch('select distinct date from hy.iknow_data where date>=%s and date<=%s and date not in (select distinct date from dx.iknow_tell3)',(start,end))
        for dt in dts:
            if not self._istold(dt[0]):
                self.tell(dt[0])
        self._logger.info('dxik3 handle tell[%s-%s] end....'%(start,end))

    def _istold(self,day):
        cnt = g_tool.exesqlone('select count(*) from dx.iknow_tell3 where date=%s',(day,))
        if cnt[0]>0:
            return True
        return False

    def daily_task(self,name):
        g_tool.reconn('hy')
        time.sleep(5)
        self._logger.info('daily_task[%s] start....'%(name))
        if not self._istold(name):
            self.tell(name)
        self._logger.info('daily_task[%s] end successfully....'%(name))

    def _data_status(self):
        status = g_tool.exesqlone('select value from hy.iknow_conf where name=%s',('status',))
        if len(status)==0:
            return None
        return status[0]

    def _taskname(self):
        dt = datetime.datetime.now()
        if dt.hour < 17:
            dt = dt + datetime.timedelta(days=-1)
        while dt.isoweekday()>5:
            dt = dt + datetime.timedelta(days=-1)
        return '%04d-%02d-%02d'%(dt.year,dt.month,dt.day)

    def run(self):
        pretask = ''
        while 1:
            taskname = self._taskname()
            if taskname != pretask and self._data_status()=='idle':
                self.daily_task(taskname)
                pretask = taskname
            time.sleep(5)

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-t', '--tell', action='store_true', dest='tell',default=False, help='tell task')
    parser.add_option('-a', '--attr', action='store_true', dest='attr',default=False, help='attr task')
    parser.add_option('-s', '--start', action='store', dest='start',default=None, help='tell task start day')
    parser.add_option('-e', '--end', action='store', dest='end',default=None, help='tell task end day')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    ik = dxik3()
    if ops.tell and ops.start and ops.end:
        ik.told(ops.start,ops.end)
    else:
        ik.run()
    
    
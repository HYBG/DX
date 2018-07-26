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

class dxiknow:
    def __init__(self):
        self.__codes = {}
        g_tool.conn('hy')
        self._reload()
        self._mindate = '2015-01-05'
        self._logger = g_iu.createlogger('dxiknow',os.path.join(os.path.join(g_home,'log'),'dxiknow.log'),logging.INFO)

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

    def _fv(self,cur,prev):
        hb = 0
        if cur[2]>prev[2]:
            hb = 1
        lb = 0
        if cur[3]<prev[3]:
            lb = 1
        k = 0
        if cur[4]>cur[1]:
            k = 1
        v1 = 0
        if (cur[4]>cur[1])*cur[5]-(prev[4]>prev[1])*prev[5]>0:
            v1 = 1
        return '%d%d%d%d'%(hb,lb,k,v1)

    def _standardization(self,need):
        prices = 0.0
        for row in need:
            prices = prices + row[1] + row[2] + row[3] + row[4]
        pev = prices/(len(need)*4.0)
        prices = 0.0
        for row in need:
            prices = prices + (row[1]-pev)**2 + (row[2]-pev)**2 + (row[3]-pev)**2 + (row[4]-pev)**2
        pstd = prices**0.5
        lis = []
        tmp = list(copy.deepcopy(need))
        while len(tmp)>0:
            row = tmp.pop()
            for i in range(1,len(row)-1):
                lis.append(self._stdv(row[i],pev,pstd))
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
        perf = [[row[i] for row in data] for i in range(10)]
        h1m = self._middle(perf[1])
        l1m = self._middle(perf[2])
        p1m = self._middle(perf[3])
        p2m = self._middle(perf[4])
        hbp = sum(perf[5])/float(len(data))
        lbp = sum(perf[6])/float(len(data))
        kp = sum(perf[7])/float(len(data))
        hpp = sum(perf[8])/float(len(data))
        lpp = sum(perf[9])/float(len(data))
        return (float('%0.4f'%h1m),float('%0.4f'%l1m),float('%0.4f'%p1m),float('%0.4f'%p2m),float('%0.4f'%hbp),float('%0.4f'%lbp),float('%0.4f'%kp),float('%0.4f'%hpp),float('%0.4f'%lpp))

    def _prob2(self,data):
        all = float(len(data))
        hhmt = []
        hlmt = []
        lhmt = []
        llmt = []
        bhmt = []
        blmt = []
        nhmt = []
        nlmt = []
        for row in data:
            code = row[1]
            date = row[2]
            pd = g_tool.exesqlbatch('select high,low,close from hy.iknow_data where code=%s and date>=%s order by date limit 2',(code,date))
            if len(pd)<2:
                continue
            hb = 0
            if float(pd[1][0])>float(pd[0][0]):
                hb = 1
            lb = 0
            if float(pd[1][1])<float(pd[0][1]):
                lb = 1
            hr = (float(pd[1][0])-float(pd[0][2]))/float(pd[0][2])
            lr = (float(pd[1][1])-float(pd[0][2]))/float(pd[0][2])
            if hb==1 and lb==0:
                hhmt.append(hr)
                hlmt.append(lr)
            elif hb==0 and lb==1:
                lhmt.append(hr)
                llmt.append(lr)
            elif hb==1 and lb==1:
                bhmt.append(hr)
                blmt.append(lr)
            else:
                nhmt.append(hr)
                nlmt.append(lr)
        hhmt.sort()
        hlmt.sort()
        lhmt.sort()
        llmt.sort()
        bhmt.sort()
        blmt.sort()
        nhmt.sort()
        nlmt.sort()
        self._logger.info('dxiknow hhmt[%d],hlmt[%d],lhmt[%d],llmt[%d],bhmt[%d],blmt[%d],nhmt[%d],nlmt[%d]....'%(len(hhmt),len(hlmt),len(lhmt),len(llmt),len(bhmt),len(blmt),len(nhmt),len(nlmt)))
        hp = float(len(hhmt))/all
        lp = float(len(lhmt))/all
        bp = float(len(bhmt))/all
        np = float(len(nhmt))/all
        hhev = 0
        hlev = 0
        lhev = 0
        llev = 0
        bhev = 0
        blev = 0
        nhev = 0
        nlev = 0
        if len(hhmt)>0:
            hhev = hhmt[len(hhmt)/2]
        if len(hlmt)>0:
            hlev = hlmt[len(hlmt)/2]
        if len(lhmt)>0:
            lhev = lhmt[len(lhmt)/2]
        if len(llmt)>0:
            llev = llmt[len(llmt)/2]
        if len(bhmt)>0:
            bhev = bhmt[len(bhmt)/2]
        if len(blmt)>0:
            blev = blmt[len(blmt)/2]
        if len(nhmt)>0:
            nhev = nhmt[len(nhmt)/2]
        if len(nlmt)>0:
            nlev = nlmt[len(nlmt)/2]
        return (float('%0.4f'%hp),float('%0.4f'%lp),float('%0.4f'%bp),float('%0.4f'%np),float('%0.4f'%hhev),float('%0.4f'%hlev),float('%0.4f'%lhev),float('%0.4f'%llev),float('%0.4f'%bhev),float('%0.4f'%blev),float('%0.4f'%nhev),float('%0.4f'%nlev))
        
    def tell(self,day):
        self._logger.info('dxiknow tell[%s] task start....'%day)
        clis = self._codes()
        total = float(len(clis))
        handled = 1
        sqls = []
        thv = 0.1
        maxlen = 256
        for code in clis:
            data = g_tool.exesqlbatch('select date,open,high,low,close,volh from hy.iknow_data where code=%s and date<=%s order by date desc limit 2',(code,day))
            if len(data)!=2:
                continue
            fv = self._fv(data[0],data[1])
            data = list(data)
            data.sort()
            stdvec = self._standardization(data)
            rng = self._range(fv,stdvec,thv,day)
            tmt = []
            for row in rng:
                d = self._distance(stdvec,row[2:-5])
                if d<thv:
                    tmt.append((d,row[-4],row[-3],row[-2],row[-1],int(row[-5][0]),int(row[-5][1]),int(row[-5][2]),int(row[-5][3]),int(row[-5][4])))
            if len(tmt)==0:
                continue
            realhit = len(tmt)
            if len(tmt)>maxlen:
                tmt.sort()
                tmt = tmt[:maxlen]
            tell = self._prob(tmt)
            sqls.append(('insert into dx.iknow_tell(code,date,count,h1m,l1m,p1m,p2m,hbp,lbp,kp,hpp,lpp) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,day,len(tmt),)+tell))
            self._logger.info('dxiknow tell handle progress[%0.2f%%] code[%s] date[%s] range[%d] hit[%d] use[%d]....'%(100*(handled/total),code,day,len(rng),realhit,len(tmt)))
            handled = handled+1
        g_tool.task(sqls)
        self._logger.info('dxiknow tell[%s] task done,executed sqls[%d]....'%(day,len(sqls)))
        
    def tell2(self,day):
        self._logger.info('dxiknow tell2[%s] task start....'%day)
        clis = self._codes()
        total = float(len(clis))
        handled = 1
        sqls2 = []
        thv = 0.12
        maxlen = 512
        for code in clis:
            data = g_tool.exesqlbatch('select date,open,high,low,close,volh from hy.iknow_data where code=%s and date<=%s order by date desc limit 2',(code,day))
            if len(data)!=2:
                continue
            fv = self._fv(data[0],data[1])
            data = list(data)
            data.sort()
            stdvec = self._standardization(data)
            rng = self._range(fv,stdvec,thv,day)
            tmt2 = []
            for row in rng:
                d = self._distance(stdvec,row[2:-5])
                if d<thv:
                    tmt2.append((d,row[0],row[1]))
            if len(tmt2)==0:
                continue
            realhit = len(tmt2)
            if len(tmt2)>maxlen:
                tmt2.sort()
                tmt2 = tmt2[:maxlen]
            tell2 = self._prob2(tmt2)
            sqls2.append(('insert into dx.iknow_tell2(code,date,count,hbr,lbr,bbr,nbr,hhev,hlev,lhev,llev,bhev,blev,nhev,nlev) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,day,len(tmt2))+tell2))
            self._logger.info('dxiknow tell2 handle progress[%0.2f%%] code[%s] date[%s] range[%d] hit[%d] use[%d]....'%(100*(handled/total),code,day,len(rng),realhit,len(tmt2)))
            handled = handled+1
        g_tool.task(sqls2)
        self._logger.info('dxiknow tell2[%s] task done,executed sqls[%d]....'%(day,len(sqls2)))

    def told(self,start,end):
        self._logger.info('dxiknow handle tell[%s-%s] start....'%(start,end))
        dts = g_tool.exesqlbatch('select distinct date from hy.iknow_data where date>=%s and date<=%s and date not in (select distinct date from dx.iknow_tell)',(start,end))
        for dt in dts:
            if not self._istold(dt[0]):
                self.tell(dt[0])
                self.tell2(dt[0])
        self._logger.info('dxiknow handle tell[%s-%s] end....'%(start,end))

    def _istold(self,day):
        cnt = g_tool.exesqlone('select count(*) from dx.iknow_tell where date=%s',(day,))
        if cnt[0]>0:
            return True
        return False
            
    def attr(self,day):
        self._logger.info('dxiknow attr[%s] task start....'%day)
        clis = self._codes()
        total = float(len(clis))
        handled = 1
        sqls = []
        for code in clis:
            data = g_tool.exesqlbatch('select date,open,high,low,close,volh from hy.iknow_data where code=%s and date<=%s order by date desc limit 2',(code,day))
            if len(data)!=2:
                continue
            fv = self._fv(data[0],data[1])
            data = list(data)
            data.sort()
            stdvec = self._standardization(data)
            sqls.append(('insert into dx.iknow_attr(code,date,fv,stdo,stdh,stdl,stdc,stdo1,stdh1,stdl1,stdc1) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,day,fv,)+stdvec))
            self._logger.info('dxiknow attr handle progress[%0.2f%%] code[%s] date[%s]....'%(100*(handled/total),code,day))
            handled = handled+1
        g_tool.task(sqls)
        self._logger.info('dxiknow attr[%s] task done,executed sqls[%d]....'%(day,len(sqls)))
        
    def _isattr(self,day):
        cnt = g_tool.exesqlone('select count(*) from dx.iknow_attr where date=%s',(day,))
        if cnt[0]>0:
            return True
        return False
        
    def attrs(self,start,end):
        self._logger.info('dxiknow handle attrs[%s-%s] start....'%(start,end))
        dts = g_tool.exesqlbatch('select distinct date from hy.iknow_data where date>=%s and date<=%s and date not in (select distinct date from dx.iknow_attr)',(start,end))
        for dt in dts:
            if not self._isattr(dt[0]):
                self.attr(dt[0])
        self._logger.info('dxiknow handle attrs[%s-%s] end....'%(start,end))

    def daily_task(self,name):
        g_tool.reconn('hy')
        time.sleep(5)
        self._logger.info('daily_task[%s] start....'%(name))
        if not self._istold(name):
            self.tell2(name)
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
        try:
            while 1:
                taskname = self._taskname()
                if taskname != pretask and self._data_status()=='idle':
                    self.daily_task(taskname)
                    pretask = taskname
                time.sleep(5)
        except Exception,e:
            self._logger.info('dxiknow run exception[%s]....'%(e))

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-t', '--tell', action='store_true', dest='tell',default=False, help='tell task')
    parser.add_option('-a', '--attr', action='store_true', dest='attr',default=False, help='attr task')
    parser.add_option('-s', '--start', action='store', dest='start',default=None, help='tell task start day')
    parser.add_option('-e', '--end', action='store', dest='end',default=None, help='tell task end day')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)
        
    ik = dxiknow()
    if ops.tell and ops.start and ops.end:
        ik.told(ops.start,ops.end)
    elif ops.attr and ops.start and ops.end:
        ik.attrs(ops.start,ops.end)
    else:
        ik.run()
        
            
    
    
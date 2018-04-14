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

class iknow:
    def __init__(self):
        self.__codes = {}
        g_tool.conn('dx')
        self._reload()
        self._sqlbatch = 1500
        self._mincnt = 21
        self._rate = 0.0012

    def __del__(self):
        pass

    def _reload(self):
        g_tool.reconn('dx')
        data = g_tool.exesqlbatch('select code from dx.iknow_name order by code', None)
        for row in data:
            ld = g_tool.exesqlone('select date from dx.iknow_data where code=%s order by date desc limit 1',(row[0],))
            if len(ld)!=0:
                self.__codes[row[0]]=ld[0]
            else:
                self.__codes[row[0]]='1982-09-04'
                
    def _codes(self):
        codes = self.__codes.keys()
        codes.sort()
        return codes

    def dl(self):
        try:
            g_iu.log(logging.INFO,'dx dl task start....')
            now = datetime.datetime.now()
            self._reload()
            clis = self._codes()
            sqls = []
            defaultstart = '2016-01-01'
            for code in clis:
                try:
                    start = defaultstart
                    if self.__codes.has_key(code):
                        start = self.__codes[code]
                    mat = g_tool.dl_upfrom163(code,start)
                    for row in mat:
                        sqls.append(('insert into dx.iknow_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                    if len(sqls)>=self._sqlbatch:
                        g_tool.task(sqls)
                        sqls = []
                except Exception,e:
                    g_iu.log(logging.INFO,'code[%s],date[%04d-%02d-%02d] update failed[%s]'%(code,now.year,now.month,now.day,e))
            g_tool.task(sqls)
            sqls = []
            for code in clis:
                try:
                    shouldadd = g_tool.exesqlbatch('select date from hs.hs_daily_data where code=%s and date not in (select date from dx.iknow_data where code=%s)',(code,code))
                    for adt in shouldadd:
                        g_iu.log(logging.INFO,'dx handle dl code[%s] date[%s]....'%(code,adt[0]))
                        row = g_tool.exesqlone('select code,date,open,high,low,close,volh,volwy from hs.hs_daily_data where code=%s and date=%s',(code,adt[0]))
                        sqls.append(('insert into dx.iknow_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                except Exception,e:
                    g_iu.log(logging.INFO,'code[%s],date[%04d-%02d-%02d] local update exception[%s]'%(code,now.year,now.month,now.day,e))
            g_tool.task(sqls)
        except Exception,e:
            g_iu.log(logging.INFO,'dx dl exception[%s]....'%e)
        g_iu.log(logging.INFO,'dx dl task done....')
        
    def _fv(self,crow,last,before):
        DATE = 0
        OPEN = 1
        HIGH = 2
        LOW = 3
        CLOSE = 4
        VOL = 5
        hb = 0
        lb = 0
        if crow[HIGH] > last[HIGH]:
            hb = 1
        if crow[LOW] < last[LOW]:
            lb = 1
        k = 0
        if crow[CLOSE]>crow[OPEN]:
            k = 1
        v1 = 0
        if (crow[VOL]-last[VOL])>0:
            v1 = 1
        v2 = 0
        if (crow[VOL]+before[VOL]-2*last[VOL])>0:
            v2 = 1
        return '%d%d%d%d%d'%(hb,lb,k,v1,v2)
        
    def _stdv(self,lis):
        ev = sum(lis)/float(len(lis))
        all = 0
        for item in lis:
            all = all + (item-ev)**2
        std = all**0.5
        stdv = (lis[0]-ev)/std
        return stdv
        
    def _transfer(self,data):
        OPEN = 1
        HIGH = 2
        LOW = 3
        CLOSE = 4
        zdfmat = []
        zfmat = []
        osrcmt = []
        csrcmt = []
        for i in range(len(data)-1):
            yc = data[i+1][CLOSE]
            open = data[i][OPEN]
            high = data[i][HIGH]
            low = data[i][LOW]
            close = data[i][CLOSE]
            zdf = (close-yc)/yc
            zf = (high-low)/yc
            osrc = 0.5
            csrc = 0.5
            if high!=low:
                osrc = (open-low)/(high-low)
                csrc = (close-low)/(high-low)
            zdfmat.append(zdf)
            zfmat.append(zf)
            osrcmt.append(osrc)
            csrcmt.append(csrc)
        return (zdfmat,zfmat,osrcmt,csrcmt)
        
    def _moreinfo(self,data):
        tmats = self._transfer(data)
        stdzdf =  self._stdv(tmats[0])
        stdzf =  self._stdv(tmats[1])
        stdosrc =  self._stdv(tmats[2])
        stdcsrc =  self._stdv(tmats[3])
        return (stdzdf,stdzf,stdosrc,stdcsrc)

    def attr(self):
        g_tool.reconn('dx')
        codes = self._codes()
        g_iu.log(logging.INFO,'dx attr handle start....')
        total = float(len(codes))
        handled = 1
        sqls = []
        for code in codes:
            ld = g_tool.exesqlone('select date from dx.iknow_attr where code=%s order by date desc limit 1',(code,))
            end = '2018-01-01'
            if len(ld)!=0:
                end = ld[0]
            data = g_tool.exesqlbatch('select date,open,high,low,close,volh from dx.iknow_data where code=%s order by date desc',(code,))
            if len(data)<=120:
                continue
            for i in range(len(data)-121):
                if data[i][0]<=end:
                    break
                need = data[i:i+121]
                fv = self._fv(need[0],need[1],need[2])
                more = self._moreinfo(need)
                sqls.append(('insert into dx.iknow_attr(code,date,fv,stdzdf,stdzf,stdosrc,stdcsrc) values(%s,%s,%s,%s,%s,%s,%s)',(code,data[i][0],fv,more[0],more[1],more[2],more[3])))
                g_iu.log(logging.INFO,'dx handle attr progress[%0.2f%%]'%(100*(handled/total)))
                handled = handled+1
            g_iu.log(logging.INFO,'dx handled attr code[%s]'%code)
        g_tool.task(sqls)
        g_iu.log(logging.INFO,'dx attr handle done,executed sqls[%d]....'%len(sqls))

    def _extract(self,baseset,vector):
        ds = []
        for row in baseset:
            d = abs(vector[0]-row[1])+abs(vector[1]-row[2])+abs(vector[2]-row[3])+abs(vector[3]-row[4])
            ds.append((d,)+row[5:])
        ds.sort()
        thv = max(int(len(ds)*self._rate),min(len(ds),self._mincnt))
        ds = ds[:thv]
        perf = [[row[i] for row in ds] for i in range(12)]
        row = []
        for p in perf[1:]:
            row.append(float('%0.4f'%(float(sum(p))/float(len(p)))))
        return tuple(row)

    def savebaseset(self):
        g_iu.log(logging.INFO,'dx savebaseset start....')
        odir = os.path.join(os.path.join(g_home,'dx'),'baseset')
        for i in range(32):
            fv = '%05d'%int(bin(i)[2:])
            ofn = os.path.join(odir,'%s.csv'%fv)
            baseset = g_tool.exesqlbatch('select date,stdzdf,stdzf,stdosrc,stdcsrc,nhb,nlb,nk,nhp,nlp,nopenzdf,nhighzdf,nlowzdf,nclosezdf from dx.iknow_base where fv=%s',(fv,))
            g_iu.dumpfile(ofn,baseset)
        g_iu.log(logging.INFO,'dx savebaseset end....')

    def loadbaseset(self,local=False):
        g_iu.log(logging.INFO,'dx loading baseset start....')
        bsdict = {}
        idir = os.path.join(os.path.join(g_home,'dx'),'baseset')
        for i in range(32):
            fv = '%05d'%int(bin(i)[2:])
            g_iu.log(logging.INFO,'dx loading baseset for fv[%s]....'%fv)
            if local:
                ifn = os.path.join(idir,'%s.csv'%fv)
                baseset = g_iu.loadcsv(ifn,{1:type(1.0),2:type(1.0),3:type(1.0),4:type(1.0),5:type(1),6:type(1),7:type(1),8:type(1),9:type(1),10:type(1.0),11:type(1.0),12:type(1.0),13:type(1.0)})
            else:
                baseset = g_tool.exesqlbatch('select date,stdzdf,stdzf,stdosrc,stdcsrc,nhb,nlb,nk,nhp,nlp,nopenzdf,nhighzdf,nlowzdf,nclosezdf from dx.iknow_base where fv=%s',(fv,))
            bsdict[fv] = baseset
        g_iu.log(logging.INFO,'dx loading baseset end....')
        return bsdict

    def tell(self,end):
        g_iu.log(logging.INFO,'dx handle tell start....')
        ld = g_tool.exesqlone('select date from dx.iknow_tell order by date limit 1',None)
        dts = None
        if len(ld)==0:
            ld = g_tool.exesqlone('select date from dx.iknow_attr order by date desc limit 1')
            if len(ld)==0:
                g_iu.log(logging.INFO,'dx handle tell end no need....')
                return
            ld = ld[0]
            dts = g_tool.exesqlbatch('select date from dx.iknow_attr where date<=%s and date>=%s order by date desc',(ld,end))
        else:
            ld = ld[0]
            dts = g_tool.exesqlbatch('select date from dx.iknow_attr where date<%s and date>=%s order by date desc',(ld,end))
        for dt in dts:
            g_iu.log(logging.INFO,'dx handle tell start date[%s]....'%dt[0])
            self.told(dt[0])
        g_iu.log(logging.INFO,'dx handle tell end....')
        
    def told(self,day):
        g_iu.log(logging.INFO,'dx handle told start[%s]....'%(day))
        attrs = g_tool.exesqlbatch('select fv,stdzdf,stdzf,stdosrc,stdcsrc,code from dx.iknow_attr where date=%s',(day,))
        fvdic = {}
        sqls = []
        total = float(len(attrs))
        handled = 1
        for attr in attrs:
            if fvdic.has_key(attr[0]):
                fvdic[attr[0]].append(attr[1:])
            else:
                fvdic[attr[0]] = [attr[1:]]
        g_iu.log(logging.INFO,'dx handle told fvs collected done....')
        fvs = fvdic.keys()
        fvs.sort()
        for fv in fvs:
            g_iu.log(logging.INFO,'dx handle told load baseset for fv[%s]....'%(fv))
            baseset = g_tool.exesqlbatch('select date,stdzdf,stdzf,stdosrc,stdcsrc,nhb,nlb,nk,nv1,nv2,nhp,nlp,nopenzdf,nhighzdf,nlowzdf,nclosezdf from dx.iknow_base where fv=%s and date<%s',(fv,day))
            g_iu.log(logging.INFO,'dx handle told load baseset for fv[%s] done....'%(fv))
            for val in fvdic[fv]:
                code = val[-1]
                vector = val[:-1]
                row = self._extract(baseset,vector)
                sqls.append(('insert into dx.iknow_tell(code,date,hbp,lbp,kp,v1p,v2p,hpp,lpp,openev,highev,lowev,closeev) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,day)+row))
                g_iu.log(logging.INFO,'dx tell handle progress[%0.2f%%] code[%s] date[%s]....'%(100*(handled/total),code,day))
                handled = handled+1
        g_tool.task(sqls)
        g_iu.log(logging.INFO,'dx handle told end[%s] executed insert sqls[%d]....'%(day,len(sqls)))

    def backupdata(self,zip=False):
        g_iu.log(logging.INFO,'dx backupdata start....')
        now = datetime.datetime.now()
        odir = os.path.join(os.path.join(g_home,'tmp'),'dx_data_%04d%02d%02d%02d%02d%02d'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
        g_iu.mkdir(odir)
        codes = g_tool.exesqlbatch('select distinct code from dx.iknow_data',None)
        for code in codes:
            data = g_tool.exesqlbatch('select code,date,open,high,low,close,volh,volwy from dx.iknow_data where code=%s order by date',(code[0],))
            ofn = os.path.join(odir,'%s.csv'%code[0])
            g_iu.dumpfile(ofn,data)
        if zip:
            cur = os.getcwd()
            os.chdir(odir)
            g_iu.execmd('zip -r %s.zip %s'%(odir,odir))
            g_iu.execmd('rm -fr %s'%odir)
            os.chdir(cur)
        g_iu.log(logging.INFO,'dx backupdata done output[%s]....'%oidr)
        
    def daily_task(self,name):
        g_iu.log(logging.INFO,'daily_task[%s] start....'%(name))
        self.dl()
        self.attr()
        self.told(name)
        g_iu.log(logging.INFO,'daily_task[%s] end successfully....'%(name))

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
            if taskname != pretask:
                self.daily_task(taskname)
                pretask = taskname
            time.sleep(5)

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-t', '--tell', action='store_true', dest='tell',default=False, help='tell task')
    parser.add_option('-b', '--backup', action='store_true', dest='backup',default=False, help='backup task')
    parser.add_option('-e', '--end', action='store', dest='end',default=None, help='tell task end day')
    parser.add_option('-i', '--input', action='store', dest='input',default=None, help='data dir')
    parser.add_option('-o', '--output', action='store', dest='output',default=None, help='output dir')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    ik = iknow()
    if ops.tell and ops.end:
        ik.tell(ops.end)
    if ops.backup:
        ik.backupdata(True)
    else:
        ik.run()

    
    
    
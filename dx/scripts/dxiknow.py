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
        self._rate = 0.001
        self._mincnt = 19
        self._minlength=360
        self._sqlbatch = 2000

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
                    shouldadd = g_tool.exesqlbatch('select date from hy.iknow_data_ex where code=%s and date not in (select date from dx.iknow_data where code=%s)',(code,code))
                    for adt in shouldadd:
                        g_iu.log(logging.INFO,'dx handle dl code[%s] date[%s]....'%(code,adt[0]))
                        row = g_tool.exesqlone('select code,date,open,high,low,close,volh,volwy from hy.iknow_data_ex where code=%s and date=%s',(code,adt[0]))
                        sqls.append(('insert into dx.iknow_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                except Exception,e:
                    g_iu.log(logging.INFO,'code[%s],date[%04d-%02d-%02d] local update exception[%s]'%(code,now.year,now.month,now.day,e))
            g_tool.task(sqls)
        except Exception,e:
            g_iu.log(logging.INFO,'dx dl exception[%s]....'%e)

    def _attr(self,date,yc,row):
        open = row[0]
        high = row[1]
        low = row[2]
        close = row[3]
        volwy = row[4]
        openzdf = float('%0.4f'%((open-yc)/yc))
        highzdf = float('%0.4f'%((high-yc)/yc))
        lowzdf = float('%0.4f'%((low-yc)/yc))
        closezdf = float('%0.4f'%((close-yc)/yc))
        useful = 1
        if lowzdf<-0.101:
            useful = 0
        osrc = 0.5
        csrc = 0.5
        if high!=low:
            osrc = float('%0.4f'%((open-low)/(high-low)))
            csrc = float('%0.4f'%((close-low)/(high-low)))
        rank = g_tool.exesqlone('select count(*) from dx.iknow_data where date=%s and volwy>%s',(date,volwy));
        rank = rank[0]+1
        return (openzdf,highzdf,lowzdf,closezdf,osrc,csrc,rank,useful)
            
    def attr(self):
        codes = self._codes()
        sqls = []
        mat = []
        g_iu.log(logging.INFO,'dx attr handle start....')
        cnt = 0
        for code in codes:
            start = g_tool.exesqlone('select date from dx.iknow_data where code=%s order by date limit 1',(code,))
            if len(start)==0:
                g_iu.log(logging.INFO,'dx attr handle code[%s] no data....'%(code))
                continue
            shouldadd = g_tool.exesqlbatch('select date from dx.iknow_data where code=%s and date>%s and date not in (select date from dx.iknow_attr where code=%s) order by date',(code,start[0],code))
            g_iu.log(logging.DEBUG,'dx attr handle code[%s] count[%d]....'%(code,len(shouldadd)))
            for adt in shouldadd:
                if (adt[0]>'2004-01-01'):
                    mat.append((code,adt[0]))
            g_iu.log(logging.INFO,'dx attr loading task[%d/%d--%d]....'%(cnt+1,len(codes),len(mat)))
            cnt = cnt+1

        g_iu.log(logging.INFO,'dx attr handle task load[%d]....'%(len(mat)))
        total=float(len(mat))
        prog = 0.0
        for i in range(len(mat)):
            data = g_tool.exesqlbatch('select open,high,low,close,volwy from dx.iknow_data where code=%s and date<=%s order by date desc limit 2',(mat[i][0],mat[i][1]))
            if data[1][4]==0:
                g_iu.log(logging.WARNING,'dx attr handle code[%s] date[%s] lastclose is zero'%(mat[i][0],mat[i][1]))
                continue
            attrs = self._attr(mat[i][1],data[1][4],data[0])
            sqls.append(('insert into dx.iknow_attr(code,date,openzdf,highzdf,lowzdf,closezdf,osrc,csrc,ranking,useful) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(mat[i][0],mat[i][1],attrs[0],attrs[1],attrs[2],attrs[3],attrs[4],attrs[5],attrs[6],attrs[7])))
            if len(sqls)>=self._sqlbatch:
                g_tool.task(sqls)
                sqls = []
                g_tool.reconn('dx')
            curprog = 100*(float((i+1))/total)
            if curprog-prog>=0.01:
                g_iu.log(logging.INFO,'dx attr handle progress[%0.2f%%]....'%(curprog))
                prog = curprog
        g_tool.task(sqls)
        g_iu.log(logging.INFO,'dx attr handle task done....')

    def _starting(self,code):
        default = '2005-01-04'
        sql = 'select date from dx.iknow_attr where code=%s order by date limit %d'%(code,self._minlength)
        data = g_tool.exesqlbatch(sql,None)
        if len(data)<self._minlength:
            g_iu.log(logging.DEBUG,'dx _starting code[%s] data is too short[%d/%d]....'%(code,len(data),self._minlength))
            return None
        else:
            start = data[-1][0]
            if start < default:
                return default
            return start

    def prepare(self):
        codes = self._codes()
        sqls = []
        mat = []
        g_iu.log(logging.INFO,'dx prepare handle start....')
        for code in codes:
            start = self._starting(code)
            if not start:
                g_iu.log(logging.INFO,'dx prepare handle code[%s] history is too short....'%(code))
                continue
            shouldadd = g_tool.exesqlbatch('select date from dx.iknow_attr where code=%s and date>=%s and date not in (select date from dx.iknow_prepare where code=%s) order by date',(code,start,code))
            for adt in shouldadd:
                dtrng = g_tool.exesqlbatch('select date from iknow_attr where code=%s and date<=%s order by date desc limit 120',(code,adt[0]))
                begin = dtrng[-1][0]
                g_iu.log(logging.DEBUG,'dx prepare loading code[%s] date[%s] begin[%s]....'%(code,adt[0],begin))
                mat.append((code,adt[0],begin))
            g_iu.log(logging.INFO,'dx prepare loading task[%d]....'%(len(mat)))
        g_iu.log(logging.INFO,'dx prepare handle task loaded[%d]....'%(len(mat)))
        total=float(len(mat))
        for i in range(len(mat)):
            data = g_tool.exesqlone('select avg(closezdf),std(closezdf),avg(highzdf-lowzdf),std(highzdf-lowzdf),avg(osrc),std(osrc),avg(csrc),std(csrc) from iknow_attr where code=%s and date<=%s and date>=%s',(mat[i][0],mat[i][1],mat[i][2]))
            sqls.append(('insert into dx.iknow_prepare(code,date,zdf120_ev,zdf120_std,zf120_ev,zf120_std,osrc120_ev,osrc120_std,csrc120_ev,csrc120_std) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(mat[i][0],mat[i][1],data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7])))
            if len(sqls)>=self._sqlbatch:
                g_tool.task(sqls)
                sqls = []
            g_iu.log(logging.INFO,'dx prepare handle progress[%0.2f%%]....'%(100*(float((i+1))/total)))
        g_tool.task(sqls)
        g_iu.log(logging.INFO,'dx prepare handle task done....')

    def _base(self,vol2,currow,lastrow):
        OPEN = 0
        HIGH = 1
        LOW = 2
        CLOSE = 3
        VOL = 4
        hb = 0
        if currow[HIGH]>lastrow[HIGH]:
            hb=1
        lb=0
        if currow[LOW]<lastrow[LOW]:
            lb=1
        k=0
        if currow[CLOSE]>currow[OPEN]:
            k=1
        v1 = 0
        if (currow[VOL]-lastrow[VOL])>0:
            v1 = 1
        v2 = 0
        if (currow[VOL]+vol2-2*lastrow[VOL])>0:
            v2 = 1
        return (hb,lb,k,v1,v2)
        
    def fillbase(self):
        g_tool.reconn('dx')
        codes = self._codes()
        sqls = []
        mat = []
        g_iu.log(logging.INFO,'dx fillbase handle start....')
        for code in codes:
            start = self._starting(code)
            if not start:
                g_iu.log(logging.INFO,'dx fillbase handle code[%s] history is too short....'%(code))
                continue
            shouldadd = g_tool.exesqlbatch('select date from dx.iknow_prepare where code=%s and date>=%s and date not in (select date from dx.iknow_base where code=%s) order by date',(code,start,code))
            for adt in shouldadd:
                mat.append((code,adt[0]))
                g_iu.log(logging.INFO,'dx fillbase loading task[%d]....'%(len(mat)))
        g_iu.log(logging.INFO,'dx fillbase handle task loaded[%d]....'%(len(mat)))
        total=float(len(mat))
        for i in range(len(mat)):
            g_iu.log(logging.DEBUG,'dx fillbase handling code[%s] date[%s]....'%(code,adt[0]))
            data = g_tool.exesqlbatch('select open,high,low,close,(close-open)*volh from iknow_data where code=%s and date<=%s order by date desc limit 3',(mat[i][0],mat[i][1]))
            fv = self._base(data[2][4],data[0],data[1])
            pres = g_tool.exesqlone('select zdf120_ev,zdf120_std,zf120_ev,zf120_std,scoreo120_ev,scoreo120_std,scorec120_ev,scorec120_std from dx.iknow_prepare where code=%s and date=%s',(mat[i][0],mat[i][1]))
            attrs = g_tool.exesqlone('select zdf,zf,scoreo,scorec from dx.iknow_attr where code=%s and date=%s',(mat[i][0],mat[i][1]))
            zdfz = float('%0.4f'%((attrs[0]-pres[0])/pres[1]))
            zfz = float('%0.4f'%((attrs[1]-pres[2])/pres[3]))
            scoreoz = float('%0.4f'%((attrs[2]-pres[4])/pres[5]))
            scorecz = float('%0.4f'%((attrs[3]-pres[6])/pres[7]))
                
            openf = float('%0.4f'%((data[0][1]-data[1][4])/data[1][4]))
            highf = float('%0.4f'%((data[0][2]-data[1][4])/data[1][4]))
            lowf = float('%0.4f'%((data[0][3]-data[1][4])/data[1][4]))
            closef = float('%0.4f'%((data[0][4]-data[1][4])/data[1][4]))
            useful = 1
            if lowf<-0.101:
                useful = 0
            sqls.append(('insert into dx.iknow_base(code,date,hb,lb,k,v1,v2,zdfz,zfz,scoreoz,scorecz,openf,highf,lowf,closef,useful) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,data[1][0],hb,lb,k,v1,v2,zdfz,zfz,scoreoz,scorecz,openf,highf,lowf,closef,useful)))
            if len(sqls)>=self._sqlbatch:
                g_tool.task(sqls)
                sqls = []
        g_tool.task(sqls)
            
    def poles(self):
        g_tool.reconn('dx')
        codes = self._codes()
        sqls = []
        for code in codes:
            g_iu.log(logging.INFO,'dx handle poles code[%s]....'%(code))
            start = g_tool.exesqlone('select date from dx.iknow_data where code=%s order by date limit 1',(code,))
            if len(start)==0:
                continue
            start = start[0]
            end = g_tool.exesqlone('select date from dx.iknow_data where code=%s order by date desc limit 1',(code,))
            if len(end)==0:
                continue
            end = end[0]
            shouldadd = g_tool.exesqlbatch('select date from dx.iknow_data where code=%s and date>%s and date<%s and date not in (select date from dx.iknow_poles where code=%s) order by date',(code,start,end,code))
            shoulds = set()
            for s in shouldadd:
                shoulds.add(s[0])
            data = g_tool.exesqlbatch('select date,high,low from dx.iknow_data where code=%s order by date',(code,))
            for i in range(1,len(data)-1):
                g_iu.log(logging.DEBUG,'dx poles handling code[%s] date[%s]....'%(code,data[i][0]))
                if data[i][0] in shoulds:
                    hp = 0
                    if data[i][1]>data[i-1][1] and data[i][1]>data[i+1][1]:
                        hp = 1
                    lp = 0
                    if data[i][2]<data[i-1][2] and data[i][2]<data[i+1][2]:
                        lp = 1
                    sqls.append(('insert into dx.iknow_poles(code,date,hp,lp) values(%s,%s,%s,%s)',(code,data[i][0],hp,lp)))
            if len(sqls)>=self._sqlbatch:
                g_tool.task(sqls)
                sqls = []
        g_tool.task(sqls)

    def _extract(self,simmat):
        if len(simmat)==0:
            return ()
        itemcnt = len(simmat[0])
        perf = [[row[i] for row in simmat] for i in range(itemcnt)]
        row = []
        for p in perf:
            row.append(float('%0.4f'%(float(sum(p))/float(len(p)))))
        return tuple(row)

    def _filter(self,fv,baseset):
        ds = []
        for row in baseset:
            d = abs(fv[0]-row[0])+abs(fv[1]-row[1])+abs(fv[2]-row[2])+abs(fv[3]-row[3])
            ds.append((d,row[4],row[5]))
        thv = max(int(len(ds)*self._rate),min(len(ds),self._mincnt))
        ds = ds[:thv]
        data = []
        for dd in ds:
            sim = g_tool.exesqlone('select hb,lb,k,v1,v2,zdfz,zfz,scoreoz,scorecz,openf,highf,lowf,closef from dx.iknow_base where code=%s and date>%s and useful=1 order by date limit 1',(dd[1],dd[2]))
            simpoles = g_tool.exesqlone('select hp,lp from dx.iknow_poles where code=%s and date>%s order by date limit 1',(dd[1],dd[2]))
            if len(sim)>0 and len(simpoles)>0:
                data.append((sim[0],sim[1],sim[2],sim[3],sim[4],sim[5],sim[6],sim[7],sim[8],sim[9],sim[10],sim[11],sim[12],simpoles[0],simpoles[1]))
        return data

    def tell(self):
        g_tool.reconn('dx')
        codes = self._codes()
        sqls = []
        allset = {}
        g_iu.log(logging.INFO,'dx handle tell collect start....')
        for code in codes:
            start = '2018-04-04'
            shouldadd = g_tool.exesqlbatch('select date from dx.iknow_data where code=%s and date>%s and date not in (select date from dx.iknow_tell where code=%s) and date in (select date from dx.iknow_base where code=%s)',(code,start,code,code))
            for adt in shouldadd:
                if allset.has_key(adt[0]):
                    allset[adt[0]].append(code)
                else:
                    allset[adt[0]]=[code]
        g_iu.log(logging.INFO,'dx handle tell collect end....')

        dates = allset.keys()
        dates.sort()
        for dt in dates:
            g_iu.log(logging.INFO,'dx handle tell date[%s]....'%(dt))
            fvs = g_tool.exesqlbatch('select hb,lb,k,v1,v2,code,zdfz,zfz,scoreoz,scorecz from dx.iknow_base where date=%s',(dt,))
            allfvs = {}
            for fv in fvs:
                if allfvs.has_key(fv[:5]):
                    allfvs[fv[:5]].append(fv[5:])
                else:
                    allfvs[fv[:5]]=[fv[5:]]
            for v in allfvs.keys():
                baseset = g_tool.exesqlbatch('select zdfz,zfz,scoreoz,scorecz,code,date from iknow_base where hb=%s and lb=%s and k=%s and v1=%s and v2=%s and date<%s',(v[0],v[1],v[2],v[3],v[4],dt))
                cins = allfvs[v]
                cins.sort()
                for cin in allfvs[v]:
                    g_iu.log(logging.INFO,'dx handle tell code[%s] date[%s]....'%(cin[0],dt))
                    data = self._filter((cin[1],cin[2],cin[3],cin[4]),baseset)
                    tell = self._extract(data)
                    sqls.append(('insert into dx.iknow_tell(code,date,hb,lb,k,v1,v2,zdfz,zfz,scoreoz,scorecz,openf,highf,lowf,closef,hp,lp) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(cin[0],dt,tell[0],tell[1],tell[2],tell[3],tell[4],tell[5],tell[6],tell[7],tell[8],tell[9],tell[10],tell[11],tell[12],tell[13],tell[14])))
                if len(sqls)>=self._sqlbatch:
                    g_tool.task(sqls)
                    sqls = []
        g_tool.task(sqls)

    def daily_task(self,name,retry):
        while retry>0:
            try:
                g_iu.log(logging.INFO,'daily_task[%s] start retry[%d]....'%(name,retry))
                self.dl()
                self.attr()
                self.poles()
                self.prepare()
                self.fillbase()
                self.tell()
                g_iu.log(logging.INFO,'daily_task[%s] end successfully retry[%d]....'%(name,retry))
                return True
            except Exception,e:
                g_iu.log(logging.ERROR,'daily_task[%s] retry[%d] exception[%s]'%(name,retry,e))
            retry = retry-1
        return False

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
                self.daily_task(taskname,1)
                pretask = taskname
            time.sleep(5)

if __name__ == "__main__":
    ik = iknow()
    #ik.prepare()
    #ik.poles()
    #ik.fillbase()
    #ik.dl()
    ik.attr()
    #ik.tell()
    
    
    
    
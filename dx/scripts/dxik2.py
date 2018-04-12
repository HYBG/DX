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
        self._minlength=360
        self._sqlbatch = 1500
        self._defaultstart = '2005-01-04'

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

    def _starting(self,code):
        sql = 'select date from dx.iknow_data where code=%s order by date limit %d'%(code,self._minlength)
        data = g_tool.exesqlbatch(sql,None)
        if len(data)<self._minlength:
            g_iu.log(logging.DEBUG,'dx _starting code[%s] data is too short[%d/%d]....'%(code,len(data),self._minlength))
            return None
        else:
            start = data[-1][0]
            if start < self._defaultstart:
                return self._defaultstart
            return start

    def _baseattr(self,currow,lastrow,beforerow):
        DATE = 0
        OPEN = 1
        HIGH = 2
        LOW = 3
        CLOSE = 4
        VOL = 5
        openzdf = (currow[OPEN]-lastrow[CLOSE])/lastrow[CLOSE]
        highzdf = (currow[HIGH]-lastrow[CLOSE])/lastrow[CLOSE]
        lowzdf = (currow[LOW]-lastrow[CLOSE])/lastrow[CLOSE]
        closezdf = (currow[CLOSE]-lastrow[CLOSE])/lastrow[CLOSE]
        osrc = 0.5
        csrc = 0.5
        if currow[HIGH]!=currow[LOW]:
            osrc = (currow[OPEN]-currow[LOW])/(currow[HIGH]-currow[LOW])
            csrc = (currow[CLOSE]-currow[LOW])/(currow[HIGH]-currow[LOW])
        hb = 0
        lb = 0
        if currow[HIGH] > lastrow[HIGH]:
            hb = 1
        if currow[LOW] < lastrow[LOW]:
            lb = 1
        k = 0
        if currow[CLOSE]>currow[OPEN]:
            k = 1
        v1 = 0
        if (currow[VOL]-lastrow[VOL])>0:
            v1 = 1
        v2 = 0
        if (currow[VOL]+beforerow[VOL]-2*lastrow[VOL])>0:
            v2 = 1
        useful = 1
        if lowzdf<=-0.11:
            useful = 0
        hp = 0
        lp = 0
        if (lastrow[HIGH]>currow[HIGH]) and (lastrow[HIGH]>beforerow[HIGH]):
            hp = 1
        if (lastrow[LOW]<currow[LOW]) and (lastrow[LOW]<beforerow[LOW]):
            lp = 1
        return ('%0.4f'%openzdf,'%0.4f'%highzdf,'%0.4f'%lowzdf,'%0.4f'%closezdf,'%0.4f'%osrc,'%0.4f'%csrc,hb,lb,k,v1,v2,useful,hp,lp)

    def attr(self):
        g_tool.reconn('dx')
        codes = self._codes()
        g_iu.log(logging.INFO,'dx attr handle start....')
        total = float(len(codes))
        handled = 1
        for code in codes:
            sqls = []
            upsqls = []
            begin = self._starting(code)
            if not begin:
                g_iu.log(logging.INFO,'dx attr handle code[%s] no data....'%(code))
                continue
            g_iu.log(logging.DEBUG,'dx handle attr code[%s] begin[%s]....'%(code,begin))
            shouldadd = g_tool.exesqlbatch('select date from dx.iknow_data where code=%s and date>%s and date not in (select date from dx.iknow_attr where code=%s) order by date',(code,begin,code))
            for adt in shouldadd:
                data = g_tool.exesqlbatch('select date,open,high,low,close,(close-open)*volh from dx.iknow_data where code=%s and date<=%s order by date desc limit 3',(code,adt[0]))
                g_iu.log(logging.DEBUG,'dx handle attr code[%s] date[%s]....'%(code,adt[0]))
                info = self._baseattr(data[0],data[1],data[2])
                sqls.append(('insert into dx.iknow_attr(code,date,openzdf,highzdf,lowzdf,closezdf,opensrc,closesrc,hb,lb,k,v1,v2,useful,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,adt[0])+info[:12]+(1,)))
                upsqls.append(('update dx.iknow_attr set hp=%s,lp=%s,next=%s,status=2 where code=%s and date=%s',(info[12],info[13],adt[0],code,data[1][0])))
            g_tool.task(sqls)
            g_tool.task(upsqls)
            g_iu.log(logging.INFO,'dx attr handle progress[%0.2f%%]....'%(100*(handled/total)))
            handled = handled+1
        g_iu.log(logging.INFO,'dx attr handle done....')
        
    def _divide(self,stdv):
        dv = 1
        if stdv<-0.43:
            dv = 0
        elif stdv>0.43:
            dv = 2
        return dv
        
    def _stdv(self,lis):
        ev = sum(lis)/float(len(lis))
        all = 0
        for item in lis:
            all = all + (item-ev)**2
        std = all**0.5
        stdv = (lis[0]-ev)/std
        return stdv
        
    def _transfer(self,data):
        zdfmat = []
        zfmat = []
        osrcmt = []
        csrcmt = []
        for i in range(1,len(data)):
            yc = data[i-1][4]
            open = data[i][1]
            high = data[i][2]
            low = data[i][3]
            close = data[i][4]
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
    
    def _divmoreinfo(self,data):
        stdvs = self._moreinfo(data)
        dvizdf = self._divide(stdvs[0])
        dvizf = self._divide(stdvs[1])
        dviosrc = self._divide(stdvs[2])
        dvicsrc = self._divide(stdvs[3])
        return (dvizdf,dvizf,dviosrc,dvicsrc)

    def _locdate(self,data,date):
        start = 0
        end = len(data)-1
        while start <= end :
            mid = (start+end)/2
            if data[mid][0] == date:
                return mid
            elif data[mid][0] > date:
                end = mid-1
            else:
                start = mid+1
        return -1

    def freshen(self):
        g_tool.reconn('dx')
        codes = self._codes()
        g_iu.log(logging.INFO,'dx freshen handle start....')
        total = float(len(codes))
        handled = 1
        for code in codes:
            sqls = []
            dts = g_tool.exesqlbatch('select date from dx.iknow_attr where code=%s and status=2 order by date',(code,))
            data = g_tool.exesqlbatch('select date,open,high,low,close from dx.iknow_data where code=%s order by date',(code,))
            for dt in dts:
                try:
                    g_iu.log(logging.DEBUG,'dx handle freshen code[%s] date[%s]....'%(code,dt[0]))
                    dtpos = self._locdate(data,dt[0])
                    if dtpos == -1:
                        g_iu.log(logging.ERROR,'dx freshen handle data date[%d] not found'%dt[0])
                        continue
                    need = data[dtpos-120:dtpos+1]
                    dmi = self._divmoreinfo(need)
                    sqls.append(('update dx.iknow_attr set zdfg_120=%s,zfg_12=%s,osrcg_120=%s,csrcg_120=%s,status=3 where code=%s and date=%s',(dmi[0],dmi[1],dmi[2],dmi[3],code,dt)))
                except Exception,e:
                    g_iu.log(logging.WARNING,'dx freshen handle exception[%s]'%(e))
            g_tool.task(sqls)
            g_iu.log(logging.INFO,'dx freshen handle progress[%0.2f%%]....'%(100*(handled/total)))
            handled = handled+1
        g_iu.log(logging.INFO,'dx freshen handle done....')

    def attr2(self):
        g_tool.reconn('dx')
        codes = self._codes()
        g_iu.log(logging.INFO,'dx attr2 handle start....')
        total = float(len(codes))
        handled = 1
        for code in codes:
            sqls = []
            upsqls = []
            begin = self._starting(code)
            if not begin:
                g_iu.log(logging.INFO,'dx attr2 handle code[%s] no data....'%(code))
                continue
            g_iu.log(logging.DEBUG,'dx handle attr2 code[%s] begin[%s]....'%(code,begin))
            shouldadd = g_tool.exesqlbatch('select date from dx.iknow_data where code=%s and date>%s and date not in (select date from dx.iknow_attr2 where code=%s) order by date',(code,begin,code))
            data = g_tool.exesqlbatch('select date,open,high,low,close,(close-open)*volh from dx.iknow_data where code=%s',(code,))
            for adt in shouldadd:
                dtpos = self._locdate(data,adt[0])
                if dtpos == -1:
                    g_iu.log(logging.ERROR,'dx attr2 handle data date[%d] not found'%adt[0])
                    continue
                need = data[dtpos-3:dtpos+1]
                g_iu.log(logging.DEBUG,'dx handle attr2 code[%s] date[%s]....'%(code,adt[0]))
                info = self._baseattr(need[2],need[1],need[0])
                sqls.append(('insert into dx.iknow_attr2(code,date,openzdf,highzdf,lowzdf,closezdf,opensrc,closesrc,hb,lb,k,v1,v2,useful,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,adt[0])+info[:12]+(1,)))
                upsqls.append(('update dx.iknow_attr2 set hp=%s,lp=%s,next=%s,status=2 where code=%s and date=%s',(info[12],info[13],adt[0],code,data[1][0])))
            g_tool.task(sqls)
            g_tool.task(upsqls)
            g_iu.log(logging.INFO,'dx attr2 handle progress[%0.2f%%]....'%(100*(handled/total)))
            handled = handled+1
        g_iu.log(logging.INFO,'dx attr2 handle done....')

    def freshen2(self):
        g_tool.reconn('dx')
        codes = self._codes()
        g_iu.log(logging.INFO,'dx freshen2 handle start....')
        total = float(len(codes))
        handled = 1
        for code in codes:
            sqls = []
            dts = g_tool.exesqlbatch('select date from dx.iknow_attr2 where code=%s and status=2 order by date',(code,))
            data = g_tool.exesqlbatch('select date,open,high,low,close from dx.iknow_data where code=%s order by date',(code,))
            for dt in dts:
                try:
                    g_iu.log(logging.DEBUG,'dx handle freshen2 code[%s] date[%s]....'%(code,dt[0]))
                    dtpos = self._locdate(data,dt[0])
                    if dtpos == -1:
                        g_iu.log(logging.ERROR,'dx freshen2 handle data date[%d] not found'%dt[0])
                        continue
                    need = data[dtpos-120:dtpos+1]
                    mi = self._moreinfo(need)
                    sqls.append(('update dx.iknow_attr2 set zdfg_120=%s,zfg_12=%s,osrcg_120=%s,csrcg_120=%s,status=3 where code=%s and date=%s',(mi[0],mi[1],mi[2],mi[3],code,dt)))
                except Exception,e:
                    g_iu.log(logging.WARNING,'dx freshen2 handle exception[%s]'%(e))
            g_tool.task(sqls)
            g_iu.log(logging.INFO,'dx freshen2 handle progress[%0.2f%%]....'%(100*(handled/total)))
            handled = handled+1
        g_iu.log(logging.INFO,'dx freshen2 handle done....')
        
    def _tell(self,code,date=None):
        fv = None
        dt = None
        if not date:
            ldfv = g_tool.exesqlone('select date,hb,lb,k,v1,v2,zdfg_120,zfg_120,osrcg_120,csrcg_120 from dx.iknow_attr where code=%s and status=3 order by date desc limit 1',(code,))
            if len(ldfv)==0:
                return None
            fv = ldfv[1:]
            dt = ldfv[0]
        else:
            ldfv = g_tool.exesqlone('select hb,lb,k,v1,v2,zdfg_120,zfg_120,osrcg_120,csrcg_120 from dx.iknow_attr where code=%s and date=%s and status=3',(code,date))
            if len(ldfv)==0:
                return None
            fv = ldfv
            dt = date
        indexs = g_tool.exesqlbatch('select code,next from dx.iknow_attr where hb=%s and lb=%s and k=%s and v1=%s and v2=%s and zdfg_120=%s and zfg_120=%s and osrcg_120=%s and csrcg_120=%s and status=3',fv)
        lis = [0,0,0,0,0,0,0,0,0]
        ignore = 0
        for inx in indexs:
            row = g_tool.exesqlone('select hb,lb,k,hp,lp,openzdf,highzdf,lowzdf,closezdf from dx.iknow_attr where code=%s and date=%s and useful=1 and status>=2',(inx[0],inx[1]))
            if len(row)==0:
                ignore = ignore+1
                continue
            for i in range(9):
                lis[i] = lis[i]+row[i]
        cnt = len(indexs)-ignore
        if cnt>0:
            story = []
            for j in range(9):
                story.append(lis[j]/float(cnt))
            return tuple(story)+(dt,)
        return None

    def tell(self,start=None):
        g_tool.reconn('dx')
        codes = self._codes()
        sqls = []
        total = float(len(codes))
        handled = 1
        g_iu.log(logging.INFO,'dx handle tell start....')
        for code in codes:
            if start:
                shouldadd = g_tool.exesqlbatch('select date from dx.iknow_attr where code=%s and date>%s and date not in (select date from dx.iknow_tell where code=%s)',(code,start,code))
                for adt in shouldadd:
                    story = self._tell(code,adt[0])
                    if not story:
                        continue
                    sqls.append(('insert into dx.iknow_tell(code,date,hbp,lbp,kp,hpp,lpp,openev,highev,lowev,closeev) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'),(code,adt[0],)+story[:-1])
            else:
                story = self._tell(code)
                if not story:
                    continue
                sqls.append(('insert into dx.iknow_tell(code,date,hbp,lbp,kp,hpp,lpp,openev,highev,lowev,closeev) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'),(code,story[-1],)+story[:-1])
            g_tool.task(sqls)
            g_iu.log(logging.INFO,'dx tell handle progress[%0.2f%%]....'%(100*(handled/total)))
            handled = handled+1
        g_iu.log(logging.INFO,'dx handle tell end....')
        
    def backupset(self):
        odir = os.path.join(os.path.join(g_home,'dx'),'backupset')
        if 

    def daily_task(self,name,retry):
        while retry>0:
            try:
                g_iu.log(logging.INFO,'daily_task[%s] start retry[%d]....'%(name,retry))
                self.dl()
                self.attr()
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
    #ik.dl()
    ik.attr()
    #ik.tell()
    
    
    
    
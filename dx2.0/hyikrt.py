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

class hyhq:
    def __init__(self,code,open,high,low,close,lastclose,volwy,volh,date,time):
        self.code = code
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volwy = volwy
        self.lastclose = lastclose
        self.volh = volh
        self.date = date
        self.time = time
        
    def _multiple(self):
        dt = datetime.datetime.strptime(self.time,'%H:%M:%S')
        if dt.hour==9 and dt.minute<40:
            return 24.0/1.0
        elif dt.hour==9 and dt.minute<50:
            return 24.0/2.0
        elif dt.hour==9 and dt.minute<59:
            return 24.0/3.0
        elif dt.hour==10 and dt.minute<10:
            return 24.0/4.0
        elif dt.hour==10 and dt.minute<20:
            return 24.0/5.0
        elif dt.hour==10 and dt.minute<30:
            return 24.0/6.0
        elif dt.hour==10 and dt.minute<40:
            return 24.0/7.0
        elif dt.hour==10 and dt.minute<50:
            return 24.0/8.0
        elif dt.hour==10 and dt.minute<59:
            return 24.0/9.0
        elif dt.hour==11 and dt.minute<10:
            return 24.0/10.0
        elif dt.hour==11 and dt.minute<20:
            return 24.0/11.0
        elif dt.hour==11 and dt.minute<30:
            return 24.0/12.0
        elif dt.hour==13 and dt.minute<10:
            return 24.0/13.0
        elif dt.hour==13 and dt.minute<20:
            return 24.0/14.0
        elif dt.hour==13 and dt.minute<30:
            return 24.0/15.0
        elif dt.hour==13 and dt.minute<40:
            return 24.0/16.0
        elif dt.hour==13 and dt.minute<50:
            return 24.0/17.0
        elif dt.hour==13 and dt.minute<59:
            return 24.0/18.0
        elif dt.hour==14 and dt.minute<10:
            return 24.0/19.0
        elif dt.hour==14 and dt.minute<20:
            return 24.0/20.0
        elif dt.hour==14 and dt.minute<30:
            return 24.0/21.0
        elif dt.hour==14 and dt.minute<40:
            return 24.0/22.0
        elif dt.hour==14 and dt.minute<50:
            return 24.0/23.0
        elif dt.hour==14 and dt.minute<59:
            return 24.0/24.0
        return 1.0
        
    def _fv(self,hexp,lexp,kexp):
        fv = 0
        if hexp and not lexp and kexp:
            fv = 1
        elif hexp and not lexp and not kexp:
            fv = 2
        elif not hexp and lexp and kexp:
            fv = 3
        elif not hexp and lexp and not kexp:
            fv = 4
        elif hexp and lexp and kexp:
            fv = 5
        elif hexp and lexp and not kexp:
            fv = 6
        elif not hexp and not lexp and kexp:
            fv = 7
        elif not hexp and not lexp and not kexp:
            fv = 8
        return fv
        
    def _middles(self,all,sets):
        if len(sets)!=0:
            prob = round(100*(float(len(sets))/all),2)
            opens = []
            highs = []
            lows = []
            closes = []
            for row in sets:
                opens.append(row[0])
                highs.append(row[1])
                lows.append(row[2])
                closes.append(row[3])
            opens.sort()
            highs.sort()
            lows.sort()
            closes.sort()
            return (prob,opens[len(opens)/2],highs[len(highs)/2],lows[len(lows)/2],closes[len(closes)/2])
        return (0,0,0,0,0)

    def _next(self,fv,vr,hr,lr,hopen,chr,clr,hclose):
        mat = []
        vcond = 'vr<=0.8'
        if vr>=1.5:
            vcond = 'vr>=1.5'
        elif vr>=0.5:
            vcond = 'vr>0.5 and vr<1.5'
        all = g_tool.exesqlone('select count(*) from hy.iknow_feature where fv=%s and '+vcond+' and not (highr<=%s and (next=1 or next=2 or next=5 or next=6)) and not (lowr>=%s and (next=3 or next=4 or next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8))',(fv,hr,lr,hr,lr))
        ocond = 'openr<0'
        if hopen:
            ocond = 'openr>0'
        hlcond = 'highr<=%s and lowr>=%s'%(chr,clr)
        if hclose==1:
            hlcond = 'highr<=%s and lowr<=%s'%(chr,clr)
        elif hclose == 3:
            hlcond = 'highr>=%s and lowr>=%s'%(chr,clr)
        closes = g_tool.exesqlbatch('select closer from hy.iknow_feature where ffv=%s and '+ocond+' and '+hlcond,(fv,))
        closemid = 0.0
        if len(closes)!=0:
            closes = list(closes)
            closes.sort()
            closemid = closes[len(closes)/2][0]
        c1 = g_tool.exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=1',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
        mat.append(self._middles(all[0],c1))
        c2 = g_tool.exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=2',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
        mat.append(self._middles(all[0],c2))
        c3 = g_tool.exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=3',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
        mat.append(self._middles(all[0],c3))
        c4 = g_tool.exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=4',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
        mat.append(self._middles(all[0],c4))
        c5 = g_tool.exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=5',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
        mat.append(self._middles(all[0],c5))
        c6 = g_tool.exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=6',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
        mat.append(self._middles(all[0],c6))
        c7 = g_tool.exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=7',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
        mat.append(self._middles(all[0],c7))
        c8 = g_tool.exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=8',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
        mat.append(self._middles(all[0],c8))
        return (all[0],closemid,mat)

    def zdf(self):
        return round(100*((self.close-self.lastclose)/self.lastclose),2)

    def build(self,stone):
        hb = 0
        if self.high > stone.lasthigh:
            hb = 1
        lb = 0
        if self.low < stone.lastlow:
            lb = 1
        csrc = 50.0
        if self.high!=self.low:
            csrc = round(100*((self.close-self.low)/(self.high-self.low)),2)
        high = stone.high8
        if self.high>high:
            high = self.high
        low = stone.low8
        if self.low<low:
            low = self.low
        k = 50.0
        d = 50.0
        if high != low:
            rsv = 100*((self.close-low)/(high-low))
            k = (2.0*stone.lastk+rsv)/3.0
            d = (2.0*stone.lastd+k)/3.0
        macdparan1 = 12
        macdparan2 = 26
        macdparan3 = 9
        emaf = 2*self.close/(macdparan1+1)+(macdparan1-1)*stone.emaf/(macdparan1+1)
        emas = 2*self.close/(macdparan2+1)+(macdparan2-1)*stone.emas/(macdparan2+1)
        diff = round(emaf-emas,4)
        dea  = round(2*diff/(macdparan3+1)+(macdparan3-1)*stone.dea/(macdparan3+1),4)
        macd = round(2*(diff-dea),4)
        ma5 = round((stone.s4+self.close)/5.0,2)
        ma10 = round((stone.s9+self.close)/10.0,2)
        ma20 = round((stone.s19+self.close)/20.0,2)
        ma30 = round((stone.s29+self.close)/30.0,2)
        ma60 = round((stone.s59+self.close)/60.0,2)
        vol = self.volwy*self._multiple()
        vr = round(vol/((stone.vol4+vol)/5.0),2)
        hr = round((self.high-self.close)/self.close,4)
        lr = round((self.low-self.close)/self.close,4)
        fv = '%s%d'%(stone.cfv,self._fv(self.high>stone.lasthigh,self.low<stone.lastlow,self.close>self.open))
        chr = round((self.high-self.lastclose)/self.lastclose,4)
        clr = round((self.low-self.lastclose)/self.lastclose,4)
        ccr = round((self.close-self.lastclose)/self.lastclose,4)
        pos = 2
        if self.close>(self.high-self.low)*0.8+self.low:
            pos = 3
        elif self.close<(self.high-self.low)*0.2+self.low:
            pos = 1
        mat = self._next(fv,vr,hr,lr,self.open>self.lastclose,chr,clr,pos)
        datetime = '%s %s'%(self.date,self.time)
        return ('insert into hy.iknow_rt(code,datetime,name,industry,zdf,hb,lb,csrc,volwy,vr,k,d,macd,fv,fvcnt,close,closemid,ma5,ma10,ma20,ma30,ma60,prob1,openmid1,highmid1,lowmid1,closemid1,prob2,openmid2,highmid2,lowmid2,closemid2,prob3,openmid3,highmid3,lowmid3,closemid3,prob4,openmid4,highmid4,lowmid4,closemid4,prob5,openmid5,highmid5,lowmid5,closemid5,prob6,openmid6,highmid6,lowmid6,closemid6,prob7,openmid7,highmid7,lowmid7,closemid7,prob8,openmid8,highmid8,lowmid8,closemid8) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(self.code,datetime,stone.name,stone.industry,self.zdf(),hb,lb,csrc,self.volwy,vr,k,d,macd,fv,mat[0],self.close,mat[1],ma5,ma10,ma20,ma30,ma60,mat[2][0][0],mat[2][0][1],mat[2][0][2],mat[2][0][3],mat[2][0][4],mat[2][1][0],mat[2][1][1],mat[2][1][2],mat[2][1][3],mat[2][1][4],mat[2][2][0],mat[2][2][1],mat[2][2][2],mat[2][2][3],mat[2][2][4],mat[2][3][0],mat[2][3][1],mat[2][3][2],mat[2][3][3],mat[2][3][4],mat[2][4][0],mat[2][4][1],mat[2][4][2],mat[2][4][3],mat[2][4][4],mat[2][5][0],mat[2][5][1],mat[2][5][2],mat[2][5][3],mat[2][5][4],mat[2][6][0],mat[2][6][1],mat[2][6][2],mat[2][6][3],mat[2][6][4],mat[2][7][0],mat[2][7][1],mat[2][7][2],mat[2][7][3],mat[2][7][4]))

class hystone:
    def __init__(self,code,date,name,industry,high8,low8,lastk,lastd,emaf,emas,dea,s4,s9,s19,s29,s59,lasthigh,lastlow,cfv,vol4):
        self.code = code
        self.date = date
        self.name = name
        self.industry = industry
        self.high8 = high8
        self.low8 = low8
        self.lastk = lastk
        self.lastd = lastd
        self.emaf = emaf
        self.emas = emas
        self.dea = dea
        self.s4 = s4
        self.s9 = s9
        self.s19 = s19
        self.s29 = s29
        self.s59 = s59
        self.lasthigh = lasthigh
        self.lastlow = lastlow
        self.cfv = cfv
        self.vol4 = vol4

class hyrt:
    def __init__(self):
        self._stone = {}
        g_tool.conn('hy')
        self._reload()
        self._logger = g_iu.createlogger('hyrt',os.path.join(os.path.join(g_home,'log'),'hyrt.log'),logging.INFO)

    def __del__(self):
        pass

    def _reload(self):
        g_tool.reconn('hy')
        data = g_tool.exesqlbatch('select code,date,high8,low8,vol4,s4,s9,s19,s29,s59 from hy.iknow_stone where active=1 order by code', None)
        for row in data:
            names = g_tool.exesqlone('select name,tag from hy.iknow_tags where code=%s and tagtype=%s',(row[0],'industry'))
            hl = g_tool.exesqlone('select high,low from hy.iknow_data where code=%s and date=%s',(row[0],row[1]))
            attrs = g_tool.exesqlone('select k,d,emaf,emas,dea from hy.iknow_attr where code=%s and date=%s',(row[0],row[1]))
            ffv = g_tool.exesqlone('select ffv from hy.iknow_feature where code=%s and date=%s',(row[0],row[1]))
            if len(names)!=0 and names[0] and len(hl)!=0 and hl[0] and len(attrs)!=0 and attrs[0] and len(ffv)!=0 and ffv[0]:
                self._stone[row[0]] = hystone(row[0],row[1],names[0],names[1],row[2],row[3],attrs[0],attrs[1],attrs[2],attrs[3],attrs[4],row[5],row[6],row[7],row[8],row[9],hl[0],hl[1],ffv[0][1:],row[4])

    def _codes(self):
        codes = self._stone.keys()
        codes.sort()
        return codes

    def _rtprice(self):
        codeliststr = ''
        codes = self._codes()
        for code in codes:
            market = None
            if code[:2]=='60' or code[0]=='5':
                market = 'sh'
            else:
                market = 'sz'
            codeliststr = codeliststr + '%s%s,'%(market,code)
        url = 'http://hq.sinajs.cn/list=%s'%(codeliststr[:-1])
        try:
            data = urllib2.urlopen(url).readlines()
            i = 0
            lis = []
            for line in data:
                try:
                    info = line.split('"')[1].split(',')
                    now = datetime.datetime.now()
                    if int(info[8])>0 and info[30]=='%04d-%02d-%02d'%(now.year,now.month,now.day):
                        hq = hyhq(codes[i],float(info[1]),float(info[4]),float(info[5]),float(info[3]),float(info[2]),float(info[9])/10000.0,float(info[8])/100,info[30],info[31])
                        lis.append(hq)
                except Exception, e:
                    self._logger.error('get current price codes[%s] exception[%s]'%(codes[i],e))
                i = i+1
            return lis
        except Exception, e:
            self._logger.error('get current price codes[%d] url[%s] exception[%s]'%(len(codes),url,e))
            return None

    def rttask(self):
        g_tool.reconn('hy')
        self._logger.info('rt_task start....')
        hqlis = self._rtprice()
        sqls = [('update hy.iknow_rt set active=active+1',None)]
        self._logger.info('rt_task get hq list[%d]....'%len(hqlis))
        hbc = 0
        lbc = 0
        csrc = 0
        for hq in hqlis:
            sqls.append(hq.build(self._stone[hq.code]))
            if hq.high>self._stone[hq.code].lasthigh:
                hbc = hbc + 1
            if hq.low<self._stone[hq.code].lastlow:
                lbc = lbc + 1
            if hq.high==hq.low:
                csrc = csrc + 50.0
            else:
                csrc = csrc + round(100*((hq.close-hq.low)/(hq.high-hq.low)),2)
        
        if len(sqls)>1:
            g_tool.task(sqls)
        self._logger.info('rt_task end successfully sqls[%d]....'%(len(sqls)-1))

    def _righttime(self,now):
        tt = (now.hour,now.minute)
        all = [(9,31),(9,41),(9,51),(10,1),(10,11),(10,21),(10,31),(10,41),(10,51),(11,1),(11,11),(11,21),(13,10),(13,20),(13,30),(13,40),(13,50),(14,0),(14,10),(14,20),(14,30),(14,40),(14,50),(15,0)]
        if tt in all:
            return True 
        return False

    def run(self):
        open = False
        if g_tool.isopenday():
            open = True
        while 1:
            now = datetime.datetime.now()
            if open:
                if self._righttime(now):
                    self.task()
            else:
                otime = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=9,minute=30,second=0)
                ctime = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=15,minute=10,second=0)
                if now >= otime and now < ctime and g_tool.isopenday():
                    open = True
                    self._logger.info('market is open....')
                    continue
                if now>=ctime:
                    open = False
                    self._logger.info('market is closed....')
            time.sleep(5)

if __name__ == "__main__":
    ik = hyrt()
    ik.run()
    
    
    
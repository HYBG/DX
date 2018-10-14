#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import Queue
import MySQLdb
import urllib2
import threading
import Queue
import ConfigParser
from socket import *
from bs4 import BeautifulSoup
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
from ikbase import ikbase
from ikbase import ikmessage
from ikbase import ikset
from ikbase import ikobj

HY_TASK_REALTIME = 'HY_TASK_REALTIME'
HY_TASK_AFTERCLOSE = 'HY_TASK_AFTERCLOSE'
HY_TASK_BEFOREOPEN = 'HY_TASK_BEFOREOPEN'
HY_TASK_UPDATEINFO = 'HY_TASK_UPDATEINFO'

class iktask(ikbase):
    def __init__(self,conf):
        ikbase.__init__(self,conf)
        self._tasklist = []
        self._rts = []
        config = ConfigParser.ConfigParser()
        config.read(conf)
        self._datastart = config.get('iktask','data_start_default','1987-05-07')
        self._parsert(config.get('iktask','realtime_task'))
        self._afterbegin = config.get('iktask','close_task_begin','1700')
        self._featuremin = config.getint('iktask','feature_length_min')
        self._featurestart = config.get('iktask','feature_start_default','2005-01-01')
        self.setsleepinterval(config.getint('iktask','sleep_interval'))
        self._watchmax = config.getint('iktask','watch_max')
        self._watchvolmin = config.getint('iktask','watch_volume_min')
        self.rtprepare = {}

    def _loadconf(self,conf):
        pass

    def _parsert(self,rttask):
        if rttask:
            tasks = rttask.split('|')
            for it in tasks:
                if re.match('\d{4}',it):
                    self._rts.append(it)
            self._rts.sort()
        self.info('pid[%d] iktask rttask[%d] is ready'%(os.getpid(),len(self._rts)))

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
            dig = ''
            for i in range(len(lis)):
                if lis[i].isdigit():
                    dig = dig + lis[i]
            return int(dig)

    def _dl_drawfloat(self,str):
        pos = str.find(',')
        while pos != -1:
            str = str[:pos]+str[pos+1:]
            pos = str.find(',')
        return float(str)

    def _dl_upfrom163(self,code,start):
        td = datetime.datetime.today()
        ey = td.year
        em = td.month
        es = self._dl_season(em)
        ymd= start.split('-')
        sy = int(ymd[0])
        ss = self._dl_season(int(ymd[1]))
        s = [sy,ss]
        e = [ey,es]
        mat = []
        while s<=e:
            url = 'http://quotes.money.163.com/trade/lsjysj_%s.html?year=%s&season=%s'%(code,s[0],s[1])
            self.debug('pid[%d] iktask ready to open url[%s]'%(os.getpid(),url))
            html=urllib2.urlopen(url).read()
            #soup = BeautifulSoup(html, 'html.parser')
            soup = BeautifulSoup(html, 'lxml')
            trs = soup.find_all('tr')
            for tr in trs:
                tds=tr.find_all('td')
                if len(tds)==11:
                    dt = tds[0].text.strip()
                    if re.match('\d{4}-\d{2}-\d{2}', dt) and dt>start:
                        open = self._dl_drawfloat(tds[1].text.strip())
                        high = self._dl_drawfloat(tds[2].text.strip())
                        low = self._dl_drawfloat(tds[3].text.strip())
                        close = self._dl_drawfloat(tds[4].text.strip())
                        volh = self._dl_drawdigit(tds[7].text.strip())
                        volwy = self._dl_drawdigit(tds[8].text.strip())
                        v = (code,dt,open,high,low,close,volh,volwy)
                        mat.append(v)
            self.info('pid[%d] iktask fetch from url[%s] records[%d] start[%s]'%(os.getpid(),url,len(mat),start))
            if s[1]!=4:
                s[1]=s[1]+1
            else:
                s[0]=s[0]+1
                s[1]=1
        return mat

    def _check(self,codes):
        sqls = []
        all = 0
        for code in codes:
            try:
                lds = self.lastdays('ik_data',codes,self._datastart)
                shouldadd = self.exesqlquery('select date from hs.hs_daily_data where code=%s and date not in (select date from iknow.ik_data where code=%s)',(code,code))
                for adt in shouldadd:
                    self.info('iktask _check handle dl code[%s] date[%s]....'%(code,adt))
                    row = self.exesqlquery('select code,date,open,high,low,close,volh,volwy from hs.hs_daily_data where code=%s and date=%s',(code,adt))
                    sqls.append(('insert into iknow.ik_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
            except Exception,e:
                self.info('pid[%d] iktask _check code[%s],date[%04d-%02d-%02d] local update exception[%s]'%(os.getpid(),code,now.year,now.month,now.day,e))
        if self.task(sqls):
            all = all + len(sqls)
            self.info('pid[%d] iktask _check handle dl check executed sqls[%d] successfully....'%(os.getpid(),len(sqls)))
        else:
            self.info('pid[%d] iktask _check handle dl check executed sqls[%d] failed....'%(os.getpid(),len(sqls)))
        return all

    def download(self):
        all = 0
        try:
            self.info('pid[%d] iktask download task start....'%os.getpid())
            now = datetime.datetime.now()
            clis = self.codes()
            sqls = []
            lds = self.lastdays('ik_data',clis,self._datastart)
            for code in clis:
                try:
                    start = lds[code]
                    mat = self._dl_upfrom163(code,start)
                    for row in mat:
                        sqls.append(('insert into iknow.ik_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                    if len(sqls)>10000:
                        if self.task(sqls):
                            self.info('pid[%d] iktask handle download executed sqls[%d]....'%(os.getpid(),len(sqls)))
                            all = all+len(sqls)
                        sqls = []
                except Exception,e:
                    self.info('pid[%d] iktask download code[%s],date[%04d-%02d-%02d] update failed[%s]'%(os.getpid(),code,now.year,now.month,now.day,e))
            if self.task(sqls):
                all = all+len(sqls)
                self.info('pid[%d] iktask handle download executed sqls[%d] successfully....'%(os.getpid(),len(sqls)))
            else:
                self.info('pid[%d] iktask handle download executed sqls[%d] failed....'%(os.getpid(),len(sqls)))
            #all = all + self._check(clis)
        except Exception,e:
            self.info('pid[%d] iktask download exception[%s]....'%(os.getpid(),e))
        self.info('pid[%d] iktask download task done insert records[%d]....'%(os.getpid(),all))
        return all

    def _kinfo(self,code,data,ld):
        self.debug('pid[%d] iktask _kinfo start code[%s] length[%d]'%(os.getpid(),code,data.length()))
        dic = {}
        dl = data.keys(True)
        for i in range(len(dl)-1):
            if dl[i]<=ld:
                break
            obj = data.get(dl[i])
            objp = data.get(dl[i+1])
            hb = 0
            if obj.high>objp.high:
                hb = 1
            lb = 0
            if obj.low<objp.low:
                lb = 1
            k = 0
            if obj.close>obj.open:
                k = 1
            csrc = 0.5
            if obj.high!=obj.low:
                csrc = round((obj.close-obj.low)/(obj.high-obj.low),4)
            zdf = round((obj.close-objp.close)/objp.close,4)
            dic[dl[i]] = (hb,lb,k,csrc,zdf)
        self.debug('pid[%d] iktask _kinfo done code[%s] length[%d]'%(os.getpid(),code,len(dic)))
        return dic

    def _kd(self,code,data,ld):
        self.debug('pid[%d] iktask _kd start code[%s] length[%d]'%(os.getpid(),code,data.length()))
        kdp = 9
        lastk = 50.0
        lastd = 50.0
        dic = {}
        dl = data.keys()
        for i in range(kdp,len(dl)):
            close = data.get(dl[i]).close
            high = data.get(dl[i]).high
            low = data.get(dl[i]).low
            for j in range(1,kdp):
                if data.get(dl[i-j]).high>high:
                    high = data.get(dl[i-j]).high
                if data.get(dl[i-j]).low<low:
                    low = data.get(dl[i-j]).low
            k = 50.0
            d = 50.0
            if high != low:
                rsv = 100*((close-low)/(high-low))
                k = (2.0*lastk+rsv)/3.0
                d = (2.0*lastd+k)/3.0
            lastk = k
            lastd = d
            k = round(k,2)
            d = round(d,2)
            if dl[i]>ld:
                dic[dl[i]]=(k,d)
        self.debug('pid[%d] iktask _kd done code[%s] length[%d]'%(os.getpid(),code,len(dic)))
        return dic

    def _boll(self,code,data,ld):
        self.debug('pid[%d] iktask _boll start code[%s] length[%d]'%(os.getpid(),code,data.length()))
        bollp = 20
        dic = {}
        dl = data.keys()
        for i in range(bollp,len(dl)):
            if i >= bollp:
                if dl[i] <= ld:
                    continue
                sum = 0.0
                for j in range(bollp):
                    sum = sum + data.get(dl[i-j]).close
                mid = round(sum/float(bollp),2)
                all = 0.0
                for j in range(bollp):
                    all = all + (data.get(dl[i-j]).close-mid)**2
                std = round((all/float(bollp))**0.5,2)
                dic[dl[i]] = (mid,std)
        self.debug('pid[%d] iktask _boll done code[%s] length[%d]'%(os.getpid(),code,len(dic)))
        return dic
        
    def _macd(self,code,data,ld):
        self.debug('pid[%d] iktask _macd start code[%s] length[%d]'%(os.getpid(),code,data.length()))
        macdparan1 = 12
        macdparan2 = 26
        macdparan3 = 9
        dic = {}
        dl = data.keys()
        for i in range(len(dl)):
            if i == 0:
                emaf = data.get(dl[i]).close
                emas = data.get(dl[i]).close
                dea = 0
            else:
                close = data.get(dl[i]).close
                emaf = 2*close/(macdparan1+1)+(macdparan1-1)*emaf/(macdparan1+1)
                emas = 2*close/(macdparan2+1)+(macdparan2-1)*emas/(macdparan2+1)
                diff = round(emaf-emas,4)
                dea  = round(2*diff/(macdparan3+1)+(macdparan3-1)*dea/(macdparan3+1),4)
                macd = round(2*(diff-dea),4)
                if dl[i]>ld:
                    dic[dl[i]] = (round(emaf,4),round(emas,4),diff,dea,macd)
        self.debug('pid[%d] iktask _macd done code[%s] length[%d]'%(os.getpid(),code,len(dic)))
        return dic

    def _ma(self,code,data,ld):
        self.debug('pid[%d] iktask _ma start code[%s] length[%d]'%(os.getpid(),code,data.length()))
        dic = {}
        dl = data.keys()
        for i in range(60,len(dl)):
            mas = [5,10,30,60]
            line = []
            for map in mas:
                sum = 0.0
                for j in range(map):
                    sum = sum + data.get(dl[i-j]).close
                line.append(round(sum/float(map),2))
                sum = 0.0
            dic[dl[i]] = tuple(line)
        self.debug('pid[%d] iktask _ma done code[%s] length[%d]'%(os.getpid(),code,len(dic)))
        return dic

    def _vol(self,code,data,ld):
        self.debug('pid[%d] iktask _vol start code[%s] length[%d]'%(os.getpid(),code,data.length()))
        dic = {}
        dl = data.keys()
        for i in range(20,len(dl)):
            mas = [3,5,10,20]
            line = []
            for map in mas:
                sum = 0.0
                for j in range(map):
                    sum = sum + data.get(dl[i-j]).volwy
                line.append(round(sum,2))
                sum = 0.0
            dic[dl[i]] = tuple(line)
        self.debug('pid[%d] iktask _vol done code[%s] length[%d]'%(os.getpid(),code,len(dic)))
        return dic

    def attr(self):
        all = 0
        self.info('pid[%d] iktask attr task start....'%os.getpid())
        codes = self.codes()
        total = float(len(codes))
        handled = 0
        lds = self.lastdays('ik_attr',codes,self._datastart)
        for code in codes:
            handled = handled+1
            data = self.loadset('ik_data',code,['date','open','high','low','close','volwy'])
            sqls = []
            ld = lds[code]
            kinfo = self._kinfo(code,data,ld)
            kd = self._kd(code,data,ld)
            boll = self._boll(code,data,ld)
            macd = self._macd(code,data,ld)
            ma = self._ma(code,data,ld)
            vol = self._vol(code,data,ld)
            for dt in kinfo.keys():
                if kd.has_key(dt) and boll.has_key(dt) and macd.has_key(dt) and ma.has_key(dt) and vol.has_key(dt):
                    sqls.append(('insert into iknow.ik_attr(code,date,hb,lb,kline,csrc,zdf,k,d,mid,std,emaf,emas,diff,dea,macd,ma5,ma10,ma30,ma60,vol3,vol5,vol10,vol20) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,dt,)+kinfo[dt]+kd[dt]+boll[dt]+macd[dt]+ma[dt]+vol[dt]))
            if self.task(sqls):
                all = all + len(sqls)
                self.info('pid[%d] iktask attr handle progress[%0.2f%%] code[%s] sqls[%d] successfully....'%(os.getpid(),100*(handled/total),code,len(sqls)))
            else:
                self.info('pid[%d] iktask attr handle progress[%0.2f%%] code[%s] sqls[%d] falied....'%(os.getpid(),100*(handled/total),code,len(sqls)))
        self._logger.info('pid[%d] iktask attr task done....'%os.getpid())
        return all

    def _fv(self,hb,lb,kline):
        fv = 0
        if hb==1 and lb==0 and kline==1:
            fv = 1
        elif hb==1 and lb==0 and kline==0:
            fv = 2
        elif hb==0 and lb==1 and kline==1:
            fv = 3
        elif hb==0 and lb==1 and kline==0:
            fv = 4
        elif hb==1 and lb==1 and kline==1:
            fv = 5
        elif hb==1 and lb==1 and kline==0:
            fv = 6
        elif hb==0 and lb==0 and kline==1:
            fv = 7
        elif hb==0 and lb==0 and kline==0:
            fv = 8
        return fv

    def _kfv(self,k,d,kp):
        kfv = 0
        mid = (k+d)/2.0
        if mid>50:
            if k>d:
                kfv = 1
                if k<kp:
                    kfv = 2
            else:
                kfv = 3
                if k<kp:
                    kfv = 4
        else:
            if k>d:
                kfv = 5
                if k<kp:
                    kfv = 6
            else:
                kfv = 7
                if k<kp:
                    kfv = 8
        return kfv

    def _bfv(self,close,mid,std,stdp):
        bfv = 0
        up = mid+2*std
        dn = mid-2*std
        if close>up:
            bfv = 1
            if std<stdp:
                bfv = 2
        elif close<=up and close>mid:
            bfv = 3
            if std<stdp:
                bfv = 4
        elif close<=mid and close>=dn:
            bfv = 5
            if std<stdp:
                bfv = 6
        else:
            bfv = 7
            if std<stdp:
                bfv = 8
        return bfv

    def _macdv(self,macd,macdp):
        mfv = 0
        if macd>0 and macdp>0 and macd>macdp:
            mfv = 1
        elif macd>0 and macdp>0 and macd<=macdp:
            mfv = 2
        elif macd<=0 and macdp<=0 and macd>macdp:
            mfv = 3
        elif macd<=0 and macdp<=0 and macd<=macdp:
            mfv = 4
        elif macd>0 and macdp<=0 and macd>macdp:
            mfv = 5
        elif macd>0 and macdp<=0 and macd<=macdp:
            mfv = 6
        elif macd<=0 and macdp>0 and macd>macdp:
            mfv = 7
        elif macd<=0 and macdp>0 and macd<=macdp:
            mfv = 8
        return mfv

    def derivative(self):
        all = 0
        self._logger.info('pid[%d] iktask derivative task start....'%os.getpid())
        codes = self.codes()
        total = float(len(codes))
        handled = 0
        lds = self.lastdays('ik_deri',codes,self._datastart)
        for code in codes:
            handled = handled+1
            sqls = []
            ld = lds[code]
            data = self.exesqlquery('select date,hb,lb,kline,k,d,mid,std,macd from iknow.ik_attr where code=%s and date>=%s order by date',(code,ld))
            for i in range(1,len(data)):
                close = self.loadone(code,data[i][0],{'ik_data':['close']})
                if close:
                    close = close.close
                    fv = self._fv(data[i][1],data[i][2],data[i][3])
                    kfv = self._kfv(data[i][4],data[i][5],data[i-1][4])
                    bfv = self._bfv(close,data[i][6],data[i][7],data[i-1][7])
                    mfv = self._macdv(data[i][8],data[i-1][8])
                    sqls.append(('insert into iknow.ik_deri(code,date,fv,kfv,bfv,mfv) values(%s,%s,%s,%s,%s,%s)',(code,data[i][0],fv,kfv,bfv,mfv)))
            if self.task(sqls):
                all = all + len(sqls)
                self.info('pid[%d] iktask derivative handle progress[%0.2f%%] code[%s] sqls[%d] successfully....'%(os.getpid(),100*(handled/total),code,len(sqls)))
            else:
                self.info('pid[%d] iktask derivative handle progress[%0.2f%%] code[%s] sqls[%d] falied....'%(os.getpid(),100*(handled/total),code,len(sqls)))
        self.info('pid[%d] iktask derivative task done....'%os.getpid())
        return all

    def feature(self):
        all = 0
        self.info('pid[%d] iktask feature task start....'%os.getpid())
        codes = self.codes()
        total = float(len(codes))
        handled = 0
        for code in codes:
            sqls = []
            handled = handled+1
            data = self.loadset('ik_deri',code,['date','fv','kfv','bfv','mfv'])
            if data.length()<self._featuremin:
                continue
            start = self.lastday('ik_feature',code,self._featurestart)
            mat = []
            dl = data.keys()
            for i in range(4,len(dl)):
                date = dl[i-1]
                nextdate = dl[i]
                if date<=start:
                    continue
                fv4 = '%d%d%d%d'%(data.get(dl[i-4]).fv,data.get(dl[i-3]).fv,data.get(dl[i-2]).fv,data.get(dl[i-1]).fv)
                kfv2 = '%d%d'%(data.get(dl[i-2]).kfv,data.get(dl[i-1]).kfv)
                bfv2 = '%d%d'%(data.get(dl[i-2]).bfv,data.get(dl[i-1]).bfv)
                mfv2 = '%d%d'%(data.get(dl[i-2]).mfv,data.get(dl[i-1]).mfv)
                ohlc = self.exesqlquery('select date,open,high,low,close,volwy from ik_data where code=%s and date<=%s order by date desc limit 2',(code,nextdate))
                if len(ohlc)==2:
                    openr = round((ohlc[1][1]-ohlc[0][4])/ohlc[0][4],4)
                    highr = round((ohlc[1][2]-ohlc[0][4])/ohlc[0][4],4)
                    lowr = round((ohlc[1][3]-ohlc[0][4])/ohlc[0][4],4)
                    closer = round((ohlc[1][4]-ohlc[0][4])/ohlc[0][4],4)
                    vol = self.loadone(code,ohlc[1][0],{'ik_attr':['vol5']})
                    if vol:
                        vr = round((ohlc[0][5]/(vol.vol5/5.0)),2)
                        nfv4 = '%d%d%d%d'%(data.get(dl[i-3]).fv,data.get(dl[i-2]).fv,data.get(dl[i-1]).fv,data.get(dl[i]).fv)
                        nkfv2 = '%d%d'%(data.get(dl[i-1]).kfv,data.get(dl[i]).kfv)
                        nbfv2 = '%d%d'%(data.get(dl[i-1]).bfv,data.get(dl[i]).bfv)
                        nmfv2 = '%d%d'%(data.get(dl[i-1]).mfv,data.get(dl[i]).mfv)
                        sqls.append(('insert into iknow.ik_feature(code,date,vr,fv4,kfv2,bfv2,mfv2,nextdate,nextfv,nextkfv,nextbfv,nextmfv,openr,highr,lowr,closer,nextfv4,nextkfv2,nextbfv2,nextmfv2) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,date,vr,fv4,kfv2,bfv2,mfv2,nextdate,data.get(dl[i]).fv,data.get(dl[i]).kfv,data.get(dl[i]).bfv,data.get(dl[i]).mfv,openr,highr,lowr,closer,nfv4,nkfv2,nbfv2,nmfv2)))
            if self.task(sqls):
                all = all + len(sqls)
                self.info('pid[%d] iktask feature handle progress[%0.2f%%] code[%s] sqls[%d] successfully....'%(os.getpid(),100*(handled/total),code,len(sqls)))
            else:
                self.info('pid[%d] iktask feature handle progress[%0.2f%%] code[%s] sqls[%d] failed....'%(os.getpid(),100*(handled/total),code,len(sqls)))
        self.info('pid[%d] iktask feature task done....'%os.getpid())
        return all

    def updatert(self):
        all = 0
        self.info('pid[%d] iktask updatert task start....'%os.getpid())
        codes = self.codes()
        total = float(len(codes))
        handled = 0
        lis = []
        for code in codes:
            handled = handled+1
            data = self.exesqlquery('select volwy from ik_data where code=%s order by date desc limit 200',(code,))
            s200 = sum(data)
            s100 = sum(data[:100])
            ev200 = s200/200.0
            ev100 = s100/100.0
            lis.append((ev200,ev100,code))
            self.debug('pid[%d] iktask updatert handle progress[%0.2f%%] code[%s] ev200[%0.2f] ev100[%0.2f]....'%(os.getpid(),100*(handled/total),code,ev200,ev100))
        lis.sort(reverse=True)
        sqls = []
        for j in range(len(lis)):
            code = lis[j][2]
            ev100 = lis[j][1]
            prs = self.exesqlquery('select close,high,low,date from ik_data where code=%s order by date desc limit 60',(code,))
            if len(prs)!=60:
                continue
            updt = prs[0][3]
            i = 0
            s = 0
            high8 = 0
            low8 = 100000
            s4 = 0
            s9 = 0
            s29 = 0
            s59 = 0
            for row in prs:
                i = i + 1
                s = s+row[0]
                if i <= 8:
                    if row[1]>high8:
                        high8 = row[1]
                    if row[2]<low8:
                        low8 = row[2]
                if i == 4:
                    s4 = s
                elif i == 9:
                    s9 = s
                elif i == 29:
                    s29 = s
                elif i == 59:
                    s59 = s
            fvs = self.exesqlquery('select date,fv from ik_deri where code=%s and date<=%s order by date desc limit 3',(code,updt))
            fv3 = '%d%d%d'%(fvs[2][1],fvs[1][1],fvs[0][1])
            laststd = self.loadone(code,updt,{'ik_attr':['std']})
            if laststd:
                now = datetime.datetime.now()
                stamp = '%04d-%02d-%02d %02d:%02d:%02d'%(now.year,now.month,now.day,now.hour,now.minute,now.second)
                if j<self._watchmax and ev100>self._watchvolmin:
                    sqls.append(('update iknow.ik_rt set watch=1,basedate=%s,timestamp=%s,high8=%s,low8=%s,laststd=%s,s4=%s,s9=%s,s29=%s,s59=%s,fv3=%s where code=%s',(updt,stamp,high8,low8,laststd.std,s4,s9,s29,s59,fv3,code)))
                else:
                    sqls.append(('update iknow.ik_rt set watch=0,basedate=%s,timestamp=%s,high8=%s,low8=%s,laststd=%s,s4=%s,s9=%s,s29=%s,s59=%s,fv3=%s where code=%s',(updt,stamp,high8,low8,laststd.std,s4,s9,s29,s59,fv3,code)))
        if self.task(sqls):
            all = all + len(sqls)
            self.info('pid[%d] iktask updatert task successfully'%os.getpid())
        else:
            self.info('pid[%d] iktask updatert task failed'%os.getpid())
        self.info('pid[%d] iktask updatert task done sqls[%d]....'%(os.getpid(),len(sqls)))
        return all

    def next(self):
        all = 0
        self.info('pid[%d] iktask next task start....'%os.getpid())
        codes = self.codes()
        sqls = []
        for code in codes:
            ld = self.lastday('ik_next',code,self._datastart)
            fvs = self.exesqlquery('select date,fv,kfv,bfv,mfv from ik_deri where code=%s order by date desc limit 4',(code,))
            if len(fvs)==4:
                date = fvs[0][0]
                if date>ld:
                    fv4 = '%d%d%d%d'%(fvs[3][1],fvs[2][1],fvs[1][1],fvs[0][1])
                    hlr = self.loadone(code,date,{'ik_data':['high','low','close','volwy']})
                    hr = round((hlr.high-hlr.close)/hlr.close,4)
                    lr = round((hlr.low-hlr.close)/hlr.close,4)
                    vol = self.loadone(code,fvs[1][0],{'ik_attr':['vol5']})
                    vr = round(hlr.volwy/(vol.vol5/5.0),2)
                    fv4p = self.prob('fv4',fv4,hr,lr,vr)
                    sqls.append(('insert into ik_next(code,date,fv4,fv4cnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,date,fv4,fv4p[0])+fv4p[1]))
            self.info('pid[%d] iktask next collect sqls[%d]'%(os.getpid(),len(sqls)))
        if self.task(sqls):
            all = all + len(sqls)
            self.info('pid[%d] iktask next handle sqls[%d] successfully....'%(os.getpid(),len(sqls)))
        else:
            self.info('pid[%d] iktask next handle sqls[%d] failed....'%(os.getpid(),len(sqls)))
        self.info('pid[%d] iktask next task done....'%os.getpid())
        return all

    def rtprices(self):
        codeliststr = ''
        codes = self.rtprepare.keys()
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
                        hq = ikobj()
                        setattr(hq,'code',codes[i])
                        setattr(hq,'open',float(info[1]))
                        setattr(hq,'high',float(info[4]))
                        setattr(hq,'low',float(info[5]))
                        setattr(hq,'close',float(info[3]))
                        setattr(hq,'lastclose',float(info[2]))
                        setattr(hq,'volwy',float(info[9])/10000.0)
                        setattr(hq,'volh',float(info[8])/100)
                        setattr(hq,'date',info[30])
                        setattr(hq,'time',info[31])
                        lis.append(hq)
                except Exception, e:
                    self.error('pid[%d] iktask get current price codes[%s] exception[%s]'%(os.getpid(),codes[i],e))
                i = i+1
            return lis
        except Exception, e:
            self.error('pid[%d] iktask get current price codes[%d] url[%s] exception[%s]'%(os.getpid(),len(codes),url,e))
            return None

    def rttask(self):
        cnt = 0
        self.info('pid[%d] iktask rttask start....'%os.getpid())
        hqlis = self.rtprices()
        self.info('pid[%d] iktask rttask get hq list[%d]....'%(os.getpid(),len(hqlis)))
        hbc = 0
        lbc = 0
        scsrc = 0
        total = float(len(hqlis))
        handled = 0
        sqls = []
        for hq in hqlis:
            date = hq.date
            time = hq.time
            zdf = round(100*((hq.close-hq.lastclose)/hq.lastclose),2)
            csrc = 50.0
            if hq.high!=hq.low:
                csrc = round(100*((hq.close-hq.low)/(hq.high-hq.low)),2)
            volwy = hq.volwy
            ymd = hq.date.split('-')
            hms = hq.time.split(':')
            hqtime = datetime.datetime(int(ymd[0]),int(ymd[1]),int(ymd[2]),int(hms[0]),int(hms[1]),int(hms[2]))
            delta = hqtime-datetime.datetime(hqtime.year,hqtime.month,hqtime.day,9,30,0)
            if hqtime>datetime.datetime(hqtime.year,hqtime.month,hqtime.day,11,30,59):
                delta = hqtime-datetime.datetime(hqtime.year,hqtime.month,hqtime.day,13,0,0)+datetime.timedelta(seconds=7200)
            vr = round(hq.volwy/((self.rtprepare[hq.code].vol5/5.0)*(float(delta.seconds)/float(14400))),2)
            close = hq.close
            ma5 = round((close+self.rtprepare[hq.code].s4)/5.0,2)
            ma10 = round((close+self.rtprepare[hq.code].s9)/10.0,2)
            ma20 = round((close+sum(self.rtprepare[hq.code].closes))/20.0,2)
            ma30 = round((close+self.rtprepare[hq.code].s29)/30.0,2)
            ma60 = round((close+self.rtprepare[hq.code].s59)/60.0,2)
            all = 0.0
            for c in self.rtprepare[hq.code].closes:
                all = all + (c-ma20)**2
            all = all + (hq.close-ma20)**2
            std = round(all**0.5,2)
            hb = 0
            if hq.high>self.rtprepare[hq.code].lasthigh:
                hb = 1
                hbc = hbc + 1
            lb = 0
            if hq.low<self.rtprepare[hq.code].lastlow:
                lb = 1
                lbc = lbc + 1
            scsrc = scsrc + csrc
            kline = 0
            if hq.close>hq.open:
                kline = 1
            fv = self._fv(hb,lb,kline)
            fv4 = '%s%d'%(self.rtprepare[hq.code].fv3,fv)
            high = self.rtprepare[hq.code].high8
            if hq.high>high:
                high = hq.high
            low = self.rtprepare[hq.code].low8
            if hq.low<low:
                low = hq.low
            k = 50.0
            d = 50.0
            lastk = self.rtprepare[hq.code].lastk
            lastd = self.rtprepare[hq.code].lastd
            if high != low:
                rsv = 100*((hq.close-low)/(high-low))
                k = (2.0*lastk+rsv)/3.0
                d = (2.0*lastd+k)/3.0
            kfv = self._kfv(k,d,lastk)
            kfv2 = '%d%d'%(self.rtprepare[hq.code].kfv,kfv)
            bfv = self._bfv(hq.close,ma20,std,self.rtprepare[hq.code].laststd)
            bfv2 = '%d%d'%(self.rtprepare[hq.code].bfv,bfv)
            macdparan1 = 12
            macdparan2 = 26
            macdparan3 = 9
            emaf = 2*hq.close/(macdparan1+1)+(macdparan1-1)*self.rtprepare[hq.code].emaf/(macdparan1+1)
            emas = 2*hq.close/(macdparan2+1)+(macdparan2-1)*self.rtprepare[hq.code].emas/(macdparan2+1)
            diff = round(emaf-emas,4)
            dea  = round(2*diff/(macdparan3+1)+(macdparan3-1)*self.rtprepare[hq.code].dea/(macdparan3+1),4)
            macd = round(2*(diff-dea),4)
            mfv = self._macdv(macd,self.rtprepare[hq.code].lastmacd)
            mfv2 = '%d%d'%(self.rtprepare[hq.code].mfv,mfv)
            hr = round((hq.high-hq.lastclose)/hq.lastclose,4)
            lr = round((hq.low-hq.lastclose)/hq.lastclose,4)
            fvp = self.prob('fv4',fv4,hr,lr,vr)
            now = datetime.datetime.now()
            rtstamp = '%04d-%02d-%02d %02d:%02d:%02d'%(now.year,now.month,now.day,now.hour,now.minute,now.second)
            sqls.append(('update ik_rt set date=%s,time=%s,zdf=%s,csrc=%s,volwy=%s,vr=%s,close=%s,ma5=%s,ma10=%s,ma20=%s,ma30=%s,ma60=%s,fv4=%s,fv4cnt=%s,fv4p1=%s,fv4p2=%s,fv4p3=%s,fv4p4=%s,fv4p5=%s,fv4p6=%s,fv4p7=%s,fv4p8=%s,rttimestamp=%s where code=%s',(date,time,zdf,csrc,volwy,vr,close,ma5,ma10,ma20,ma30,ma60,fv4,fvp[0])+fvp[1]+(hq.code,rtstamp)))
            handled = handled + 1
            self.info('pid[%d] iktask rttask handle progress[%0.2f%%] code[%s]....'%(os.getpid(),100*(handled/total),hq.code))
        if self.task(sqls):
            cnt = cnt + len(sqls)
            self.info('pid[%d] iktask rttask end successfully sqls[%d]....'%(os.getpid(),len(sqls)-1))
        else:
            self.info('pid[%d] iktask rttask end failed sqls[%d]....'%(os.getpid(),len(sqls)-1))
        return cnt

    def _loadtask(self):
        cur = None
        if len(self._tasklist)==0:
            now = datetime.datetime.now()
            tm = '%02d%02d'%(now.hour,now.minute)
            if self.isopenday():
                if now.hour<=14:
                    cur = ikmessage('%s_%04d%02d%02d%s'%(HY_TASK_BEFOREOPEN,now.year,now.month,now.day,tm),HY_TASK_BEFOREOPEN,None,False,None)
                    for p in self._rts:
                        if p > tm:
                            active = '%04d%02d%02d%s'%(now.year,now.month,now.day,p)
                            self._tasklist.append(ikmessage('%s_%s'%(HY_TASK_REALTIME,active),HY_TASK_REALTIME,None,True,active))
                    active = '%04d%02d%02d%s'%(now.year,now.month,now.day,self._afterbegin)
                    self._tasklist.append(ikmessage('%s_%s'%(HY_TASK_AFTERCLOSE,active),HY_TASK_AFTERCLOSE,None,True,active))
                elif tm<self._afterbegin:
                    active = '%04d%02d%02d%s'%(now.year,now.month,now.day,self._afterbegin)
                    self._tasklist.append(ikmessage('%s_%s'%(HY_TASK_AFTERCLOSE,active),HY_TASK_AFTERCLOSE,None,True,active))
                else:
                    cur = ikmessage('%s_%04d%02d%02d%s'%(HY_TASK_BEFOREOPEN,now.year,now.month,now.day,tm),HY_TASK_BEFOREOPEN,None,False,None)
            else:
                last = self.lasttask()
                if (not last) or last.type!=HY_TASK_AFTERCLOSE:
                    cur = ikmessage('%s_%04d%02d%02d%s'%(HY_TASK_AFTERCLOSE,now.year,now.month,now.day,tm),HY_TASK_AFTERCLOSE,None,False,None)
            next = self.nextopenday()
            ymd = next.split('-')
            next = '%s%s%s'%(ymd[0],ymd[1],ymd[2])
            for p in self._rts:
                active = '%s%s'%(next,p)
                self._tasklist.append(ikmessage('%s_%s'%(HY_TASK_REALTIME,active),HY_TASK_REALTIME,None,True,active))
            active = '%s%s'%(next,self._afterbegin)
            self._tasklist.append(ikmessage('%s_%s'%(HY_TASK_AFTERCLOSE,active),HY_TASK_AFTERCLOSE,None,True,active))
        return cur

    def handle_afterclose(self):
        dlcnt = self.download()
        atcnt = self.attr()
        decnt = self.derivative()
        fecnt = self.feature()
        wccnt = self.updatert()
        ntcnt = self.next()
        self.handle_beforeopen()
        self.loadinfo()
        self.info('pid[%d] iktask handle_afterclose dl[%d] attr[%d] derivative[%d] feature[%d] rt[%d] next[%d]'%(os.getpid(),dlcnt,atcnt,decnt,fecnt,wccnt,ntcnt))

    def handle_realtime(self):
        rtcnt = self.rttask()
        self.info('pid[%d] iktask handle_realtime rt[%d]'%(os.getpid(),rtcnt))

    def handle_beforeopen(self):
        data = self.exesqlquery('select code,name,industry,high8,low8,laststd,s4,s9,s29,s59,fv3 from ik_rt where watch=1',None)
        self.rtprepare = {}
        for row in data:
            hlc = self.exesqlquery('select date,high,low,close from ik_data where code=%s order by date desc limit 19',(row[0],))
            attrs = self.loadone(row[0],hlc[0][0],{'ik_attr':['k','d','emaf','emas','diff','dea','macd','vol5'],'ik_deri':['kfv','bfv','mfv']})
            if attrs:
                obj = ikobj()
                setattr(obj,'code',row[0])
                setattr(obj,'name',row[1])
                setattr(obj,'industry',row[2])
                setattr(obj,'high8',row[3])
                setattr(obj,'low8',row[4])
                setattr(obj,'laststd',row[5])
                setattr(obj,'s4',row[6])
                setattr(obj,'s9',row[7])
                setattr(obj,'s29',row[8])
                setattr(obj,'s59',row[9])
                setattr(obj,'fv3',row[10])
                setattr(obj,'kfv',attrs.kfv)
                setattr(obj,'bfv',attrs.bfv)
                setattr(obj,'mfv',attrs.mfv)
                setattr(obj,'lastk',attrs.k)
                setattr(obj,'lastd',attrs.d)
                setattr(obj,'lasthigh',hlc[0][1])
                setattr(obj,'lastlow',hlc[0][2])
                setattr(obj,'emaf',attrs.emaf)
                setattr(obj,'emas',attrs.emas)
                setattr(obj,'diff',attrs.diff)
                setattr(obj,'dea',attrs.dea)
                setattr(obj,'lastmacd',attrs.macd)
                setattr(obj,'vol5',attrs.vol5)
                cls = []
                for it in hlc:
                    cls.append(it[3])
                setattr(obj,'closes',cls)
                self.rtprepare[row[0]] = obj

    def handle_message(self,msg):
        if msg.type==HY_TASK_AFTERCLOSE:
            self.handle_afterclose()
        elif msg.type==HY_TASK_REALTIME:
            self.handle_realtime()
        elif msg.type==HY_TASK_BEFOREOPEN:
            self.handle_beforeopen()
        elif msg.type==HY_TASK_UPDATEINFO:
            self.loadinfo()
        else:
            self.error('pid[%d] ikatsk unknown message[%s]'%(os.getpid(),msg.name))

    def main(self):
        task = self._loadtask()
        if task:
            self.putq(task)
            self.info('pid[%d] iktask tasklist[%d] nexttask[%s]'%(os.getpid(),len(self._tasklist),self._tasklist[0].name))
        else:
            now = datetime.datetime.now()
            tm = '%04d%02d%02d%02d%02d'%(now.year,now.month,now.day,now.hour,now.minute)
            while tm>self._tasklist[0].active:
                self.info('pid[%d] iktask tasklist[%d] task[%s] has been expired'%(os.getpid(),len(self._tasklist),self._tasklist[0].name))
                self._tasklist.pop(0)
            if tm==self._tasklist[0].active:
                self.putq(self._tasklist.pop(0))
                self.info('pid[%d] iktask tasklist[%d] nexttask[%s]'%(os.getpid(),len(self._tasklist),self._tasklist[0].name))
            else:
                self.debug('pid[%d] iktask tasklist[%d] nexttask[%s]'%(os.getpid(),len(self._tasklist),self._tasklist[0].name))

if __name__ == "__main__":
    ik = iktask('iknow.conf')
    ik.run()

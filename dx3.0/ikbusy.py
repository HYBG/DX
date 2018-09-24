#!/usr/bin/python

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
from bs4 import BeautifulSoup
from optparse import OptionParser
from logging.handlers import RotatingFileHandler

sys.path.append(os.path.join(os.getenv('IKNOW_HOME','/var/data/iknow'),'lib'))
from ikdata import ikdata

class ikset:
    def __init__(self):
        self._store = {}

    def set(self,key,value):
        self._store[key] = value

    def get(self,key):
        try:
            return self._store[key]
        except Exception,e:
            pass
        return None

    def keys(self,rev=False):
        keys = self._store.keys()
        keys.sort(reverse=rev)
        return keys

    def length(self):
        return len(self._store)

class ikobj:
    def __init__(self):
        pass

class ikbusy(ikdata):
    def __init__(self,logfile=None,logon=False):
        home = os.getenv('IKNOW_HOME','/var/data/iknow')
        if logfile:
            ikdata.__init__(self,logfile,logon)
        else:
            ikdata.__init__(self,os.path.join(os.path.join(home,'log'),'ikbusy.log'),logon)
        self._defaultstart = '1987-05-07'
        self.rtprepare = {}

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
            self.debug('ikdata ready to open url[%s]'%url)
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
            self.debug('ikdata fetch from url[%s] records[%d] start[%s]'%(url,len(mat),start))
            if s[1]!=4:
                s[1]=s[1]+1
            else:
                s[0]=s[0]+1
                s[1]=1
        return mat

    def _check(self,codes):
        sqls = []
        for code in codes:
            try:
                lds = self.lastdays('ik_data',codes,'1987-05-07')
                shouldadd = self.exesqlquery('select date from hs.hs_daily_data where code=%s and date not in (select date from iknow.ik_data where code=%s)',(code,code))
                for adt in shouldadd:
                    self.info('ikdata _check handle dl code[%s] date[%s]....'%(code,adt))
                    row = self.exesqlquery('select code,date,open,high,low,close,volh,volwy from hs.hs_daily_data where code=%s and date=%s',(code,adt))
                    sqls.append(('insert into iknow.ik_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
            except Exception,e:
                self.info('code[%s],date[%04d-%02d-%02d] local update exception[%s]'%(code,now.year,now.month,now.day,e))
        self.task(sqls)
        self.info('ikdata _check handle dl check executed sqls[%d]....'%(len(sqls)))

    def download(self):
        try:
            self.info('ikdata download task start....')
            now = datetime.datetime.now()
            clis = self.codes()
            sqls = []
            lds = self.lastdays('ik_data',clis,self._defaultstart)
            for code in clis:
                try:
                    start = lds[code]
                    mat = self._dl_upfrom163(code,start)
                    for row in mat:
                        sqls.append(('insert into iknow.ik_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                    if len(sqls)>10000:
                        self.task(sqls)
                        self.info('ikdata handle download executed sqls[%d]....'%(len(sqls)))
                        sqls = []
                except Exception,e:
                    self.info('ikdata download code[%s],date[%04d-%02d-%02d] update failed[%s]'%(code,now.year,now.month,now.day,e))
            self.task(sqls)
            self.info('ikdata handle download executed sqls[%d]....'%(len(sqls)))
            self._check(clis)
        except Exception,e:
            self.info('ikdata download exception[%s]....'%e)
        self.info('ikdata download task done....')

    def loadset(self,table,code,fields):
        items = ''
        if 'date' not in fields:
            fields.append('date')
        for it in fields:
            items = items+it+','
        items = items[:-1]
        sql = 'select '+items+' from '+table+' where code=%s'
        self.debug('loadset sql[%s] code[%s]'%(sql,code))
        n = self._cursor.execute(sql,(code,))
        set = ikset()
        while n>0:
            ret = self._cursor.fetchone()
            obj = ikobj()
            for i in range(len(ret)):
                setattr(obj,fields[i],ret[i])
            set.set(getattr(obj,'date'),obj)
            n = n-1
        return set

    def loadone(self,code,date,dic):
        items = ''
        tabs  = ''
        cond  = ''
        paras = []
        attrs = []
        for tab in dic.keys():
            tabs = tabs+tab+','
            cond = cond+tab+'.code=%s and '+tab+'.date=%s and '
            for it in dic[tab]:
                item = '%s.%s'%(tab,it)
                if not hasattr(self,it):
                    attrs.append(it)
                items = items+item+','
            paras.append(code)
            paras.append(date)
        if len(tabs)!=0 and len(items)!=0 and len(cond)!=0:
            tabs = tabs[:-1]
            items = items[:-1]
            cond = cond[:-5]
            sql = 'select %s from %s where %s'%(items,tabs,cond)
            self._logger.debug('loadone sql[%s],paras[%s]'%(sql,str(paras)))
            n = self._cursor.execute(sql,tuple(paras))
            if n==1:
                ret = self._cursor.fetchone()
                obj = ikobj()
                for i in range(len(ret)):
                    setattr(obj,attrs[i],ret[i])
                return obj
        return None

    def _kinfo(self,code,data,ld):
        self.debug('ikdata _kinfo start code[%s] length[%d]'%(code,data.length()))
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
        self.debug('ikdata _kinfo done code[%s] length[%d]'%(code,len(dic)))
        return dic

    def _kd(self,code,data,ld):
        self.debug('ikdata _kd start code[%s] length[%d]'%(code,data.length()))
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
        self.debug('ikdata _kd done code[%s] length[%d]'%(code,len(dic)))
        return dic

    def _boll(self,code,data,ld):
        self.debug('ikdata _boll start code[%s] length[%d]'%(code,data.length()))
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
        self.debug('ikdata _boll done code[%s] length[%d]'%(code,len(dic)))
        return dic
        
    def _macd(self,code,data,ld):
        self.debug('ikdata _macd start code[%s] length[%d]'%(code,data.length()))
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
        self.debug('ikdata _macd done code[%s] length[%d]'%(code,len(dic)))
        return dic

    def _ma(self,code,data,ld):
        self.debug('hyik _ma start code[%s] length[%d]'%(code,data.length()))
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
        self.debug('ikdata _ma done code[%s] length[%d]'%(code,len(dic)))
        return dic

    def _vol(self,code,data,ld):
        self.debug('ikdata _vol start code[%s] length[%d]'%(code,data.length()))
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
        self.debug('ikdata _vol done code[%s] length[%d]'%(code,len(dic)))
        return dic
        
    def attr(self):
        self.info('ikdata attr task start....')
        codes = self.codes()
        total = float(len(codes))
        handled = 0
        lds = self.lastdays('ik_attr',codes,self._defaultstart)
        for code in codes:
            handled = handled+1
            data = self.loadset('ik_data',code,['date','open','high','low','close','volwy'])
            dic = self._kinfo(code,data,lds[code])
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
            self.task(sqls)
            self.info('ikdata attr handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self._logger.info('ikdata attr task done....')

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
        self._logger.info('ikdata derivative task start....')
        codes = self.codes()
        total = float(len(codes))
        handled = 0
        lds = self.lastdays('ik_deri',codes,self._defaultstart)
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
            self.task(sqls)
            self.info('ikdata derivative handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self.info('ikdata derivative task done....')

    def feature(self):
        self.info('ikdata feature task start....')
        codes = self.codes()
        total = float(len(codes))
        handled = 0
        for code in codes:
            sqls = []
            handled = handled+1
            data = self.loadset('ik_deri',code,['date','fv','kfv','bfv','mfv'])
            if data.length()<200:
                continue
            start = self.lastday('ik_feature',code,'2005-01-01')
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
            self.task(sqls)
            self.info('ikdata feature handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self.info('ikdata feature task done....')

    def updatewatch(self):
        self.info('ikdata updatewatch task start....')
        codes = self.codes()
        total = float(len(codes))
        handled = 0
        lis = []
        dic = {}
        for code in codes:
            handled = handled+1
            data = self.exesqlquery('select volwy from ik_data where code=%s order by date desc limit 200',(code,))
            s200 = sum(data)
            s100 = sum(data[:100])
            ev200 = s200/200.0
            ev100 = s100/100.0
            lis.append((ev200,code))
            dic[code]=ev100
            self.debug('ikdata updatewatch handle progress[%0.2f%%] code[%s] ev200[%0.2f] ev100[%0.2f]....'%(100*(handled/total),code,ev200,ev100))
        lis.sort(reverse=True)
        sqls = []
        for j in range(len(lis)):
            code = lis[j][1]
            if j<600 and dic[code]>12000:
                prs = self.exesqlquery('select close,high,low from ik_data where code=%s order by date desc limit 60',(code,))
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
                    if i >= 8:
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
                fvs = self.exesqlquery('select date,fv from ik_deri where code=%s order by date desc limit 3',(code,))
                updt = fvs[0][0]
                fv3 = '%d%d%d'%(fvs[0][1],fvs[1][1],fvs[2][1])
                laststd = self.loadone(code,updt,{'ik_attr':['std']})
                if laststd:
                    sqls.append(('update iknow.ik_rt set watch=1,updatedate=%s,high8=%s,low8=%s,laststd=%s,s4=%s,s9=%s,s29=%s,s59=%s,fv3=%s where code=%s',(updt,high8,low8,laststd.std,s4,s9,s29,s59,fv3,code)))
            else:
                updt = self.exesqlquery('select date from ik_data where code=%s order by date desc limit 1',(code,))
                if len(updt)!=0 and updt:
                    sqls.append(('update iknow.ik_rt set watch=0,updatedate=%s,high8=0,low8=0,laststd=0,s4=0,s9=0,s29=0,s59=0,fv3=0  where code=%s',(updt[0],'0',code)))
        if not self.task(sqls):
            self.info('ikdata updatewatch task false')
        self.info('ikdata updatewatch task done sqls[%d]....'%(len(sqls)))

    def next(self):
        self.info('ikdata next task start....')
        codes = self.codes()
        total = float(len(codes))
        handled = 0
        sqls = []
        for code in codes:
            handled = handled+1
            fvs = self.exesqlquery('select date,fv,kfv,bfv,mfv from ik_deri where code=%s order by date desc limit 4',(code,))
            fv4 = '%d%d%d%d'%(fvs[3][1],fvs[2][1],fvs[1][1],fvs[0][1])
            kfv2 = '%d%d'%(fvs[1][2],fvs[0][2])
            bfv2 = '%d%d'%(fvs[1][3],fvs[0][3])
            mfv2 = '%d%d'%(fvs[1][4],fvs[0][4])
            hlr = self.loadone(code,fvs[0][0],{'ik_data':['high','low','close','volwy']})
            hr = round((hlr.high-hlr.close)/hlr.close,4)
            lr = round((hlr.low-hlr.close)/hlr.close,4)
            vol = self.loadone(code,fvs[1][0],{'ik_attr':['vol5']})
            vr = round(hlr.volwy/(vol.vol5/5.0),2)
            fv4p = self._prob('fv4',fv4,hr,lr,vr)
            kfv2p = self._prob('kfv2',kfv2,hr,lr,vr)
            bfv2p = self._prob('bfv2',bfv2,hr,lr,vr)
            mfv2p = self._prob('mfv2',mfv2,hr,lr,vr)
            sqls.append(('insert into ik_next(code,date,fv4,fv4cnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8,kfv2,kfv2cnt,kfv2p1,kfv2p2,kfv2p3,kfv2p4,kfv2p5,kfv2p6,kfv2p7,kfv2p8,bfv2,bfv2cnt,bfv2p1,bfv2p2,bfv2p3,bfv2p4,bfv2p5,bfv2p6,bfv2p7,bfv2p8,mfv2,mfv2cnt,mfv2p1,mfv2p2,mfv2p3,mfv2p4,mfv2p5,mfv2p6,mfv2p7,mfv2p8) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,fvs[0][0],fv4,fv4p[0])+fv4p[1]+(kfv2p[0],)+kfv2p[1]+(bfv2p[0],)+bfv2p[1]+(mfv2p[0],)+mfv2p[1]))
            self.info('ikdata next handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
        self.task(sqls)
        self.info('ikdata next task done sqls[%d]....'%(len(sqls)))

    def loadprepare(self):
        data = self.exesqlquery('select code,name,industry,high8,low8,laststd,s4,s9,s29,s59,fv3,kfv3,bfv3,mfv3 from ik_rt where watch=1',None)
        self.rtprepare = {}
        for row in data:
            hlc = self.exesqlquery('select date,high,low,close from ik_data where code=%s order by date desc limit 19',(row[0],))
            attrs = self.loadone(row[0],hlc[0][0],{'ik_attr':['k','d','emaf','emas','diff','dea','macd','vol5'],'ik_deri':['kfv,bfv,mfv']})
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
                        setattr(hq,'volwy',float(info[2]))
                        setattr(hq,'volh',float(info[8])/100)
                        setattr(hq,'date',info[30])
                        setattr(hq,'time',info[31])
                        lis.append(hq)
                except Exception, e:
                    self.error('get current price codes[%s] exception[%s]'%(codes[i],e))
                i = i+1
            return lis
        except Exception, e:
            self.error('get current price codes[%d] url[%s] exception[%s]'%(len(codes),url,e))
            return None

    def _prob(self,item,iv,hr,lr,vr):
        self.info('ikdata _prob handle item[%s] val[%s] start....'%(str(item),str(iv)))
        plis = []
        dn = 0.6
        up = 1.4
        vcond = 'vr<=%s'%(dn)
        if vr>=up:
            vcond = 'vr>=%s'%str(up)
        elif vr>=dn:
            vcond = 'vr>%s and vr<%s'%(str(dn),str(up))
        fcond = item+'=%s'
        all = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8))',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        if all[0]==0:
            return (0,(0,0,0,0,0,0,0,0))
        c1 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=1',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c1[0])/all[0]),2))
        c2 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=2',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c2[0])/all[0]),2))
        c3 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=3',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c3[0])/all[0]),2))
        c4 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=4',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c4[0])/all[0]),2))
        c5 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=5',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c5[0])/all[0]),2))
        c6 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=6',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c6[0])/all[0]),2))
        c7 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=7',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c7[0])/all[0]),2))
        c8 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=8',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c8[0])/all[0]),2))
        self.info('ikdata _prob handle item[%s] val[%s] done....'%(str(item),str(iv)))
        return (all[0],tuple(plis))

    def rttask(self):
        self.info('rttask start....')
        hqlis = self.rtprices()
        sqls = []
        self.info('rttask get hq list[%d]....'%len(hqlis))
        hbc = 0
        lbc = 0
        scsrc = 0
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
            delta = hqtime-datetime.dattime(hqtime.year,hqtime.month,hqtime.day,9,30,0)
            if hqtime>datetime.dattime(hqtime.year,hqtime.month,hqtime.day,11,30,59):
                delta = hqtime-datetime.dattime(hqtime.year,hqtime.month,hqtime.day,13,0,0)+datetime.timedelta(seconds=7200)
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
            mfv = self._mfv(macd,self.rtprepare[hq.code].lastmacd)
            mfv2 = '%d%d'%(self.rtprepare[hq.code].mfv,mfv)
            hr = round((hq.high-hq.lastclose)/hq.lastclose,4)
            lr = round((hq.low-hq.lastclose)/hq.lastclose,4)
            fvp = self._prob('fv4',fv4,hr,lr,vr)
            kfvp = self._prob('kfv2',kfv2,hr,lr,vr)
            bfvp = self._prob('bfv2',bfv2,hr,lr,vr)
            mfvp = self._prob('mfv2',mfv2,hr,lr,vr)
            sqls.append(('update ik_rt set date=%s,time=%s,zdf=%s,csrc=%s,volwy=%s,vr=%s,close=%s,ma5=%s,ma10=%s,ma20=%s,ma30=%s,ma60=%s,fv4=%s,fv4cnt=%s,fv4p1=%s,fv4p2=%s,fv4p3=%s,fv4p4=%s,fv4p5=%s,fv4p6=%s,fv4p7=%s,fv4p8=%s,kfv2=%s,kfv2cnt=%s,kfv2p1=%s,kfv2p2=%s,kfv2p3=%s,kfv2p4=%s,kfv2p5=%s,kfv2p6=%s,kfv2p7=%s,kfv2p8=%s,bfv2=%s,bfv2cnt=%s,bfv2p1=%s,bfv2p2=%s,bfv2p3=%s,bfv2p4=%s,bfv2p5=%s,bfv2p6=%s,bfv2p7=%s,bfv2p8=%s,mfv2=%s,mfv2cnt=%s,mfv2p1=%s,mfv2p2=%s,mfv2p3=%s,mfv2p4=%s,mfv2p5=%s,mfv2p6=%s,mfv2p7=%s,mfv2p8=%s where code=%s',(date,time,zdf,csrc,volwy,vr,close,ma5,ma10,ma20,ma30,ma60,fv4,fvp[0])+fvp[1]+(kfvp[0],)+kfvp[1]+(bfvp[0],)+bfvp[1]+(mfvp[0],)+mfvp[1]))
        g_tool.task(sqls)
        self.info('scsrc end successfully sqls[%d]....'%(len(sqls)-1))

    def onbeforeopen(self):
        self.loadprepare()

    def afterclose(self):
        self.download()
        self.attr()
        self.derivative()
        self.feature()
        self.updatewatch()

    def start(self):
        all = [(9,31),(9,41),(9,51),(10,1),(10,11),(10,21),(10,31),(10,41),(10,51),(11,1),(11,11),(11,21),(13,10),(13,20),(13,30),(13,40),(13,50),(14,0),(14,10),(14,20),(14,30),(14,40),(14,50),(15,0)]
        for it in all:
            self.addhandler(True,it,self.rttask)
        self.addhandler(True,(17,0),self.afterclose)
        self.run()

if __name__ == "__main__":
    ik = ikbusy()
    ik.start()

    
    
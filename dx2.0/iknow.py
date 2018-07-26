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
import web
import json
from bs4 import BeautifulSoup
from optparse import OptionParser
from logging.handlers import RotatingFileHandler

IK_STATUS_BREAK_UP = 1
IK_STATUS_BREAK_DN = 2
IK_STATUS_DEVIATION_UP = 3
IK_STATUS_DEVIATION_DN = 4
IK_STATUS_REBOUND_UP = 5 
IK_STATUS_REBOUND_DN = 6
IK_STATUS_STAND_UP = 7
IK_STATUS_STAND_DN = 8
IK_STATUS_OPEN_UP = 9
IK_STATUS_OPEN_DN = 10
IK_STATUS_ADJUST_UP = 11
IK_STATUS_ADJUST_DN = 12
IK_STATUS_MA5_UP = 51
IK_STATUS_MA5_DN = 52
IK_STATUS_MA10_UP = 53
IK_STATUS_MA10_DN = 54
IK_STATUS_MA20_UP = 55
IK_STATUS_MA20_DN = 56
IK_STATUS_MA30_UP = 57
IK_STATUS_MA30_DN = 58
IK_STATUS_MA60_UP = 59
IK_STATUS_MA60_DN = 60


class iknow:
    def __init__(self,home='/var/data/iknow'):
        self._logger = logging.getLogger('iknow')
        self._loglevel = logging.INFO
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logd = os.path.join(home,'log')
        logfile = os.path.join(logd,'iknow.log')
        rh = RotatingFileHandler(logfile, maxBytes=50*1024*1024,backupCount=10)
        rh.setLevel(self._loglevel)
        fmter = logging.Formatter(formatstr)
        rh.setFormatter(fmter)
        self._logger.addHandler(rh)
        self._logger.setLevel(self._loglevel)
        self._connection = None
        self._cursor = None
        self._conn('hy')
        self._callbacks = {}
        self._callbacks[self._up] = IK_STATUS_BREAK_UP
        self._callbacks[self._dn] = IK_STATUS_BREAK_DN
        self._callbacks[self._deviation_dn] = IK_STATUS_DEVIATION_UP
        self._callbacks[self._deviation_up] = IK_STATUS_DEVIATION_DN
        self._callbacks[self._rebound_up] = IK_STATUS_REBOUND_UP
        self._callbacks[self._rebound_dn] = IK_STATUS_REBOUND_DN
        self._callbacks[self._stand_up] = IK_STATUS_STAND_UP
        self._callbacks[self._stand_dn] = IK_STATUS_STAND_DN
        self._callbacks[self._open_up] = IK_STATUS_OPEN_UP
        self._callbacks[self._open_dn] = IK_STATUS_OPEN_DN
        self._callbacks[self._adjustback_up] = IK_STATUS_ADJUST_UP
        self._callbacks[self._adjustback_dn] = IK_STATUS_ADJUST_DN

    def __del__(self):
        if not self._cursor:
            self._cursor.close()
        if not self._connection:
            self._connection.close()
        
    def _conn(self,dbname):
        try:
            self._connection = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._connection.cursor()
            return True
        except Exception,e:
            self._logger.info('iknow connect db[%s] error[%s]'%(dbname,e))
        return False
        
    def _reconn(self,dbname):
        try:
            self._cursor.close()
            self._connection.close()
            self._connection = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._connection.cursor()
            return True
        except Exception,e:
            self._logger.info('iknow reconnect db[%s] error[%s]'%(dbname,e))
        return False

    def _exesqlone(self,sql,param):
        n = 0
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        ret = ()
        if n==1:
            ret = self._cursor.fetchone()
        return ret

    def _exesqlbatch(self,sql,param):
        n = 0
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        ret = ()
        if n>0:
            ret = self._cursor.fetchall()
        return ret
        
    def _task(self,sqls,log=False):
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if log:
                    self._logger.info('iknow execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                self._logger.error('iknow execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._connection.rollback()
                return False
        self._connection.commit()
        return True
        
    def _std(self,list):
        ev = sum(list)/float(len(list))
        all = 0.0
        for it in list:
            all = all + (it-ev)**2
        std = (all/float(len(list)))**0.5
        nwl = []
        for it in list:
            nwl.append(float('%0.4f'%((it-ev)/std)))
        return nwl
        
    def _distance(self,v1,v2):
        all = 0.0
        for i in range(len(v1)):
            all = all + (v1[i]-v2[i])**2
        return all**0.5
        
    def updatelib(self,paras):
        codes = self._exesqlbatch('select distinct code from iknow_data',None)
        handled = 0
        total = float(len(codes))
        for code in codes:
            handled = handled+1
            data = self._exesqlbatch('select date,open,high,low,close from iknow_data where code=%s order by date',(code[0],))
            if len(data)<300:
                continue
            ld = self._exesqlone('select date from iknow.feature_lib where code=%s order by date desc limit 1',(code[0],))
            sqls = []
            for i in range(1,len(data)-1):
                if data[i][0]<'2006-01-01':
                    continue
                if ld and ld[0]>=data[i][0]:
                    continue
                stds = self._std([float(data[i][1]),float(data[i][2]),float(data[i][3]),float(data[i][4]),float(data[i-1][1]),float(data[i-1][2]),float(data[i-1][3]),float(data[i-1][4])])
                hb = 0
                if float(data[i][1])>float(data[i-1][1]):
                    hb = 1
                lb = 0
                if float(data[i][2])<float(data[i-1][2]):
                    lb = 1
                k = 0
                if float(data[i][4])>float(data[i][1]):
                    k = 1
                fv = '%d%d%d'%(hb,lb,k)
                nhb = 0
                if float(data[i+1][1])>float(data[i][1]):
                    nhb = 1
                nlb = 0
                if float(data[i+1][2])<float(data[i][2]):
                    nlb = 1
                nk = 0
                if float(data[i+1][4])>float(data[i+1][1]):
                    nk = 1
                close = float(data[i][4])
                nopenr = float('%0.4f'%((float(data[i+1][1])-close)/close))
                nhighr = float('%0.4f'%((float(data[i+1][2])-close)/close))
                nlowr = float('%0.4f'%((float(data[i+1][3])-close)/close))
                ncloser = float('%0.4f'%((float(data[i+1][4])-close)/close))
                sqls.append(('insert into iknow.feature_lib(code,date,fv,stdo,stdh,stdl,stdc,stdop,stdhp,stdlp,stdcp,nhb,nlb,nk,nopenr,nhighr,nlowr,ncloser) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code[0],data[i][0],fv,)+tuple(stds)+(nhb,nlb,nk,nopenr,nhighr,nlowr,ncloser)))
            self._task(sqls)
            self._logger.info('iknow updatelib handle progress[%d-%d-%0.2f%%] code[%s]....'%(handled,total,100*(handled/total),code[0]))
        return 'OK'
            
    def _medians(self,mat):
        if len(mat)!=0:
            length = len(mat)
            ohlcs = [[row[i] for row in mat] for i in range(4)]
            ohlcs[0].sort()
            ohlcs[1].sort()
            ohlcs[2].sort()
            ohlcs[3].sort()
            return ('%0.4f'%ohlcs[0][length/2],'%0.4f'%ohlcs[1][length/2],'%0.4f'%ohlcs[2][length/2],'%0.4f'%ohlcs[3][length/2])
        else:
            return (0,0,0,0)
            
    def feature_tell(self,paras):
        if not paras.has_key('date'):
            return self.defaultoutput({'output':'no date'})
        date = paras['date']
        self._logger.info('iknow tell[%s] task start....'%date)
        codes = self._exesqlbatch('select distinct code from iknow_data',None)
        handled = 0
        total = float(len(codes))
        thv = 0.382
        maxlen = 256
        sqls = []
        for code in codes:
            handled = handled+1
            data = self._exesqlbatch('select date,open,high,low,close from iknow_data where code=%s and date<=%s order by date desc limit 2',(code[0],date))
            if len(data)!=2:
                continue
            if data[0][0]!=date:
                continue
            hb = 0
            if float(data[0][1])>float(data[1][1]):
                hb = 1
            lb = 0
            if float(data[0][2])<float(data[1][2]):
                lb = 1
            k = 0
            if float(data[0][4])>float(data[0][1]):
                k = 1
            fv = '%d%d%d'%(hb,lb,k)
            pd = [data[0][1],data[0][2],data[0][3],data[0][4],data[1][1],data[1][2],data[1][3],data[1][4]]
            stds = self._std(pd)
            #self._logger.info('iknow code[%s] date[%s] fv[%s],data[%s]'%(code[0],date,fv,str(pd)))
            rng = self._exesqlbatch('select code,date,stdo,stdh,stdl,stdc,stdop,stdhp,stdlp,stdcp,nhb,nlb,nk,nopenr,nhighr,nlowr,ncloser from iknow.feature_lib where date<%s and fv=%s and stdo>%s and stdo<%s and stdh>%s and stdh<%s and stdl>%s and stdl<%s and stdc>%s and stdc<%s and stdop>%s and stdop<%s and stdhp>%s and stdhp<%s and stdlp>%s and stdlp<%s and stdcp>%s and stdcp<%s',(date,fv,stds[0]-thv,stds[0]+thv,stds[1]-thv,stds[1]+thv,stds[2]-thv,stds[2]+thv,stds[3]-thv,stds[3]+thv,stds[4]-thv,stds[4]+thv,stds[5]-thv,stds[5]+thv,stds[6]-thv,stds[6]+thv,stds[7]-thv,stds[7]+thv))
            rng = list(rng)
            tmt = []
            for row in rng:
                d = self._distance(stds,row[2:10])
                #self._logger.info('IKNOW TELL code[%s] date[%s] d[%s] stds[%s] target[%s]'%(code[0],date,str(d),str(stds),str(row[2:10])))
                if d<thv:
                    tmt.append((d,row[10],row[11],row[12],row[13],row[14],row[15],row[16]))
            if len(tmt)==0:
                continue
            realhit = len(tmt)
            if len(tmt)>maxlen:
                tmt.sort()
                tmt = tmt[:maxlen]
            cnt = len(tmt)
            hrmt = []
            hgmt = []
            lrmt = []
            lgmt = []
            brmt = []
            bgmt = []
            nrmt = []
            ngmt = []
            for row in tmt:
                nhb = int(row[1])
                nlb = int(row[2])
                nk = int(row[3])
                if nhb==1 and nlb==0 and nk==1:
                    hrmt.append((row[4],row[5],row[6],row[7]))
                elif nhb==1 and nlb==0 and nk==0:
                    hgmt.append((row[4],row[5],row[6],row[7]))
                elif nhb==0 and nlb==1 and nk==1:
                    lrmt.append((row[4],row[5],row[6],row[7]))
                elif nhb==0 and nlb==1 and nk==0:
                    lgmt.append((row[4],row[5],row[6],row[7]))
                elif nhb==1 and nlb==1 and nk==1:
                    brmt.append((row[4],row[5],row[6],row[7]))
                elif nhb==1 and nlb==1 and nk==0:
                    bgmt.append((row[4],row[5],row[6],row[7]))
                elif nhb==0 and nlb==0 and nk==1:
                    nrmt.append((row[4],row[5],row[6],row[7]))
                elif nhb==0 and nlb==0 and nk==0:
                    ngmt.append((row[4],row[5],row[6],row[7]))
            hbrp = '%0.4f'%(float(len(hrmt))/float(cnt))
            hbgp = '%0.4f'%(float(len(hgmt))/float(cnt))
            lbrp = '%0.4f'%(float(len(lrmt))/float(cnt))
            lbgp = '%0.4f'%(float(len(lgmt))/float(cnt))
            bbrp = '%0.4f'%(float(len(brmt))/float(cnt))
            bbgp = '%0.4f'%(float(len(bgmt))/float(cnt))
            nbrp = '%0.4f'%(float(len(nrmt))/float(cnt))
            nbgp = '%0.4f'%(float(len(ngmt))/float(cnt))
            self._logger.info('iknow tell code[%s] date[%s] hbrp[%s] hbgp[%s] lbrp[%s] lbgp[%s] bbrp[%s] bbgp[%s] nbrp[%s] nbgp[%s]'%(code[0],date,hbrp,hbgp,lbrp,lbgp,bbrp,bbgp,nbrp,nbgp))
            hbrm = self._medians(hrmt)
            hbgm = self._medians(hgmt)
            lbrm = self._medians(lrmt)
            lbgm = self._medians(lgmt)
            bbrm = self._medians(brmt)
            bbgm = self._medians(bgmt)
            nbrm = self._medians(nrmt)
            nbgm = self._medians(ngmt)
            sqls.append(('insert into iknow.feature_tell(code,date,count,hbrp,hbgp,lbrp,lbgp,bbrp,bbgp,nbrp,nbgp,hbr_mnopenr,hbr_mnhighr,hbr_mnlowp,hbr_mnclosep,hbg_mnopenr,hbg_mnhighr,hbg_mnlowr,hbg_mncloser,lbr_mnopenr,lbr_mnhighr,lbr_mnlowr,lbr_mncloser,lbg_mnopenr,lbg_mnhighr,lbg_mnlowr,lbg_mncloser,bbr_mnopenr,bbr_mnhighr,bbr_mnlowr,bbr_mncloser,bbg_mnopenr,bbg_mnhighr,bbg_mnlowr,bbg_mncloser,nbr_mnopenr,nbr_mnhighr,nbr_mnlowr,nbr_mncloser,nbg_mnopenr,nbg_mnhighr,nbg_mnlowr,nbg_mncloser) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code[0],date,cnt,hbrp,hbgp,lbrp,lbgp,bbrp,bbgp,nbrp,nbgp,)+hbrm+hbgm+lbrm+lbgm+bbrm+bbgm+nbrm+nbgm))
            self._logger.info('iknow tell handle progress[%0.2f%%] code[%s] date[%s] range[%d] hit[%d] use[%d]....'%(100*(handled/total),code[0],date,len(rng),realhit,len(tmt)))
        self._task(sqls)
        self._logger.info('iknow tell[%s] task done,executed sqls[%d]....'%(date,len(sqls)))
        return json.dumps(['OK'])
        
    def _up(self,para):
        code = para['code']
        date = para['date']
        redm = para['redm']
        ms = self._exesqlbatch('select date,macd from hy.iknow_macd where code=%s and date<=%s order by date desc limit 3',(code,date))
        if ms[0][0]==date and ms[0][1]>=redm and (ms[1][1]<0 or ms[2][1]<0):
            return True
        return False
        
    def _dn(self,para):
        code = para['code']
        date = para['date']
        grem = para['grem']
        ms = self._exesqlbatch('select date,macd from hy.iknow_macd where code=%s and date<=%s order by date desc limit 3',(code,date))
        if ms[0][0]==date and ms[0][1]<=grem and (ms[1][1]>0 or ms[2][1]>0):
            return True
        return False

    def _deviation_dn(self,para):
        code = para['code']
        date = para['date']
        grem = para['grem']
        ms = self._exesqlbatch('select date,macd from hy.iknow_macd where code=%s and date<=%s order by date desc limit 2',(code,date))
        if ms[0][1]<0 and ms[1][1]<grem and ms[0][1]>ms[1][1]:
            lb = self._exesqlone('select lb from hy.iknow_kinfo where code=%s and date=%s', (code,date))
            if lb[0]==1:
                return True
        return False
        
    def _deviation_up(self,para):
        code = para['code']
        date = para['date']
        redm = para['redm']
        ms = self._exesqlbatch('select date,macd from hy.iknow_macd where code=%s and date<=%s order by date desc limit 2',(code,date))
        if ms[0][1]>0 and ms[1][1]>redm and ms[0][1]<ms[1][1]:
            hb = self._exesqlone('select hb from hy.iknow_kinfo where code=%s and date=%s', (code,date))
            if hb[0]==1:
                return True
        return False
        
    def _rebound_up(self,para):
        code = para['code']
        date = para['date']
        ms = self._exesqlbatch('select date,macd from hy.iknow_macd where code=%s and date<=%s order by date desc limit 2',(code,date))
        if ms[0][1]<0 and ms[0][1]>ms[1][1]:
            lb = self._exesqlone('select lb from hy.iknow_kinfo where code=%s and date=%s', (code,date))
            if lb[0]==1:
                kd = self._exesqlone('select k,d from hy.iknow_bollkd where code=%s and date=%s',(code,date))
                if kd[0]>kd[1]:
                    return True
        return False
        
    def _rebound_dn(self,para):
        code = para['code']
        date = para['date']
        ms = self._exesqlbatch('select date,macd from hy.iknow_macd where code=%s and date<=%s order by date desc limit 2',(code,date))
        if ms[0][1]>0 and ms[0][1]<ms[1][1]:
            hb = self._exesqlone('select hb from hy.iknow_kinfo where code=%s and date=%s', (code,date))
            if hb[0]==1:
                kd = self._exesqlone('select k,d from hy.iknow_bollkd where code=%s and date=%s',(code,date))
                if kd[0]<kd[1]:
                    return True
        return False
        
    def _stand_up(self,para):
        code = para['code']
        date = para['date']
        pd = self._exesqlbatch('select date,close from hy.iknow_data where code=%s and date<=%s order by date desc limit 2',(code,date))
        mid = self._exesqlone('select mid,k,d from hy.iknow_bollkd where code=%s and date=%s',(code,pd[0][0]))
        midp = self._exesqlone('select mid from hy.iknow_bollkd where code=%s and date=%s',(code,pd[1][0]))
        if pd[0][1]>mid[0] and pd[1][1]<midp[0] and mid[1]>mid[2]:
            return True
        return False

    def _stand_dn(self,para):
        code = para['code']
        date = para['date']
        pd = self._exesqlbatch('select date,close from hy.iknow_data where code=%s and date<=%s order by date desc limit 2',(code,date))
        mid = self._exesqlone('select mid,k,d from hy.iknow_bollkd where code=%s and date=%s',(code,pd[0][0]))
        midp = self._exesqlone('select mid from hy.iknow_bollkd where code=%s and date=%s',(code,pd[1][0]))
        if pd[0][1]<mid[0] and pd[1][1]>midp[0] and mid[1]<mid[2]:
            return True
        return False
        
    def _open_up(self,para):
        code = para['code']
        date = para['date']
        stdm = para['stdm']
        pd = self._exesqlbatch('select date,close from hy.iknow_data where code=%s and date<=%s order by date desc limit 2',(code,date))
        mid = self._exesqlone('select mid,std from hy.iknow_bollkd where code=%s and date=%s',(code,pd[0][0]))
        midp = self._exesqlone('select mid,std from hy.iknow_bollkd where code=%s and date=%s',(code,pd[1][0]))
        if mid[0]>stdm and midp[0]<stdm:
            if pd[0][1]>mid[0]+2*mid[1] and pd[1][1]<midp[0]+2*midp[1]:
                return True
        return False
        
    def _open_dn(self,para):
        code = para['code']
        date = para['date']
        stdm = para['stdm']
        pd = self._exesqlbatch('select date,close from hy.iknow_data where code=%s and date<=%s order by date desc limit 2',(code,date))
        mid = self._exesqlone('select mid,std from hy.iknow_bollkd where code=%s and date=%s',(code,pd[0][0]))
        midp = self._exesqlone('select mid,std from hy.iknow_bollkd where code=%s and date=%s',(code,pd[1][0]))
        if mid[0]>stdm and midp[0]<stdm:
            if pd[0][1]<mid[0]-2*mid[1] and pd[1][1]>midp[0]-2*midp[1]:
                return True
        return False
        
    def _adjustback_up(self,para):
        code = para['code']
        date = para['date']
        stdm = para['stdm']
        pd = self._exesqlbatch('select date,low,close from hy.iknow_data where code=%s and date<=%s order by date desc limit 10',(code,date))
        for row in pd:
            up = self._exesqlone('select mid+2*std from hy.iknow_bollkd where code=%s and date=%s',(code,row[0]))
            if row[2]>up[0]:
                std = self._exesqlone('select mid,std from hy.iknow_bollkd where code=%s and date=%s',(code,date))
                if std[1]>stdm and pd[0][1]<std[0] and pd[0][2]>std[0]:
                    return True
        return False
        
    def _adjustback_dn(self,para):
        code = para['code']
        date = para['date']
        stdm = para['stdm']
        pd = self._exesqlbatch('select date,high,close from hy.iknow_data where code=%s and date<=%s order by date desc limit 10',(code,date))
        for row in pd:
            up = self._exesqlone('select mid-2*std from hy.iknow_bollkd where code=%s and date=%s',(code,row[0]))
            if row[2]<up[0]:
                std = self._exesqlone('select std from hy.iknow_bollkd where code=%s and date=%s',(code,date))
                if std[0]>stdm and pd[0][1]>std[0] and pd[0][2]<std[0]:
                    return True
        return False
        
    def _ma_up_dn(self,date):
        self._logger.info('iknow _ma_up_dn[%s] task start....'%date)
        sqls = []
        insqls = [('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_ma where hy.iknow_data.date=%s and hy.iknow_ma.date=%s and hy.iknow_data.code=hy.iknow_ma.code and hy.iknow_data.close>=hy.iknow_ma.ma5',(date,date),IK_STATUS_MA5_UP),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_ma where hy.iknow_data.date=%s and hy.iknow_ma.date=%s and hy.iknow_data.code=hy.iknow_ma.code and hy.iknow_data.close<hy.iknow_ma.ma5',(date,date),IK_STATUS_MA5_DN),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_ma where hy.iknow_data.date=%s and hy.iknow_ma.date=%s and hy.iknow_data.code=hy.iknow_ma.code and hy.iknow_data.close>=hy.iknow_ma.ma10',(date,date),IK_STATUS_MA10_UP),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_ma where hy.iknow_data.date=%s and hy.iknow_ma.date=%s and hy.iknow_data.code=hy.iknow_ma.code and hy.iknow_data.close<hy.iknow_ma.ma10',(date,date),IK_STATUS_MA10_DN),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_ma where hy.iknow_data.date=%s and hy.iknow_ma.date=%s and hy.iknow_data.code=hy.iknow_ma.code and hy.iknow_data.close>=hy.iknow_ma.ma20',(date,date),IK_STATUS_MA20_UP),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_ma where hy.iknow_data.date=%s and hy.iknow_ma.date=%s and hy.iknow_data.code=hy.iknow_ma.code and hy.iknow_data.close<hy.iknow_ma.ma20',(date,date),IK_STATUS_MA20_DN),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_ma where hy.iknow_data.date=%s and hy.iknow_ma.date=%s and hy.iknow_data.code=hy.iknow_ma.code and hy.iknow_data.close>=hy.iknow_ma.ma30',(date,date),IK_STATUS_MA30_UP),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_ma where hy.iknow_data.date=%s and hy.iknow_ma.date=%s and hy.iknow_data.code=hy.iknow_ma.code and hy.iknow_data.close<hy.iknow_ma.ma30',(date,date),IK_STATUS_MA30_DN),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_ma where hy.iknow_data.date=%s and hy.iknow_ma.date=%s and hy.iknow_data.code=hy.iknow_ma.code and hy.iknow_data.close>=hy.iknow_ma.ma60',(date,date),IK_STATUS_MA60_UP),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_ma where hy.iknow_data.date=%s and hy.iknow_ma.date=%s and hy.iknow_data.code=hy.iknow_ma.code and hy.iknow_data.close<hy.iknow_ma.ma30',(date,date),IK_STATUS_MA60_DN),]
        for sql in insqls:
            output = self._exesqlbatch(sql[0],sql[1])
            for row in output:
                sqls.append(('insert into iknow.trend_tell(code,date,status,volwy) values(%s,%s,%s,%s)',(row[0],date,sql[2],row[1])))
        self._task(sqls)
        self._logger.info('iknow _ma_up_dn[%s] task done sqls[%d]....'%(date,len(sqls)))

    def trend_tell(self,paras):
        if not paras.has_key('date'):
            return self.defaultoutput({'output':'no date'})
        date = paras['date']
        self._logger.info('iknow trend_tell[%s] task start....'%date)
        codes = self._exesqlbatch('select distinct code from iknow_data',None)
        handled = 0
        total = float(len(codes))
        sqls = []
        for code in codes:
            para = {}
            handled = handled+1
            #self._logger.info('iknow trend_tell begin handle code[%s] date[%s]....'%(code[0],date))
            data = self._exesqlbatch('select date,open,high,low,close from hy.iknow_data where code=%s and date<=%s order by date desc limit 2',(code[0],date))
            if len(data)!=2:
                continue
            if data[0][0]!=date:
                continue
            para['code'] = code[0]
            para['date'] = date
            redm = self._exesqlbatch('select macd from hy.iknow_macd where code=%s and date<=%s and macd>0 order by macd',(code[0],date))
            if len(redm)==0:
                continue
            redm = redm[len(redm)/2][0]
            para['redm'] = redm
            grem = self._exesqlbatch('select macd from hy.iknow_macd where code=%s and date<=%s and macd<0 order by macd',(code[0],date))
            if len(grem)==0:
                continue
            grem = grem[len(grem)/2][0]
            para['grem'] = grem
            stdm = self._exesqlbatch('select std from hy.iknow_bollkd where code=%s and date<=%s order by std',(code[0],date))
            if len(stdm)==0:
                continue
            stdm = stdm[len(stdm)/2][0]
            para['stdm'] = stdm
            for callback in self._callbacks.keys():
                try:
                    if callback(para):
                        cd = para['code']
                        dt = para['date']
                        st = self._callbacks[callback]
                        vol = self._exesqlone('select volwy from hy.iknow_data where code=%s and date=%s',(cd,dt))
                        sqls.append(('insert into iknow.trend_tell(code,date,status,volwy) values(%s,%s,%s,%s)',(cd,dt,st,vol[0])))
                except Exception,e:
                    self._logger.warn('iknow trend_tell exception[%s]...'%e)
            self._logger.info('iknow trend_tell handle progress[%0.2f%%] code[%s] date[%s]....'%(100*(handled/total),code[0],date))
        self._task(sqls)
        self._ma_up_dn(date)
        self._logger.info('iknow trend_tell[%s] task done,executed sqls[%d]....'%(date,len(sqls)))
        
    def do_trend(self,paras):
        start = '2016-01-01'
        if not paras.has_key('start'):
            ld = self._exesqlone('select date from iknow.trend_tell order by date desc limit 1',None)
            if len(ld)>0 and ld[0]:
                start = ld[0]
        else:
            start = paras['start']
        dts = []
        if paras.has_key('end'):
            dts = self._exesqlbatch('select distinct date from hy.iknow_data where date>%s and date<=%s and date not in (select distinct date from iknow.trend_tell) order by date desc',(start,paras['end']))
        else:
            dts = self._exesqlbatch('select distinct date from hy.iknow_data where date>%s and date not in (select distinct date from iknow.trend_tell) order by date desc',(start,))
        for dt in dts:
            para = {'date':dt[0]}
            self.trend_tell(para)
        return json.dumps(['OK'])
            
    def do_feature(self,paras):
        start = '2018-06-01'
        if not paras.has_key('start'):
            ld = self._exesqlone('select date from iknow.feature_tell order by date desc limit 1',None)
            if len(ld)>0 and ld[0]:
                start = ld[0]
        else:
            start = paras['start']
        dts = []
        if paras.has_key('end'):
            dts = self._exesqlbatch('select distinct date from hy.iknow_data where date>%s and date<=%s and date not in (select distinct date from iknow.feature_tell) order by date desc',(start,paras['end']))
        else:
            dts = self._exesqlbatch('select distinct date from hy.iknow_data where date>%s and date not in (select distinct date from iknow.feature_tell) order by date desc',(start,))
        for dt in dts:
            para = {'date':dt[0]}
            self.feature_tell(para)
        return json.dumps(['OK'])
        
    def q_list(self,paras):
        lis = []
        for name in dir(self):
            if name[:2]=='q_':
                lis.append(name)
        return json.dumps(lis)
        
    def q_base(self,paras):
        lim = 40
        if paras.has_key('max'):
            lim = int(paras['max'])
        mat = []
        dts = self._exesqlbatch('select distinct date from hy.iknow_kinfo order by date desc limit %d'%lim,None)
        for dt in dts:
            all = self._exesqlone('select count(*) from hy.iknow_kinfo where date=%s',(dt[0],))
            hbs = self._exesqlone('select count(*) from hy.iknow_kinfo where date=%s and hb=1',(dt[0],))
            lbs = self._exesqlone('select count(*) from hy.iknow_kinfo where date=%s and lb=1',(dt[0],))
            src = self._exesqlone('select avg(csrc) from hy.iknow_kinfo where date=%s',(dt[0],))
            mat.append((dt[0],all[0],'%0.2f'%(100*(hbs[0]/all[0])),'%0.2f'%(100*(lbs[0]/all[0])),'%0.2f'%(100*src[0])))
        return json.dumps(mat)

    def q_vol(self,paras):
        if not paras.has_key('date'):
            return self.defaultoutput({'output':'date missing'})
        date = paras['date']
        allvol = self._exesqlone('select sum(volwy) from hy.iknow_data where date=%s',(date,))
        output = []
        if len(allvol)>0 and allvol[0]:
            output.append(allvol[0])
        return json.dumps(output)

    def q_next(self,paras):
        if not (paras.has_key('code') and paras.has_key('date')):
            return self.defaultoutput({'output':'code or date missing'})
        code = paras['code']
        date = paras['date']
        data = self._exesqlone('select ')
        
    def q_status(self,paras):
        date = None
        if not paras.has_key('date'):
            ld = self._exesqlone('select date from iknow.trend_tell order by date desc limit 1',None)
            if len(ld)>0 and ld[0]:
                date = ld[0]
        if not date:
            return self.defaultoutput({'output':'date missing'})
        data = []
        if paras.has_key('status'):
            data = self._exesqlbatch('select code,status,volwy from iknow.trend_tell where date=%s and status=%s and status<=50',(date,paras['status']))
        else:
            data = self._exesqlbatch('select code,status,volwy from iknow.trend_tell where date=%s and status<=50',(date,))
        output = []
        for row in data:
            name = self._exesqlone('select name,bdname from hy.iknow_name where code=%s',(row[0],))
            output.append({'code':row[0],'name':name[0],'bdname':name[1],'status':row[1],'volwy':row[2]})
        return json.dumps(output)
        
    def q_ma(self,paras):
        date = None
        if not paras.has_key('date'):
            ld = self._exesqlone('select date from iknow.trend_tell order by date desc limit 1',None)
            if len(ld)>0 and ld[0]:
                date = ld[0]
        if not (date or paras.has_key('ma')):
            return self.defaultoutput({'output':'date or ma missing'})
        ma = paras['ma']
        data = []
        if ma=='5':
            data = self._exesqlbatch('select code,status,volwy from iknow.trend_tell where date=%s and (status=%s or status=%s)',(date,IK_STATUS_MA5_UP,IK_STATUS_MA5_DN))
        elif ma=='10':
            data = self._exesqlbatch('select code,status,volwy from iknow.trend_tell where date=%s and (status=%s or status=%s)',(date,IK_STATUS_MA10_UP,IK_STATUS_MA10_DN))
        elif ma=='20':
            data = self._exesqlbatch('select code,status,volwy from iknow.trend_tell where date=%s and (status=%s or status=%s)',(date,IK_STATUS_MA20_UP,IK_STATUS_MA20_DN))
        elif ma=='30':
            data = self._exesqlbatch('select code,status,volwy from iknow.trend_tell where date=%s and (status=%s or status=%s)',(date,IK_STATUS_MA30_UP,IK_STATUS_MA30_DN))
        elif ma=='60':
            data = self._exesqlbatch('select code,status,volwy from iknow.trend_tell where date=%s and (status=%s or status=%s)',(date,IK_STATUS_MA60_UP,IK_STATUS_MA60_DN))
        elif ma=='all':
            data = self._exesqlbatch('select code,status,volwy from iknow.trend_tell where date=%s',(date,))
        output = []
        for row in data:
            name = self._exesqlone('select name,bdname from hy.iknow_name where code=%s',(row[0],))
            close = self._exesqlone('select close from hy.iknow_data where code=%s and date=%s',(row[0],date))
            status = int(row[1])
            ma = (0,)
            if status==IK_STATUS_MA5_UP or status==IK_STATUS_MA5_DN:
                ma = self._exesqlone('select ma5 from hy.iknow_ma where code=%s and date=%s',(row[0],date))
            elif status==IK_STATUS_MA10_UP or status==IK_STATUS_MA10_DN:
                ma = self._exesqlone('select ma10 from hy.iknow_ma where code=%s and date=%s',(row[0],date))
            elif status==IK_STATUS_MA20_UP or status==IK_STATUS_MA20_DN:
                ma = self._exesqlone('select ma20 from hy.iknow_ma where code=%s and date=%s',(row[0],date))
            elif status==IK_STATUS_MA30_UP or status==IK_STATUS_MA30_DN:
                ma = self._exesqlone('select ma30 from hy.iknow_ma where code=%s and date=%s',(row[0],date))
            elif status==IK_STATUS_MA60_UP or status==IK_STATUS_MA60_DN:
                ma = self._exesqlone('select ma60 from hy.iknow_ma where code=%s and date=%s',(row[0],date))
            ma = ma[0]
            output.append({'code':row[0],'name':name[0],'bdname':name[1],'status':row[1],'volwy':row[2],'ma':ma,'close':close[0]})
        return json.dumps(output)

    def defaultoutput(self,paras):
        if paras.has_key('output'):
            return json.dumps(paras['output'])
        return json.dumps(['DONE'])

    def _parse(self,querystr):
        paras = {}
        items = querystr[1:].split('&')
        for it in items:
            nvs = it.split('=')
            paras[nvs[0]] = nvs[1]
        return paras

    def GET(self):
        if len(web.ctx.query)==0:
            return 'OK'
        paras = self._parse(web.ctx.query)
        fun = getattr(self,paras['name'],self.defaultoutput)
        return fun(paras)
        
if __name__ == "__main__":
    urls = (
        '/iknow', 'iknow'
    )
    app = web.application(urls, globals())
    app.run()
        
        
        
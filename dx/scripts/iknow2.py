#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import socket
import MySQLdb
import signal
from optparse import OptionParser
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil

g_iu = ikutil()

class iknow2:
    def __init__(self):
        self._conf = g_iu.loadcsv(os.path.join(os.path.join(g_home,'etc'),'code.csv'),{},0)
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()
    
    def __del__(self):
        self._cursor.close()
        self._conn.close()

    def _codes(self):
        codes = self._conf.keys()
        codes.sort()
        return codes

    def _reconn(self):
        self._cursor.close()
        self._conn.close()
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()

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
        n = self._cursor.execute(sql,param)
        ret = ()
        if n>0:
            ret = self._cursor.fetchall()
        return ret
        
    def _task(self,sqls,log=False):
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if log:
                    g_logger.info('ikdaily execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                g_logger.error('ikdaily execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._conn.rollback()
                return False
        self._conn.commit()
        return True

    def prepare(self):
        self._reconn()
        dir = os.path.join(g_home,'ik2_prepare')
        g_iu.mkdir(dir)
        ld = self._exesqlone('select date from iknow2_prepare order by date desc limit 1',None)
        start='2005-01-01'
        if len(ld) > 0:
            start = ld[0]
        ofn = os.path.join(dir,'%s.csv'%start)
        codes = self._codes()
        #mat = []
        for code in codes:
            mat = []
            cnt = self._exesqlone('select count(*) from iknow_data where code=%s',(code,))
            if cnt[0]<360:
                continue
            dts = self._exesqlbatch('select date from iknow_data where code=%s order by date',(code,))
            for dt in dts:
                if dt[0]<=start:
                    continue
                g_iu.log(logging.INFO,'iknow2 prepare handling code[%s] date[%s]....'%(code,dt[0]))
                dtrng = self._exesqlbatch('select date from iknow_data where code=%s and date<=%s order by date desc limit 120',(code,dt[0]))
                begin = dtrng[-1][0]
                print 'deal with code[%s] date[%s-%s]....'%(code,begin,dt[0])
                data = self._exesqlone('select avg(zdf),std(zdf),avg(zf),std(zf) from iknow_data where code=%s and date<=%s and date>=%s',(code,dt[0],begin))
                scr = self._exesqlone('select avg((close-low)/(high-low)),std((close-low)/(high-low))')
                mat.append((code,dt[0],data[0],data[1],data[2],data[3]))
            ofn = os.path.join(dir,'%s_%s.csv'%(code,start))
            g_iu.dumpfile(ofn,mat)
            g_iu.importdata(ofn,'iknow2_prepare')
        
    def fillbase(self):
        self._reconn()
        dir = os.path.join(g_home,'ik2_base')
        g_iu.mkdir(dir)
        ld = self._exesqlone('select date from iknow2_base order by date desc limit 1',None)
        start='2005-01-01'
        if len(ld) > 0:
            start = ld[0]
        ofn = os.path.join(dir,'%s.csv'%start)
        codes = self._codes()
        #mat = []
        for code in codes:
            mat = []
            pred = self._exesqlone('select date from iknow2_prepare where code=%s order by date limit 1',(code,))
            if pred[0]>start:
                start=pred[0]
            begin = self._exesqlbatch('select date from iknow_data where code=%s and date<%s order by date desc limit 2',(code,start))
            begin = begin[-1][0]
            data = self._exesqlbatch('select date,open,high,low,close,zdf,zf,(close-open)*volh from iknow_data where code=%s and date>=%s order by date',(code,begin))
            for i in range(2,len(data)):
                g_iu.log(logging.INFO,'iknow2 fillbase handling code[%s] date[%s]....'%(code,data[i][0]))
                hb=0
                if data[i][2]>data[i-1][2]:
                    hb=1
                lb=0
                if data[i][3]<data[i-1][3]:
                    lb=1
                k=0
                if data[i][4]>data[i][1]:
                    k=1
                v1 = 0
                if (data[i][7]-data[i-1][7])>0:
                    v1 = 1
                v2 = 0
                if (data[i][7]+data[i-2][7]-2*data[i-1][7])>0:
                    v2 = 1
                pres = self._exesqlone('select zdf120_ev,zdf120_std,zf120_ev,zf120_std from iknow2_prepare where code=%s and date=%s',(code,data[i][0]))
                zdfz = float('%0.4f'%(data[i][5]-pres[0])/pres[1])
                zfz = float('%0.4f'%(data[i][6]-pres[2])/pres[3])
                score = 0.5
                if data[i][2]!=data[i][3]:
                    score = float('%0.4f'%((data[i][4]-data[i][3])/(data[i][2]-data[i][3])))
                openf = float('%0.4f'%((data[i][1]-data[i-1][4])/data[i-1][4]))
                highf = float('%0.4f'%((data[i][2]-data[i-1][4])/data[i-1][4]))
                lowf = float('%0.4f'%((data[i][3]-data[i-1][4])/data[i-1][4]))
                closef = float('%0.4f'%((data[i][4]-data[i-1][4])/data[i-1][4]))
                mat.append((code,data[i][0],hb,lb,k,v1,v2,zdfz,zfz,score,openf,highf,lowf,closef))
            ofn = os.path.join(dir,'%s_%s.csv'%(code,start))
            g_iu.dumpfile(ofn,mat)
            g_iu.importdata(ofn,'iknow2_base')
        
    def _begin_tell(self,default):
        ld = self._exesqlone('select date from iknow2_tell order by date desc limit 1',None)
        start = default
        if len(ld) > 0:
            start = ld[0]
        return start
        
    def _allfv(self,date):
        fd = {}
        codes = self._codes()
        for code in codes:
            base = self._exesqlone('select hb,lb,k,v1,v2,zdfz,zfz,score from iknow2_base where code=%s and date=%s',(code,dt))
            if len(base)==0:
                continue
            if fd.has_key((base[0],base[1],base[2],base[3],base[4])):
                fd[(base[0],base[1],base[2],base[3],base[4])].append((code,base[5],base[6],base[7]))
            else:
                fd[(base[0],base[1],base[2],base[3],base[4])]=[(code,base[5],base[6],base[7])]
        return fd
        
    def _similarities(self,fvs,baseset):
        cdtd = {}
        for item in fvs:
            ds = []
            code = item[0]
            for row in baseset:
                d = abs(item[1]-row[2])+abs(item[2]-row[3])+abs(item[3]-row[4])
                ds.append((d,row[0],row[1]))
            thv = max(len(ds)/800,13)
            ds.sort()
            ds=ds[:thv]
            data = []
            for dd in ds:
                sim = self._exesqlone('select hb,lb,k,v1,v2,zdfz,zfz,score,openf,highf,lowf,closef from iknow2_base where code=%s and date>%s order by date limit 1',(dd[1],dd[2]))
                if len(sim)>0:
                    data.append((sim[0],sim[1],sim[2],sim[3],sim[4],sim[5],sim[6],sim[7],sim[8],sim[9],sim[10],sim[11]))
            cdtd[code]=data
        return cdtd
        
    def _extract(self,simmat):
        perf = [[row[i] for row in simmat] for i in range(12)]
        hb = float('%0.4f'%float(sum(perf[0]))/len(perf[0]))
        lb = float('%0.4f'%float(sum(perf[1]))/len(perf[1]))
        k = float('%0.4f'%float(sum(perf[2]))/len(perf[2]))
        v1 = float('%0.4f'%float(sum(perf[3]))/len(perf[3]))
        v2 = float('%0.4f'%float(sum(perf[4]))/len(perf[4]))
        zdfz = float('%0.4f'%float(sum(perf[5]))/len(perf[5]))
        zfz = float('%0.4f'%float(sum(perf[6]))/len(perf[6]))
        score = float('%0.4f'%float(sum(perf[7]))/len(perf[7]))
        perf[8].sort()
        ol = perf[8][2:-2]
        openf = float('%0.4f'%float(sum(ol))/len(ol))
        perf[9].sort()
        hl = perf[9][2:-2]
        highf = float('%0.4f'%float(sum(hl))/len(hl))
        perf[10].sort()
        ll = perf[10][2:-2]
        lowf = float('%0.4f'%float(sum(ll))/len(ll))
        perf[11].sort()
        cl = perf[11][2:-2]
        closef = float('%0.4f'%float(sum(cl))/len(cl))
        return (hb,lb,k,v1,v2,zdfz,zfz,score,openf,highf,lowf,closef)

    def tell(self):
        self._reconn()
        dir = os.path.join(g_home,'ik2_tell')
        g_iu.mkdir(dir)
        start = self._begin_tell('2018-01-01')
        ofn = os.path.join(dir,'%s.csv'%start)
        mat = []
        dts = self._exesqlbatch('select distinct date from iknow2_base where date>%s order by date',(start,))
        for dt in dts:
            mat = []
            fd = self._allfv(dt)
            data = {}
            for k in fd.keys():
                baseset = self._exesqlbatch('select code,date,zdfz,zfz,score from iknow2_base where hb=%s and lb=%s and k=%s and v1=%s and v2=%s and date<%s',(k[0],k[1],k[2],k[3],k[4],dt))
                data.update(self._similarities(fd[k],baseset))
            for code in data.keys():
                g_iu.log(logging.INFO,'iknow2 tell handling date[%s] code[%s]....'%(dt,code))
                tell = self._extract(data[code])
                mat.append((code,dt)+tell)
            ofn = os.path.join(dir,'ik2_tell_%s.csv'%(code,dt))
            g_iu.dumpfile(ofn,mat)
            g_iu.importdata(ofn,'iknow2_tell')

    def dailyrun(self):
        self.prepare()
        self.fillbase()
        self.tell()

if __name__ == "__main__":
    ik = iknow2()
    ik.prepare()
    ik.fillbase()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
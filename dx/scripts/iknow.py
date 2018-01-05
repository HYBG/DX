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


class iknow:
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

    def _setstation(self,val):
        self._reconn()
        self._task([('update iknow_conf set value=%s where name=%s',(str(val),'station'))])

    def _guass(self,lis):
        all = sum(lis)
        ev = all/float(len(lis))
        alls = 0
        for it in lis:
            alls = alls + (it-ev)**2
        std = (alls/float(len(lis)))**0.5
        return (ev,std)

    def _upattr(self):
        codes = self._codes()
        volpara = 5
        macdparan1 = 12
        macdparan2 = 26
        macdparan3 = 9
        macdmaxp = 10
        now = datetime.datetime.now()
        ofn = os.path.join(os.path.join(g_home,'tmp'),'iknow_attr_%04d%02d%02d%02d%02d%02d.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
        f = open(ofn,'w')
        g_iu.log(logging.INFO,'iknow upattr task[%s] start....'%ofn)
        for code in codes:
            g_iu.log(logging.INFO,'iknow upattr handling code[%s]....'%code)
            ldi = self._exesqlone('select date,volev,emaf,emas,dea,bar,mt,mp,seq from iknow_attr where code=%s order by date desc limit 1',(code,))
            pemaf = 0.0
            pemas = 0.0
            pvol = 0.0
            pdea = 0
            pbar = 0
            pmt = 1
            pmp = 1
            pseq = 0
            sql = 'select date,open,high,low,close,volh,zdf from iknow_data where code=%s order by date'
            param = (code,)
            if len(ldi)>0:
                sql = 'select date,open,high,low,close,volh,zdf from iknow_data where code=%s and date>=%s order by date'
                param = (code,ldi[0])
                pemaf = float(ldi[2])
                pemas = float(ldi[3])
                pvol = float(ldi[1])
                pdea = float(ldi[4])
                pbar = int(ldi[5])
                pmt = int(ldi[6])
                pmp = int(ldi[7])
                pseq = int(ldi[8])
            rows = self._exesqlbatch(sql,param)
            if len(rows)>1:
                pemaf = float(rows[0][4])
                pemas = float(rows[0][4])
                pvol = float(rows[0][4])
            for i in range(1,len(rows)):
                op = float(rows[i][1])
                high = float(rows[i][2])
                low = float(rows[i][3])
                close = float(rows[i][4])
                seq = pseq+1
                oscr = 50.0
                cscr = 50.0
                if (high != low):
                    oscr = 100*((op-low)/(high-low))
                    cscr = 100*((close-low)/(high-low))
                hb = 0
                lb = 0
                if (high>float(rows[i-1][2])):
                    hb = 1
                if (low<float(rows[i-1][3])):
                    lb = 1
                vrf = float(rows[i][5])/pvol
                pvol = 2.0*pvol/(volpara+1.0) + ((volpara-1.0)*float(rows[i][5]))/(volpara+1.0)
                vr = 5
                if vrf<=0.8:
                    vr = 1
                elif vrf<=1.2:
                    vr = 2
                elif vrf<=2:
                    vr = 3
                elif vrf<=5:
                    vr = 4
                emaf = 2*close/(macdparan1+1)+(macdparan1-1)*pemaf/(macdparan1+1)
                emas = 2*close/(macdparan2+1)+(macdparan2-1)*pemas/(macdparan2+1)
                diff = emaf-emas
                dea  = 2*diff/(macdparan3+1)+(macdparan3-1)*pdea/(macdparan3+1)
                bar = 2*(diff-dea)
                tp = ()
                if (pmt == 1):
                    if (bar <= pbar):
                        tp = (1,min(pmp+1,macdmaxp))
                    else:
                        if (bar < 0):
                            tp = (2,1)
                        else:
                            tp = (3,1)
                elif (pmt == 2):
                    if (bar <= pbar):
                        tp = (1,1)
                    else:
                        if (bar < 0):
                            tp = (2,min(pmp+1,macdmaxp))
                        else:
                            tp = (3,1)
                elif (pmt == 3):
                    if (bar < pbar):
                        if (bar < 0):
                            tp = (1,1)
                        else:
                            tp = (4,1)
                    else:
                        tp = (3,min(pmp+1,macdmaxp))
                else:
                    if (bar < pbar):
                        if (bar < 0):
                            tp = (1,1)
                        else:
                            tp = (4,min(pmp+1,macdmaxp))
                    else:
                        tp = (3,1)
                pemaf = emaf
                pemas = emas
                pdea = dea
                pbar = bar
                pmt = tp[0]
                pmp = tp[1]
                pseq = seq
                zdf = float(rows[i][6])
                line = '%s,%s,%d,%0.3f,%0.3f,%0.3f,%0.3f,%0.3f,%d,%d,%d,%0.2f,%0.2f,%d,%d,%0.2f'%(code,rows[i][0],seq,pvol,pemaf,pemas,pdea,pbar,pmt,pmp,vr,oscr,cscr,hb,lb,zdf)
                f.write('%s\n'%line)
        f.close()
        g_iu.importdata(ofn,'iknow_attr')
        g_iu.execmd('rm -fr %s'%ofn)
        g_iu.log(logging.INFO,'iknow upattr task[%s] done....'%ofn)
        self._setstation(2)

    def _updaily(self):
        self._reconn()
        g_iu.log(logging.INFO,'iknow updaily task start....')
        cursor = self._conn.cursor()
        ld = self._exesqlone('select date from iknow_daily order by date desc limit 1',None)
        start = '2005-01-01'
        if len(ld) > 0:
            start = ld[0]
        sqls = []
        dts = self._exesqlbatch('select distinct date from iknow_attr where date>%s order by date',(start,))
        for dt in dts:
            inf = self._exesqlone('select count(*),avg(oscr),avg(cscr) from iknow_attr where date=%s',(dt[0],))
            if len(inf) > 0:
                hbc = self._exesqlone('select count(*) from iknow_attr where date=%s and hb=1',(dt[0],))
                hb = 0.0
                if len(hbc) > 0:
                    hb = float(hbc[0])
                lbc = self._exesqlone('select count(*) from iknow_attr where date=%s and lb=1',(dt[0],))
                lb = 0.0
                if len(lbc) > 0:
                    lb = float(lbc[0])
                hbr = 100*(hb/float(inf[0]))
                lbr = 100*(lb/float(inf[0]))
                sql = 'INSERT INTO iknow_daily(date,count,hbr,lbr,oscore,cscore) VALUES(%s,%s,%s,%s,%s,%s)'
                param = (dt[0],inf[0],'%0.2f'%hbr,'%0.2f'%lbr,'%0.2f'%inf[1],'%0.2f'%inf[2])
                sqls.append((sql,param))
        self._task(sqls)
        g_iu.log(logging.INFO,'iknow updaily task done....')
        self._setstation(3)
        
    def _upbaseset(self):
        self._reconn()
        codes = self._codes()
        now = datetime.datetime.now()
        ofn = os.path.join(os.path.join(g_home,'tmp'),'iknow_bset_%04d%02d%02d%02d%02d%02d.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
        f = open(ofn,'w')
        g_iu.log(logging.INFO,'iknow upbaseset task[%s] start....'%ofn)
        for code in codes:
            ld = self._exesqlone('select date from iknow_bset where code=%s order by date desc limit 1',(code,))
            start = '2001-01-01'
            if len(ld)>0:
                start = ld[0]
            g_iu.log(logging.INFO,'iknow upbaseset handling code[%s] from[%s]....'%(code,start))
            rows = self._exesqlbatch('select date,high,low,close from iknow_data where code=%s and date>%s',(code,start))
            if len(rows) > 5:
                for i in range(len(rows)-5):
                    at = self._exesqlone('select mt,mp,vr,oscr,cscr,zdf,hb,lb from iknow_attr where code=%s and date=%s and seq>120',(code,rows[i][0]))
                    if len(at)==0:
                        continue
                    fv = '%d%02d%d'%(int(at[0]),int(at[1]),int(at[2]))
                    high = float(rows[i][1])
                    low = float(rows[i][2])
                    close = float(rows[i][3])
                    zdfc1 = 100*((float(rows[i+1][3])-close)/close)
                    zdfh1 = 100*((float(rows[i+1][1])-close)/close)
                    zdfl1 = 100*((float(rows[i+1][2])-close)/close)
                    zdfc2 = 100*((float(rows[i+2][3])-close)/close)
                    zdfh2 = 100*((float(rows[i+2][1])-close)/close)
                    zdfl2 = 100*((float(rows[i+2][2])-close)/close)
                    zdfc3 = 100*((float(rows[i+3][3])-close)/close)
                    zdfh3 = 100*((float(rows[i+3][1])-close)/close)
                    zdfl3 = 100*((float(rows[i+3][2])-close)/close)
                    zdfc4 = 100*((float(rows[i+4][3])-close)/close)
                    zdfh4 = 100*((float(rows[i+4][1])-close)/close)
                    zdfl4 = 100*((float(rows[i+4][2])-close)/close)
                    zdfc5 = 100*((float(rows[i+5][3])-close)/close)
                    zdfh5 = 100*((float(rows[i+5][1])-close)/close)
                    zdfl5 = 100*((float(rows[i+5][2])-close)/close)
                    line = '%s,%s,%s,%s,%s,%s,%s,%s,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f'%(code,rows[i][0],fv,at[3],at[4],at[5],at[6],at[7],zdfc1,zdfh1,zdfl1,zdfc2,zdfh2,zdfl2,zdfc3,zdfh3,zdfl3,zdfc4,zdfh4,zdfl4,zdfc5,zdfh5,zdfl5)
                    f.write('%s\n'%line)
        f.close()
        g_iu.importdata(ofn,'iknow_bset')
        g_iu.execmd('rm -fr %s'%ofn)
        g_iu.log(logging.INFO,'iknow upbaseset task[%s] done....'%ofn)
        self._setstation(4)
        
    def _tell(self):
        self._reconn()
        tdir = os.path.join(g_home,'tell')
        g_iu.mkdir(tdir)

        ld = self._exesqlone('select date from iknow_tell order by date desc limit 1',None)
        start = '2017-01-01'
        if len(ld)>0:
            start = ld[0]
        dts = self._exesqlbatch('select date from iknow_daily where date>%s order by date',(start,))
        for dt in dts:
            rows = self._exesqlbatch('select code,mt,mp,vr,oscr,cscr,zdf,hb,lb from iknow_attr where date=%s',(dt[0],))
            g_iu.log(logging.INFO,'iknow feat handling date[%s] %d....'%(dt[0],len(rows)))
            md = {}
            for row in rows:
                fv = '%d%02d%d'%(int(row[1]),int(row[2]),int(row[3]))
                if md.has_key(fv):
                    md[fv].append((row[0],)+row[4:])
                else:
                    md[fv] = [(row[0],)+row[4:]]
            omt = []
            ofn = os.path.join(tdir,'%s.csv'%dt[0])
            for fv in md.keys():
                bfn = os.path.join(os.path.join(g_home,'_bset'),'%s.csv'%fv)
                if not os.path.isfile(bfn):
                    continue
                bmt = g_iu.loadcsv(bfn,{2:type(1.0),3:type(1.0),4:type(1.0),5:type(1),6:type(1),7:type(1.0),8:type(1.0),9:type(1.0),10:type(1.0),11:type(1.0),12:type(1.0),13:type(1.0),14:type(1.0),15:type(1.0),16:type(1.0),17:type(1.0),18:type(1.0),19:type(1.0),20:type(1.0),21:type(1.0)})
                cnt = len(bmt)
                thv = max(cnt/1000,13)
                for cin in md[fv]:
                    code = cin[0]
                    g_iu.log(logging.INFO,'iknow tell handling code[%s] date[%s] fv[%s]....'%(code,dt[0],fv))
                    cmt = []
                    for b in bmt:
                        if b[1]>=dt[0]:
                            continue
                        d = 0.3*abs(cin[1]-b[2])+0.3*abs(cin[2]-b[3])+0.4*abs(cin[3]-b[4])
                        cmt.append((d,)+b[7:])
                    cmt.sort()
                    cmt = cmt[:thv]
                    perf = [[row[i] for row in cmt] for i in range(1,16)]
                    c1gs = self._guass(perf[0])
                    h1gs = self._guass(perf[1])
                    l1gs = self._guass(perf[2])
                    c2gs = self._guass(perf[3])
                    h2gs = self._guass(perf[4])
                    l2gs = self._guass(perf[5])
                    c3gs = self._guass(perf[6])
                    h3gs = self._guass(perf[7])
                    l3gs = self._guass(perf[8])
                    c4gs = self._guass(perf[9])
                    h4gs = self._guass(perf[10])
                    l4gs = self._guass(perf[11])
                    c5gs = self._guass(perf[12])
                    h5gs = self._guass(perf[13])
                    l5gs = self._guass(perf[14])
                    omt.append((code,dt[0],cnt)+c1gs+h1gs+l1gs+c2gs+h2gs+l2gs+c3gs+h3gs+l3gs+c4gs+h4gs+l4gs+c5gs+h5gs+l5gs)
            g_iu.dumpfile(ofn,omt)
            g_iu.importdata(ofn,'iknow_tell')
        g_iu.log(logging.INFO,'iknow tell task done....')
        self._setstation(5)

    def _pricetag(self,price,close,ev,std):
        up2 = close*(1+(ev+2*std)/100.0)
        up1 = close*(1+(ev+std)/100.0)
        md = close*(1+ev/100.0)
        dn2 = close*(1+(ev-2*std)/100.0)
        dn1 = close*(1+(ev-std)/100.0)
        if price>up2:
            return 5
        elif price>up1:
            return 4
        elif price>md:
            return 3
        elif price>dn1:
            return 2
        elif price>dn2:
            return 1
        else:
            return 0

    def _after(self):
        self._reconn()
        odir = os.path.join(g_home,'after')
        g_iu.mkdir(odir)
        start = '2010-01-01'
        ld = self._exesqlone('select date from iknow_after order by date desc limit 1',None)
        if len(ld)==1:
            start = ld[0]
        dts = self._exesqlbatch('select date from iknow_daily where date>=%s order by date',(start,))
        for i in range(1,len(dts)):
            mat = []
            cday = dts[i][0]
            yday = dts[i-1][0]
            g_iu.log(logging.INFO,'iknow after handling[%s]'%cday)
            ofn = os.path.join(odir,'%s.csv'%cday)
            sql = 'select code,18*(c1_ev/c1_std)+15*(c2_ev/c2_std)+12*(c3_ev/c3_std)+9*(c4_ev/c4_std)+6*(c5_ev/c5_std)+18*(h1_ev/h1_std)+15*(h2_ev/h2_std)+12*(h3_ev/h3_std)+9*(h4_ev/h4_std)+6*(h5_ev/h5_std)+18*(l1_ev/l1_std)+15*(l2_ev/l2_std)+12*(l3_ev/l3_std)+9*(l4_ev/l4_std)+6*(l5_ev/l5_std) from iknow_tell where date=%s and code in (select code from iknow_attr where date=%s and seq>250)'
            param = (cday,cday)
            rows = self._exesqlbatch(sql,param)
            for row in rows:
                code = row[0]
                score = row[1]
                yc = self._exesqlone('select close from iknow_data where code=%s and date=%s',(code,yday))
                yrn = self._exesqlone('select c1_ev,c1_std,h1_ev,h1_std,l1_ev,l1_std from iknow_tell where code=%s and date=%s',(code,yday))
                ps = self._exesqlone('select close,high,low from iknow_data where code=%s and date=%s',(code,cday))
                if len(yc)==0 or len(yrn)==0 or len(ps)==0:
                    continue
                ct = self._pricetag(ps[0],yc[0],yrn[0],yrn[1])
                ht = self._pricetag(ps[1],yc[0],yrn[2],yrn[3])
                lt = self._pricetag(ps[2],yc[0],yrn[4],yrn[5])
                volwy = self._exesqlone('select volwy from iknow_data where code=%s and date=%s',(code,cday))
                rank = self._exesqlone('select count(*) from iknow_data where date=%s and volwy>=%s',(cday,volwy[0]))
                mat.append((code,cday,'%0.4f'%score,rank[0],'%0.4f'%((volwy[0]/10000.0)),ct,ht,lt))
            g_iu.dumpfile(ofn,mat)
            g_iu.importdata(ofn,'iknow_after')
        self._setstation(6)
        
    def _opers(self):
        self._reconn()
        now = datetime.datetime.now()
        ofn = os.path.join(os.path.join(g_home,'tmp'),'iknow_ops_%04d%02d%02d%02d%02d%02d.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
        g_iu.log(logging.INFO,'iknow ops task start....')
        codes = self._codes()
        f = open(ofn,'w')
        for code in codes:
            ld = self._exesqlone('select date from iknow_ops where code=%s order by date desc limit 1',(code,))
            dt = self._exesqlone('select distinct date from iknow_after where code=%s order by date limit 1',(code,))
            if len(dt)==0:
                continue
            start = dt[0]
            if len(ld)!=0:
                start = ld[0]
            dts = self._exesqlbatch('select date,score from iknow_after where code=%s order by date',(code,))
            for i in range(2,len(dts)):
                if dts[i][0]<=start:
                    continue
                g_iu.log(logging.INFO,'iknow ops handling code[%s] day[%s]....'%(code,dts[i][0]))
                hlb = self._exesqlone('select hb,lb from iknow_attr where code=%s and date=%s',(code,dts[i][0]))
                op = 0 #0:wait/hold,1:buy,2:sell
                if dts[i-1][1]>dts[i-2][1] and dts[i-1][1]>dts[i][1] and hlb[0]==0 and hlb[1]==1:
                    op = 1
                elif dts[i-1][1]<dts[i-2][1] and dts[i-1][1]<dts[i][1] and hlb[0]==1 and hlb[1]==0:
                    op = 2
                yd = dts[i-1][0]
                cday = dts[i][0]
                yc = self._exesqlone('select close from iknow_data where code=%s and date=%s',(code,yd))
                tells = self._exesqlone('select h1_ev,h1_std,l1_ev,l1_std,c1_ev,c1_std from iknow_tell where code=%s and date=%s',(code,yd))
                rn = self._exesqlone('select c1_ev,c1_std,h1_ev,h1_std,l1_ev,l1_std from iknow_tell where code=%s and date=%s',(code,cday))
                ps = self._exesqlone('select high,low,close from iknow_data where code=%s and date=%s',(code,cday))
                hrn = (((ps[0]-yc[0])/yc[0])-tells[0])/tells[1]
                lrn = (((ps[1]-yc[0])/yc[0])-tells[2])/tells[3]
                crn = (((ps[2]-yc[0])/yc[0])-tells[4])/tells[5]
                ev = (rn[0]+rn[2]+rn[4])/3.0
                std = (rn[1]+rn[3]+rn[5])/3.0
                f.write('%s,%s,%d,%0.4f,%0.4f,%0.4f,%0.4f,%0.4f\n'%(code,cday,op,hrn,lrn,crn,ev,std))
        f.close()
        g_iu.importdata(ofn,'iknow_ops')
        g_iu.log(logging.INFO,'iknow ops task done....')
        self._setstation(7)

    def _upvolr(self):
        self._reconn()
        dir = os.path.join(g_home,'volr')
        g_iu.mkdir(dir)
        ld = self._exesqlone('select date from iknow_volr order by date desc limit 1',None)
        start = '2001-01-01'
        if len(ld) > 0:
            start = ld[0]
        sqls = []
        dts = self._exesqlbatch('select date from iknow_daily where date>%s order by date',(start,))
        for dt in dts:
            mat = []
            ofn = os.path.join(dir,'%s.csv'%dt[0])
            codes = self._codes()
            for code in codes:
                g_iu.log(logging.INFO,'ikdaily volr handling code[%s] day[%s]....'%(code,dt[0]))
                cnt = self._exesqlone('select count(*) from iknow_data where date=%s and code=%s',(dt[0],code))
                if cnt[0] > 0:
                    vols = self._exesqlbatch('select volwy from iknow_data where code=%s and date<=%s order by date desc limit 2',(code,dt[0]))
                else:
                    continue
                if len(vols)!=2:
                    continue
                if vols[1][0]!=0:
                    volr = '%0.4f'%(vols[0][0]/vols[1][0])
                    mat.append((code,dt[0],volr,'%0.4f'%(vols[0][0]/10000)))
            g_iu.dumpfile(ofn,mat)
            g_iu.importdata(ofn,'iknow_volr')
        g_iu.log(logging.INFO,'iknow volr task done....')
        self._setstation('8')

    def _board(self):
        self._reconn()
        bd = {}
        bds = self._exesqlbatch('select distinct boardcode from iknow_name',None)
        for b in bds:
            bd[b[0]] = []
            codes = self._exesqlbatch('select code,name from iknow_name where boardcode=%s',(b[0],))
            for code in codes:
                bd[b[0]].append((code[0],code[1]))
        ld = self._exesqlone('select date from iknow_board order by date desc limit 1',None)
        start = '2017-01-01'
        if (len(ld)>0):
            start = ld[0]
        dts = self._exesqlbatch('select distinct date from iknow_data where date>=%s order by date',(start,))
        dir = os.path.join(g_home,'board')
        g_iu.mkdir(dir)
        g_iu.log(logging.INFO,'iknow board task start....')
        for dt in dts:
            dvol = 0.0
            bvd = {}
            mat = []
            ofn = os.path.join(dir,'%s.csv'%dt[0])
            g_iu.log(logging.INFO,'iknow board handling file[%s]....'%ofn)
            for b in bd.keys():
                bvol = 0.0
                hbl = []
                lbl = []
                scrl = []
                zdlead = self._exesqlone('select code,zdf from iknow_data where date=%s and code in (select code from iknow_name where boardcode=%s) order by zdf desc limit 1',(dt[0],b))
                vollead = self._exesqlone('select code,volwy from iknow_data where date=%s and code in (select code from iknow_name where boardcode=%s) order by volwy desc limit 1',(dt[0],b))
                if len(zdlead)==0 or len(vollead)==0:
                    continue
                mts = self._exesqlbatch('select mt from iknow_attr where date=%s and code in (select code from iknow_name where boardcode=%s)',(dt[0],b))
                mtl = []
                for t in mts:
                    mtl.append(t[0])
                bt = max(set(mtl), key=mtl.count)
                for c in bd[b]:
                    vol = self._exesqlone('select volwy from iknow_data where code=%s and date=%s',(c[0],dt[0]))
                    inf = self._exesqlone('select cscr,hb,lb from iknow_attr where code=%s and date=%s',(c[0],dt[0]))
                    if len(inf)>0:
                        scrl.append(inf[0])
                        if inf[1]==1:
                            hbl.append(inf[1])
                        if inf[2]==1:
                            lbl.append(inf[2])
                    if len(vol)>0:
                        bvol = bvol + vol[0]
                        dvol = dvol + vol[0]
                if len(scrl)>0:
                    hbr = 100*(float(len(hbl))/float(len(scrl)))
                    lbr = 100*(float(len(lbl))/float(len(scrl)))
                    score = sum(scrl)/float(len(scrl))
                    bvd[b] = (bvol,hbr,lbr,score,zdlead[0],zdlead[1],vollead[0],'%0.4f'%(vollead[1]/float(10000)),bt)
            for bv in bvd.keys():
                mat.append((bv,dt[0],bvd[bv][0],'%0.2f'%(100*(bvd[bv][0]/dvol)),'%0.2f'%bvd[bv][1],'%0.2f'%bvd[bv][2],'%0.2f'%bvd[bv][3],bvd[bv][4],bvd[bv][5],bvd[bv][6],bvd[bv][7],bvd[bv][8]))
            g_iu.dumpfile(ofn,mat)
            g_iu.importdata(ofn,'iknow_board')
        g_iu.log(logging.INFO,'iknow board task done....')
        self._setstation('done')
        
    def _indexs(self):
        self._reconn()
        dir = os.path.join(g_home,'index')
        g_iu.mkdir(dir)
        ld = self._exesqlone('select date from iknow_index order by date desc limit 1',None)
        codes = g_iu.allcodes()
        macdparan1 = 12
        macdparan2 = 26
        macdparan3 = 9
        pemaf = 0.0
        pemas = 0.0
        pdea = 0
        kdj1 = 9
        kdj2 = 3
        kdj3 = 3
        lastk = 50.0
        lastd = 50.0
        for code in codes:
            data = self._exesqlbatch('select date,open,high,low,close from iknow_data where code=%s order by date',(code,))
            for row in data:
                close = float(row[4])
                emaf = 2*close/(macdparan1+1)+(macdparan1-1)*pemaf/(macdparan1+1)
                emas = 2*close/(macdparan2+1)+(macdparan2-1)*pemas/(macdparan2+1)
                diff = emaf-emas
                dea  = 2*diff/(macdparan3+1)+(macdparan3-1)*pdea/(macdparan3+1)
                bar = 2*(diff-dea)
                pemaf = emaf
                pemas = emas
                pdea = dea


    def run(self):
        g_iu.log(logging.INFO,'iknow data process[%d] start'%(os.getpid()))
        while 1:
            try:
                self._reconn()
                st = self._exesqlone('select value from iknow_conf where name=%s',('station',))
                g_iu.log(logging.INFO,'iknow run current station[%s]....'%(st[0]))
                if st[0]=='start':
                    self._upattr()
                elif st[0]=='2':
                    self._updaily()
                elif st[0]=='3':
                    self._upbaseset()
                elif st[0]=='4':
                    self._tell()
                elif st[0]=='5':
                    self._after()
                elif st[0]=='6':
                    self._opers()
                elif st[0]=='7':
                    self._upvolr()
                elif st[0]=='8':
                    self._board()
            except Exception,e:
                g_iu.log(logging.INFO,'iknow data process exception[%s]....'%e)
            time.sleep(8)

    def backupbset(self):
        g_iu.log(logging.INFO,'iknow backupbset process[%d] start....'%(os.getpid()))
        while 1:
            try:
                dir = os.path.join(g_home,'bset')
                now = datetime.datetime.now()
                if now.isoweekday()==6 and now.hour==0 and now.minute<1:
                    self._reconn()
                    tdir = os.path.join(dir,'bset_%04d%02d%02d%02d%02d%02d'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
                    g_iu.mkdir(tdir)
                    g_iu.log(logging.INFO,'iknow backupbset task[%s] start....'%tdir)
                    codes = self._codes()
                    for code in codes:
                        sql = 'select fv,date,oscr,cscr,zdf,hb,lb,zdf_c1,zdf_h1,zdf_l1,zdf_c2,zdf_h2,zdf_l2,zdf_c3,zdf_h3,zdf_l3,zdf_c4,zdf_h4,zdf_l4,zdf_c5,zdf_h5,zdf_l5 from iknow_bset where code=%s'
                        param = (code,)
                        rows = self._exesqlbatch(sql,param)
                        for row in rows:
                            ofn = os.path.join(tdir,'%s.csv'%row[0])
                            f = open(ofn,'a')
                            line = '%s'%code
                            for it in row[1:]:
                                line = line + ',%s'%it
                            f.write('%s\n'%line)
                            f.close()
                    lnk = os.path.join(g_home,'_bset')
                    lnkbk = os.path.join(g_home,'_bset_bk')
                    if os.path.islink(lnkbk):
                        tk = os.readlink(lnkbk)
                        g_iu.execmd('rm -fr %s'%tk)
                    if os.path.islink(lnk):
                        tk = os.readlink(lnk)
                        g_iu.link(g_home,'_bset_bk',tk)
                    g_iu.link(g_home,'_bset',tdir)
                    g_iu.log(logging.INFO,'iknow backupbset task[%s] done....'%tdir)
            except Exception,e:
                g_iu.log(logging.INFO,'iknow backupbset exception[%s]....'%e)
            time.sleep(20)
        g_iu.log(logging.INFO,'iknow backupbset procesws exit....')

    def _updl(self):
        g_iu.log(logging.INFO,'iknow updl task start....')
        g_iu.execmd('py2 %s'%os.path.join(os.path.join(g_home,'bin'),'ikdl.py'))
        ofn = os.path.join(os.path.join(g_home,'etc'),'code_dl.csv')
        codes = self._codes()
        mat = []
        for code in codes:
            ld = self._exesqlone('select date from iknow_data where code=%s order by date desc limit 1',(code,))
            if len(ld)>0:
                mat.append((code,ld[0]))
        g_iu.dumpfile(ofn,mat)
        self._reconn()
        st = self._exesqlone('select value from iknow_conf where name=%s',('station',))
        if st[0]=='done':
            self._setstation('start')
        g_iu.log(logging.INFO,'iknow updl task done....')

    def dl(self):
        g_iu.log(logging.INFO,'iknow download process[%d] start....'%(os.getpid()))
        self._reconn()
        self._updl()
        while 1:
            try:
                self._reconn()
                st = self._exesqlone('select value from iknow_conf where name=%s',('station',))
                now = datetime.datetime.now()
                wd = now.isoweekday()
                g_iu.log(logging.INFO,'iknow dl weekday[%d] hour[%d] status[%s]'%(wd,now.hour,st[0]))
                if wd != 6 and wd != 7 and now.hour>=17 and st[0]=='done':
                    self._updl()
            except Exception,e:
                g_iu.log(logging.INFO,'iknow backupbset exception[%s]....'%e)
            time.sleep(5)
        g_iu.log(logging.INFO,'iknow download procesws exit....')

if __name__ == "__main__":
    ik = iknow()
    pid = os.fork()
    if pid == 0:
        ik.run()
    else:
        cpid = os.fork()
        if cpid == 0:
            ik.backupbset()
        else:
            ik.dl()
        
        
        
        
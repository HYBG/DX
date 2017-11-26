#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import MySQLdb
from optparse import OptionParser
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil

g_iu = ikutil()


class ikbill:
    def __init__(self):
        self._conf = g_iu.loadcsv(os.path.join(os.path.join(g_home,'etc'),'code.csv'),{},0)
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()
        self._dfund = {'feat':self.feat,'tell':self.tell,'oper':self.oper,'doper':self.doper,'board':self.board,'volr':self.volr}
    
    def __del__(self):
        self._cursor.close()
        self._conn.close()
    
    def _codes(self):
        codes = self._conf.keys()
        codes.sort()
        return codes
        
    def _resetdb(self):
        self._cursor.close()
        self._conn.close()
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()
        
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
            for i in range(len(lis)):
                if not lis[i].isdigit():
                    lis[i]=''
            return int(''.join(lis))
            
    def _dl_upfrom163(self,code,start):
        td = datetime.datetime.today()
        ey = td.year
        em = td.month
        es = self._dl_season(em)
        ymd=start.split('-')
        sy = int(ymd[0])
        ss = self._dl_season(int(ymd[1]))
        s = [sy,ss]
        e = [ey,es]
        mat = []
        while s<=e:
            url = 'http://quotes.money.163.com/trade/lsjysj_%s.html?year=%s&season=%s'%(code,s[0],s[1])
            g_iu.log(logging.INFO,'ikbill ready to open url[%s]'%url)
            html=urllib2.urlopen(url).read()
            #soup = BeautifulSoup(html, 'html.parser')
            soup = BeautifulSoup(html, 'lxml')
            trs = soup.find_all('tr')
            for tr in trs:
                tds=tr.find_all('td')
                if len(tds)==11:
                    dt = tds[0].text.strip()
                    if re.match('\d{4}-\d{2}-\d{2}', dt) and dt>start:
                        open = float(tds[1].text.strip())
                        high = float(tds[2].text.strip())
                        low = float(tds[3].text.strip())
                        close = float(tds[4].text.strip())
                        we = float(tds[5].text.strip())
                        ww = float(tds[6].text.strip())
                        vols = self._dl_drawdigit(tds[7].text.strip())
                        vole = self._dl_drawdigit(tds[8].text.strip())
                        zf = float(tds[9].text.strip())
                        hs = float(tds[10].text.strip())
                        v = (code,dt,open,high,low,close,we,ww,vols,vole,zf,hs)
                        mat.append(v)
            g_iu.log(logging.INFO,'ikbill fetch from url[%s] records[%d]'%(url,len(mat)))
            if s[1]!=4:
                s[1]=s[1]+1
            else:
                s[0]=s[0]+1
                s[1]=1
        return mat
        
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
        
    def _updateone(self,sql,param):
        n = 0
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        if n==1:
            self._conn.commit()
            return True
        return False
        
    def update(self):
        try:
            clis = self._codes()
            now = datetime.datetime.now()
            allofn = os.path.join(os.path.join(g_home,'tmp'),'ikbill_data_%04d%02d%02d%02d%02d%02d_update.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
            for code in clis:
                try:
                    start = '2016-01-01'
                    ld = self._exesqlone('select date from ikbill_data where code=%s order by date desc limit 1',(code,))
                    if len(ld)>0:
                        start = ld[0]
                    mat = self._dl_upfrom163(code,start)
                    if len(mat)==0:
                        continue
                    g_iu.appendmat(allofn,mat)
                except Exception,e:
                    g_iu.log(logging.INFO,'code[%s],date[%04d-%02d-%02d] update failed[%s]'%(code,now.year,now.month,now.day,e))
            if os.path.isfile(allofn):
                g_iu.importdata(allofn,'ikbill_data')
            g_iu.log(logging.INFO,'import ikbill handled codes date[%04d-%02d-%02d]'%(now.year,now.month,now.day))
            g_iu.execmd('rm -fr %s'%allofn)
        except Exception,e:
            g_iu.log(logging.INFO,'import ikbill exception[%s]....'%e)
            
    def upattr(self):
        codes = self._codes()
        volpara = 5
        macdparan1 = 12
        macdparan2 = 26
        macdparan3 = 9
        macdmaxp = 10
        now = datetime.datetime.now()
        ofn = os.path.join(os.path.join(g_home,'tmp'),'ikbill_attr_%04d%02d%02d%02d%02d%02d.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
        f = open(ofn,'w')
        g_iu.log(logging.INFO,'ikbill upattr task[%s] start....'%ofn)
        for code in codes:
            g_iu.log(logging.INFO,'ikbill upattr handling code[%s]....'%code)
            ldi = self._exesqlone('select date,volev,emaf,emas,dea,bar,mt,mp,seq from ikbill_attr where code=%s order by date desc limit 1',(code,))
            pemaf = 0.0
            pemas = 0.0
            pvol = 0.0
            pdea = 0
            pbar = 0
            pmt = 1
            pmp = 1
            pseq = 0
            sql = 'select date,open,high,low,close,volh,zdf from ikbill_data where code=%s order by date'
            param = (code,)
            if len(ldi)>0:
                sql = 'select date,open,high,low,close,volh,zdf from ikbill_data where code=%s and date>=%s order by date'
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
        g_iu.importdata(ofn,'ikbill_attr')
        g_iu.execmd('rm -fr %s'%ofn)
        g_iu.log(logging.INFO,'ikbill upattr task[%s] done....'%ofn)
        
    def upbaseset(self):
        self._resetdb()
        codes = self._codes()
        now = datetime.datetime.now()
        ofn = os.path.join(os.path.join(g_home,'tmp'),'ikbill_bset_%04d%02d%02d%02d%02d%02d.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
        f = open(ofn,'w')
        g_iu.log(logging.INFO,'ikbill upbaseset task[%s] start....'%ofn)
        for code in codes:
            ld = self._exesqlone('select date from ikbill_bset where code=%s order by date desc limit 1',(code,))
            start = '2001-01-01'
            if len(ld)>0:
                start = ld[0]
            g_iu.log(logging.INFO,'ikbill upbaseset handling code[%s] from[%s]....'%(code,start))
            rows = self._exesqlbatch('select date,high,low,close from ikbill_data where code=%s and date>%s',(code,start))
            if len(rows) > 5:
                for i in range(len(rows)-5):
                    at = self._exesqlone('select mt,mp,vr,oscr,cscr,zdf,hb,lb from ikbill_attr where code=%s and date=%s and seq>120',(code,rows[i][0]))
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
        g_iu.importdata(ofn,'ikbill_bset')
        g_iu.execmd('rm -fr %s'%ofn)
        g_iu.log(logging.INFO,'ikbill upbaseset task[%s] done....'%ofn)
        
    def backupbset(self):
        self._resetdb()
        dir = os.path.join(g_home,'bset')
        now = datetime.datetime.now()
        tdir = os.path.join(dir,'bset_%04d%02d%02d%02d%02d%02d'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
        g_iu.mkdir(tdir)
        g_iu.log(logging.INFO,'ikbill backupbset task[%s] start....'%tdir)
        codes = self._codes()
        for code in codes:
            g_iu.log(logging.INFO,'ikbill backupbset handling code[%s]....'%code)
            sql = 'select fv,date,oscr,cscr,zdf,hb,lb,zdf_c1,zdf_h1,zdf_l1,zdf_c2,zdf_h2,zdf_l2,zdf_c3,zdf_h3,zdf_l3,zdf_c4,zdf_h4,zdf_l4,zdf_c5,zdf_h5,zdf_l5 from ikbill_bset where code=%s'
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
        g_iu.log(logging.INFO,'ikbill backupbset task[%s] done....'%tdir)

    def feat(self,day):
        self._resetdb()
        dir = os.path.join(g_home,'feat')
        g_iu.mkdir(dir)
        g_iu.log(logging.INFO,'ikbill feat task[%s] start....'%day)
        dts = self._exesqlbatch('select date from ikbill_daily where date>=%s order by date',(day,))
        for dt in dts:
            ofn = os.path.join(dir,'%s.csv'%dt[0])
            if not os.path.isfile(ofn):
                rows = self._exesqlbatch('select code,mt,mp,vr,oscr,cscr,zdf,hb,lb from ikbill_attr where date=%s',(dt[0],))
                g_iu.log(logging.INFO,'ikbill feat handling date[%s] %d....'%(dt[0],len(rows)))
                mat = []
                for row in rows:
                    fv = '%d%02d%d'%(int(row[1]),int(row[2]),int(row[3]))
                    mat.append((row[0],fv,)+row[4:])
                g_iu.dumpfile(ofn,mat)
            else:
                g_iu.log(logging.INFO,'ikbill feat output file[%s] has been there....'%ofn)
        g_iu.log(logging.INFO,'ikbill feat task[%s] done....'%day)

    def updaily(self):
        self._resetdb()
        g_iu.log(logging.INFO,'ikbill updaily task start....')
        cursor = self._conn.cursor()
        ld = self._exesqlone('select date from ikbill_daily order by date desc limit 1',None)
        start = '2001-01-01'
        if len(ld) > 0:
            start = ld[0]
        dts = self._exesqlbatch('select distinct date from ikbill_attr where date>%s order by date',(start,))
        for dt in dts:
            inf = self._exesqlone('select count(*),avg(oscr),avg(cscr) from ikbill_attr where date=%s',(dt[0],))
            if len(inf) > 0:
                hbc = self._exesqlone('select count(*) from ikbill_attr where date=%s and hb=1',(dt[0],))
                hb = 0.0
                if len(hbc) > 0:
                    hb = float(hbc[0])
                lbc = self._exesqlone('select count(*) from ikbill_attr where date=%s and lb=1',(dt[0],))
                lb = 0.0
                if len(lbc) > 0:
                    lb = float(lbc[0])
                hbr = 100*(hb/float(inf[0]))
                lbr = 100*(lb/float(inf[0]))
                sql = 'INSERT INTO ikbill_daily(date,count,hbr,lbr,oscore,cscore) VALUES(%s,%s,%s,%s,%s,%s)'
                param = (dt[0],inf[0],'%0.2f'%hbr,'%0.2f'%lbr,'%0.2f'%inf[1],'%0.2f'%inf[2])
                if self._updateone(sql,param):
                    g_iu.log(logging.INFO,'ikbill updaily insert date[%s] done....'%dt[0])
                else:
                    g_iu.log(logging.ERR,'ikbill updaily insert date[%s] error....'%dt[0])
        dir = os.path.join(g_home,'daily')
        g_iu.mkdir(dir)
        now = datetime.datetime.now()
        ofn = os.path.join(dir,'daily_%04d%02d%02d%02d%02d%02d.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
        all = self._exesqlbatch('select date,hbr,lbr,oscore,cscore from ikbill_daily order by date',None)
        if len(all)>0:
            g_iu.dumpfile(ofn,all)
            g_iu.link(g_home,'_daily.csv',ofn)
        g_iu.log(logging.INFO,'ikbill updaily task done....')
        
    def _guass(self,lis):
        all = sum(lis)
        ev = all/float(len(lis))
        alls = 0
        for it in lis:
            alls = alls + (it-ev)**2
        std = (alls/float(len(lis)))**0.5
        return (ev,std)
        
    def tell(self,day):
        dir = os.path.join(g_home,'tell')
        g_iu.mkdir(dir)
        ofn = os.path.join(dir,'%s.csv'%day)
        ifn = os.path.join(os.path.join(g_home,'feat'),'%s.csv'%day)
        g_iu.log(logging.INFO,'ikbill tell task[%s] start....'%day)
        if not os.path.isfile(ofn):
            omt = []
            mat = g_iu.loadcsv(ifn,{2:type(1.0),3:type(1.0),4:type(1.0),5:type(1),6:type(1)})
            md = {}
            for r in mat:
                if md.has_key(r[1]):
                    md[r[1]].append((r[0],)+r[2:])
                else:
                    md[r[1]] = [(r[0],)+r[2:]]
            for fv in md.keys():
                bfn = os.path.join(os.path.join(g_home,'_bset'),'%s.csv'%fv)
                if not os.path.isfile(bfn):
                    continue
                bmt = g_iu.loadcsv(bfn,{2:type(1.0),3:type(1.0),4:type(1.0),5:type(1),6:type(1),7:type(1.0),8:type(1.0),9:type(1.0),10:type(1.0),11:type(1.0),12:type(1.0),13:type(1.0),14:type(1.0),15:type(1.0),16:type(1.0),17:type(1.0),18:type(1.0),19:type(1.0),20:type(1.0),21:type(1.0)})
                cnt = len(bmt)
                thv = max(cnt/1000,13)
                for cin in md[fv]:
                    code = cin[0]
                    g_iu.log(logging.INFO,'ikbill tell handling code[%s] date[%s] fv[%s]....'%(code,day,fv))
                    cmt = []
                    for b in bmt:
                        if b[1]>=day:
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
                    omt.append((code,day,cnt)+c1gs+h1gs+l1gs+c2gs+h2gs+l2gs+c3gs+h3gs+l3gs+c4gs+h4gs+l4gs+c5gs+h5gs+l5gs)
            g_iu.dumpfile(ofn,omt)
            g_iu.importdata(ofn,'ikbill_tell')
        g_iu.log(logging.INFO,'ikbill tell task[%s] done....'%day)
    
    def updl(self):
        g_iu.log(logging.INFO,'ikbill updl task start....')
        ofn = os.path.join(os.path.join(g_home,'etc'),'code_dl.csv')
        codes = self._codes()
        mat = []
        for code in codes:
            ld = self._exesqlone('select date from ikbill_data where code=%s order by date desc limit 1',(code,))
            if len(ld)>0:
                mat.append((code,ld[0]))
        g_iu.dumpfile(ofn,mat)
        g_iu.log(logging.INFO,'ikbill updl task done....')
        
    def board(self,day):
        self._resetdb()
        bd = {}
        bds = self._exesqlbatch('select distinct bdcode from ikbill_name',None)
        for b in bds:
            bd[b[0]] = []
            codes = self._exesqlbatch('select code,name from ikbill_name where bdcode=%s',(b[0],))
            for code in codes:
                bd[b[0]].append((code[0],code[1]))
        g_iu.log(logging.INFO,'ikbill board task[%s] start....'%day)
        dts = self._exesqlbatch('select distinct date from ikbill_data where date>=%s order by date',(day,))
        dir = os.path.join(g_home,'board')
        g_iu.mkdir(dir)
        for dt in dts:
            dvol = 0.0
            bvd = {}
            mat = []
            ofn = os.path.join(dir,'%s.csv'%dt[0])
            g_iu.log(logging.INFO,'ikbill board handling file[%s]....'%ofn)
            if os.path.isfile(ofn):
                continue
            for b in bd.keys():
                bvol = 0.0
                hbl = []
                lbl = []
                scrl = []
                zdlead = self._exesqlone('select code,zdf from ikbill_data where date=%s and code in (select code from ikbill_name where bdcode=%s) order by zdf desc limit 1',(dt[0],b))
                vollead = self._exesqlone('select code,volwy from ikbill_data where date=%s and code in (select code from ikbill_name where bdcode=%s) order by volwy desc limit 1',(dt[0],b))
                if len(zdlead)==0 or len(vollead)==0:
                    continue
                mts = self._exesqlbatch('select mt from ikbill_attr where date=%s and code in (select code from ikbill_name where bdcode=%s)',(dt[0],b))
                mtl = []
                for t in mts:
                    mtl.append(t[0])
                bt = max(set(mtl), key=mtl.count)
                for c in bd[b]:
                    vol = self._exesqlone('select volwy from ikbill_data where code=%s and date=%s',(c[0],dt[0]))
                    inf = self._exesqlone('select cscr,hb,lb from ikbill_attr where code=%s and date=%s',(c[0],dt[0]))
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
            g_iu.importdata(ofn,'ikbill_board')
        g_iu.log(logging.INFO,'ikbill board task[%s] done....'%day)

    def score(self):
        self._resetdb()
        dir = os.path.join(g_home,'score')
        g_iu.mkdir(dir)
        temps = self._exesqlbatch('select id,c11*c12,c21*c22,c31*c32,c41*c42,c51*c52,h11*h12,h21*h22,h31*h32,h41*h42,h51*h52,l11*l12,l21*l22,l31*l32,l41*l42,l51*l52 from ikbill_weitemp',None)
        for ts in temps:
            odir = os.path.join(dir,'%s'%ts[0])
            g_iu.mkdir(odir)
            start = '2010-01-01'
            ld = self._exesqlone('select date from ikbill_score where tid=%s order by date desc limit 1',(ts[0],))
            if len(ld)==1:
                start = ld[0]
            dts = self._exesqlbatch('select date from ikbill_daily where date>%s order by date',(start,))
            for dt in dts:
                g_iu.log(logging.INFO,'ikbill score handling[%s]'%dt[0])
                ofn = os.path.join(odir,'%s.csv'%dt[0])
                if os.path.isfile(ofn):
                    g_iu.log(logging.INFO,'ikbill score file[%s] has been there....'%ofn)
                    continue
                sql = 'select code,c1_ev,c1_std,c2_ev,c2_std,c3_ev,c3_std,c4_ev,c4_std,c5_ev,c5_std,h1_ev,h1_std,h2_ev,h2_std,h3_ev,h3_std,h4_ev,h4_std,h5_ev,h5_std,l1_ev,l1_std,l2_ev,l2_std,l3_ev,l3_std,l4_ev,l4_std,l5_ev,l5_std from ikbill_tell where date=%s and code in (select code from ikbill_attr where date=%s and seq>250)'
                param = (dt[0],dt[0])
                rows = self._exesqlbatch(sql,param)
                mat = []
                for row in rows:
                    code = row[0]
                    score = 0
                    for i in range(15):
                        score = score + ts[i+1]*(row[i*2+1]/row[i*2+2])
                    mat.append((ts[0],code,dt[0],'%0.4f'%score))
                g_iu.dumpfile(ofn,mat)
                g_iu.importdata(ofn,'ikbill_score')

    def oper(self,day):
        dir = os.path.join(g_home,'oper')
        g_iu.mkdir(dir)
        ofn = os.path.join(dir,'%s.csv'%day)
        g_iu.log(logging.INFO,'ikbill oper task[%s] start....'%day)
        if not os.path.isfile(ofn):
            codes = self._codes()
            mat = []
            tids = self._exesqlbatch('select id from ikbill_weitemp',None)
            for code in codes:
                g_iu.log(logging.INFO,'ikbill oper handling code[%s] day[%s]'%(code,day))
                for tid in tids:
                    rows = self._exesqlbatch('select score from ikbill_score where tid=%s and code=%s and date<=%s order by date desc limit 3',(tid[0],code,day))
                    if len(rows)==3:
                        hlb = self._exesqlone('select hb,lb from ikbill_attr where code=%s and date=%s',(code,day))
                        if len(hlb) == 2:
                            ops = 0
                            if hlb[0] == 1:
                                if rows[0][0]>rows[1][0] and rows[2][0]>rows[1][0]:
                                    if rows[1][0]<=0:
                                        ops = 2
                            if hlb[1] == 1:
                                if rows[0][0]<rows[1][0] and rows[2][0]<rows[1][0]:
                                    if rows[1][0]>=0:
                                        ops = 1
                            mat.append((tid[0],code,day,ops))
                        else:
                            g_iu.log(logging.INFO,'ikbill oper no need handled code[%s] day[%s]'%(code,day))
            if len(mat)>0:
                g_iu.dumpfile(ofn,mat)
                g_iu.importdata(ofn,'ikbill_opers')
            else:
                g_iu.log(logging.INFO,'ikbill oper handling code[%s] day[%s] no data'%(code,day))
        else:
            g_iu.log(logging.INFO,'ikbill oper file[%s] has been handled'%ofn)
        g_iu.log(logging.INFO,'ikbill oper task[%s] done....'%day)

    def doper(self,day):
        dir = os.path.join(g_home,'doper')
        g_iu.mkdir(dir)
        ofn = os.path.join(dir,'%s.csv'%day)
        g_iu.log(logging.INFO,'ikbill doper task[%s] start....'%day)
        if not os.path.isfile(ofn):
            thv = 7
            mat = []
            vold = {}
            vs = self._exesqlbatch('select code,volwy from ikbill_data where date=%s order by volwy desc',(day,))
            for i in range(len(vs)):
                vold[vs[i][0]] = (i+1,'%0.4f'%(vs[i][1]/float(10000)))
            codes = self._codes()
            for code in codes:
                g_iu.log(logging.INFO,'ikbill doper handling code[%s] day[%s]....'%(code,day))
                opv = self._exesqlone('select sum(ops) from ikbill_opers where code=%s and date=%s',(code,day))
                if len(opv)==0:
                    continue
                if not vold.has_key(code):
                    continue
                if opv[0]>=thv and opv[0]<2*thv:
                    mat.append((code,day,1,thv,vold[code][0],vold[code][1]))
                elif opv[0]>=2*thv:
                    mat.append((code,day,2,thv,vold[code][0],vold[code][1]))
                else:
                    mat.append((code,day,0,thv,vold[code][0],vold[code][1]))
            g_iu.dumpfile(ofn,mat)
            g_iu.importdata(ofn,'ikbill_op')
        else:
            g_iu.log(logging.INFO,'ikbill doper file[%s] has been handled'%ofn)
        g_iu.log(logging.INFO,'ikbill doper task[%s] done....'%day)
        
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
        
    def score_x(self):
        self._resetdb()
        now = datetime.datetime.now()
        ofn = os.path.join(os.path.join(g_home,'tmp'),'ikbill_score_x_%04d%02d%02d%02d%02d%02d.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
        g_iu.log(logging.INFO,'ikbill score_x task start....')
        codes = self._codes()
        f = open(ofn,'w')
        for code in codes:
            ld = self._exesqlone('select date from ikbill_after where code=%s order by date desc limit 1',(code,))
            dt = self._exesqlone('select distinct date from ikbill_score where code=%s order by date limit 1',(code,))
            if len(dt)==0:
                continue
            start = dt[0]
            if len(ld)!=0:
                start = ld[0]
            dts = self._exesqlbatch('select distinct date from ikbill_score where code=%s and date>=%s order by date',(code,start))
            for i in range(1,len(dts)):
                g_iu.log(logging.INFO,'ikbill score_x handling code[%s] day[%s]....'%(code,dts[i][0]))
                yd = dts[i-1][0]
                yc = self._exesqlone('select close from ikbill_data where code=%s and date=%s',(code,yd))
                yrn = self._exesqlone('select c1_ev,c1_std,h1_ev,h1_std,l1_ev,l1_std from ikbill_tell where code=%s and date=%s',(code,yd))
                rn = self._exesqlone('select c1_ev,c1_std,h1_ev,h1_std,l1_ev,l1_std from ikbill_tell where code=%s and date=%s',(code,dts[i][0]))
                ps = self._exesqlone('select close,high,low from ikbill_data where code=%s and date=%s',(code,dts[i][0]))
                ct = self._pricetag(ps[0],yc[0],yrn[0],yrn[1])
                ht = self._pricetag(ps[1],yc[0],yrn[2],yrn[3])
                lt = self._pricetag(ps[2],yc[0],yrn[4],yrn[5])
                scr = self._exesqlone('select avg(score) from ikbill_score where code=%s and date=%s order by date',(code,dts[i][0]))
                score = scr[0]
                ev = (rn[0]+rn[2]+rn[4])/3.0
                std = (rn[1]+rn[3]+rn[5])/3.0
                volwy = self._exesqlone('select volwy from ikbill_data where code=%s and date=%s',(code,dts[i][0]))
                rank = self._exesqlone('select count(*) from ikbill_data where date=%s and volwy>=%s',(dts[i][0],volwy[0]))
                f.write('%s,%s,%0.4f,%0.4f,%0.4f,%d,%0.4f,%d,%d,%d\n'%(code,dts[i][0],score,ev,std,rank[0],(volwy[0]/10000.0),ct,ht,lt))
        f.close()
        g_iu.importdata(ofn,'ikbill_after')
        g_iu.log(logging.INFO,'ikbill score_x task done....')
        
    def ops(self):
        self._resetdb()
        now = datetime.datetime.now()
        ofn = os.path.join(os.path.join(g_home,'tmp'),'ikbill_ops_%04d%02d%02d%02d%02d%02d.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
        g_iu.log(logging.INFO,'ikbill ops task start....')
        codes = self._codes()
        f = open(ofn,'w')
        for code in codes:
            ld = self._exesqlone('select date from ikbill_ops where code=%s order by date desc limit 1',(code,))
            dt = self._exesqlone('select distinct date from ikbill_after where code=%s order by date limit 1',(code,))
            if len(dt)==0:
                continue
            start = dt[0]
            if len(ld)!=0:
                start = ld[0]
            dts = self._exesqlbatch('select date,score from ikbill_after where code=%s order by date',(code,))
            for i in range(2,len(dts)):
                if dts[i][0]<=start:
                    continue
                g_iu.log(logging.INFO,'ikbill ops handling code[%s] day[%s]....'%(code,dts[i][0]))
                hlb = self._exesqlone('select hb,lb from ikbill_attr where code=%s and date=%s',(code,dts[i][0]))
                op = 0 #0:wait/hold,1:buy,2:sell
                if dts[i-1][1]>dts[i-2][1] and dts[i-1][1]>dts[i][1] and hlb[0]==0 and hlb[1]==1:
                    op = 1
                elif dts[i-1][1]<dts[i-2][1] and dts[i-1][1]<dts[i][1] and hlb[0]==1 and hlb[1]==0:
                    op = 2
                yd = dts[i-1][0]
                yc = self._exesqlone('select close from ikbill_data where code=%s and date=%s',(code,yd))
                tells = self._exesqlone('select h1_ev,h1_std,l1_ev,l1_std,c1_ev,c1_std from ikbill_tell where code=%s and date=%s',(code,yd))
                ps = self._exesqlone('select high,low,close from ikbill_data where code=%s and date=%s',(code,dts[i][0]))
                hrn = (((ps[0]-yc[0])/yc[0])-tells[0])/tells[1]
                lrn = (((ps[1]-yc[0])/yc[0])-tells[2])/tells[3]
                crn = (((ps[2]-yc[0])/yc[0])-tells[4])/tells[5]
                f.write('%s,%s,%d,%0.4f,%0.4f,%0.4f\n'%(code,dts[i][0],op,hrn,lrn,crn))
        f.close()
        g_iu.importdata(ofn,'ikbill_ops')
        g_iu.log(logging.INFO,'ikbill ops task done....')

    def volr(self,day):
        self._resetdb()
        dir = os.path.join(g_home,'volr')
        g_iu.mkdir(dir)
        ofn = os.path.join(dir,'%s.csv'%day)
        g_iu.log(logging.INFO,'ikbill volr task[%s] start....'%day)
        if not os.path.isfile(ofn):
            mat = []
            codes = self._codes()
            for code in codes:
                g_iu.log(logging.INFO,'ikbill volr handling code[%s] day[%s]....'%(code,day))
                cnt = self._exesqlone('select count(*) from ikbill_data where date=%s and code=%s',(day,code))
                if cnt[0] > 0:
                    vols = self._exesqlbatch('select volwy from ikbill_data where code=%s and date<=%s order by date desc limit 2',(code,day))
                else:
                    continue
                if len(vols)!=2:
                    continue
                if vols[1][0]!=0:
                    volr = '%0.4f'%(vols[0][0]/vols[1][0])
                    mat.append((code,day,volr))
            g_iu.dumpfile(ofn,mat)
            g_iu.importdata(ofn,'ikbill_volr')
        else:
            g_iu.log(logging.INFO,'ikbill volr file[%s] has been handled'%ofn)
        g_iu.log(logging.INFO,'ikbill volr task[%s] done....'%day)
        
    def afterup(self,day):
        g_iu.log(logging.INFO,'ikbill afterup task[%s] start....'%day)
        self.updl()
        self.upattr()
        self.hard_l()
        self.hard_h()
        self.updaily()
        self.upbaseset()
        self.backupbset()
        self.volr(day)
        self.feat(day)
        self.board(day)
        self.tell(day)
        self.score()
        self.score_x()
        self.ops()
        g_iu.execmd('python %s -d %s'%(os.path.join(os.path.join(g_home,'bin'),'ikbs.py'),day))
        g_iu.log(logging.INFO,'ikbill afterup task[%s] done....'%day)
            
    def fill(self,start,sfun):
        self._resetdb()
        dts = self._exesqlbatch('select date from ikbill_daily where date>%s order by date',(start,))
        for dt in dts:
            if self._dfund.has_key(sfun):
                self._dfund[sfun](dt[0])

    def hard_l(self):
        self._resetdb()
        codes = self._codes()
        lmat = []
        dir = os.path.join(g_home,'hl')
        g_iu.mkdir(dir)
        now = datetime.datetime.now()
        lfn = os.path.join(dir,'low_%04d%02d%02d%02d%02d%02d.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
        for code in codes:
            g_iu.log(logging.INFO,'ikbill hard_l handling code[%s]....'%code)
            ld = self._exesqlone('select date from ikbill_low where code=%s order by date desc limit 1',(code,))
            if len(ld)==1:
                startl = ld[0]
            data = self._exesqlbatch('select low,date from ikbill_data where code=%s and date>=%s order by date',(code,startl))
            for i in range(1,len(data)-1):
                if data[i][0]<=data[i-1][0] and data[i][0]<=data[i+1][0]:
                    if i > 1:
                        lmat.append((code,data[i][1],data[i-1][1],data[i-2][1]))
        g_iu.dumpfile(lfn,lmat)
        g_iu.importdata(lfn,'ikbill_low')

    def hard_h(self):
        self._resetdb()
        codes = self._codes()
        hmat = []
        dir = os.path.join(g_home,'hl')
        g_iu.mkdir(dir)
        now = datetime.datetime.now()
        hfn = os.path.join(dir,'high_%04d%02d%02d%02d%02d%02d.csv'%(now.year,now.month,now.day,now.hour,now.minute,now.second))
        for code in codes:
            g_iu.log(logging.INFO,'ikbill hard_h handling code[%s]....'%code)
            ld = self._exesqlone('select date from ikbill_high where code=%s order by date desc limit 1',(code,))
            starth = '2009-12-31'
            if len(ld)==1:
                starth = ld[0]
            data = self._exesqlbatch('select high,date from ikbill_data where code=%s and date>=%s order by date',(code,starth))
            for i in range(1,len(data)-1):
                if data[i][0]>=data[i-1][0] and data[i][0]>=data[i+1][0]:
                    if i > 1:
                        hmat.append((code,data[i][1],data[i-1][1],data[i-2][1]))
        g_iu.dumpfile(hfn,hmat)
        g_iu.importdata(hfn,'ikbill_high')
        
    def frame(self):
        self._cursor.execute('TRUNCATE ikbill_frame')
        self._conn.commit()
        codes = self._codes()
        mat = []
        for code in codes:
            g_iu.log(logging.INFO,'ikbill frame handling code[%s]....'%code)
            lows = self._exesqlbatch('select date from ikbill_low where code=%s',(code,))
            highs = self._exesqlbatch('select date from ikbill_high where code=%s',(code,))
            seq = []
            for l in lows:
                seq.append((l[0],1))
            for h in highs:
                seq.append((h[0],2))
            seq.sort()
            if len(seq)==0:
                continue
            hlp = self._exesqlone('select high,low from ikbill_data where code=%s and date=%s',(code,seq[0][0]))
            fm = 1
            sdate = seq[0][0]
            sp = hlp[1]
            if seq[0][1]==2:
                fm = 2
                sp = hlp[0]
            tmp = None
            ep = 0
            edate = None
            for i in range(1,len(seq)):
                hlp = self._exesqlone('select high,low from ikbill_data where code=%s and date=%s',(code,seq[i][0]))
                if seq[i][1] == 1: #low
                    if fm == 1: #up
                        if tmp:
                            if hlp[1]<tmp[0]:
                                ep = tmp[0]
                                edate = tmp[1]
                                leng = self._exesqlone('select count(*) from ikbill_data where code=%s and date>%s and date<%s',(code,sdate,edate))
                                v = (code,sdate,sp,edate,ep,fm,leng[0])
                                mat.append(v)
                                g_iu.log(logging.INFO,'ikbill frame handling code[%s] up trend[%s]....'%(code,str(v)))
                                sp = ep
                                sdate = edate
                                tmp = (hlp[1],seq[i][0])
                                fm = 2
                        else:
                            if hlp[1]<sp:
                                sp = hlp[1]
                                sdate = seq[i][0]
                    else: #down
                        if tmp:
                            if hlp[1]<=tmp[0]:
                                tmp = (hlp[1],seq[i][0])
                        else:
                            if hlp[1]<sp:
                                tmp = (hlp[1],seq[i][0])
                else: #high
                    if fm == 1: #up
                        if tmp:
                            if hlp[0]>=tmp[0]:
                                tmp = (hlp[0],seq[i][0])
                        else:
                            if hlp[0]>sp:
                                tmp = (hlp[0],seq[i][0])
                    else:# down
                        if tmp:
                            if hlp[0]>tmp[0]:
                                ep = tmp[0]
                                edate = tmp[1]
                                leng = self._exesqlone('select count(*) from ikbill_data where code=%s and date>%s and date<%s',(code,sdate,edate))
                                v = (code,sdate,sp,edate,ep,fm,leng[0])
                                mat.append(v)
                                g_iu.log(logging.INFO,'ikbill frame handling code[%s] up trend[%s]....'%(code,str(v)))
                                sp = ep
                                sdate = edate
                                tmp = (hlp[0],seq[i][0])
                                fm = 1
                        else:
                            if hlp[0]>sp:
                                tmp = (hlp[0],seq[i][0])
        ofn = os.path.join(os.path.join(g_home,'tmp'),'frame.csv')
        g_iu.dumpfile(ofn,mat)
        g_iu.importdata(ofn,'ikbill_frame')
                            

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-d', '--day', action='store', dest='day',default=None, help='day')
    parser.add_option('-s', '--score', action='store_true', dest='score',default=False, help='score')
    parser.add_option('-S', '--score_x', action='store_true', dest='score_x',default=False, help='score_x')
    parser.add_option('-O', '--oper', action='store_true', dest='oper',default=False, help='oper')
    parser.add_option('-f', '--frame', action='store_true', dest='frame',default=False, help='frame')
    parser.add_option('-F', '--fill', action='store_true', dest='fill',default=False, help='fill')
    parser.add_option('-u', '--fun', action='store', dest='fun',default=None, help='fun')
    parser.add_option('-b', '--begin', action='store', dest='begin',default='2010-01-01', help='begin')
 
    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    bill = ikbill()
    if ops.day and re.match('\d{4}-\d{2}-\d{2}',ops.day):
        bill.afterup(ops.day)
    if ops.score:
        bill.score()
    if ops.frame:
        bill.frame()
    if ops.score_x:
        bill.score_x()
    if ops.oper:
        bill.ops()
    if ops.fill:
        bill.fill(ops.begin,ops.fun)
            
            
            
            
            


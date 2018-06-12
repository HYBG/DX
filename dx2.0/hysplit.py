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
import copy
from bs4 import BeautifulSoup
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil
from iktool import iktool

g_iu = ikutil()
g_tool = iktool()

class hyiknow:
    def __init__(self):
        self.__codes = {}
        g_tool.conn('hy')
        self._reload()
        self._mindate = '2015-01-05'
        self._logger = g_iu.createlogger('hysplit',os.path.join(os.path.join(g_home,'log'),'hysplit.log'),logging.INFO)

    def __del__(self):
        pass

    def _reload(self):
        g_tool.reconn('hy')
        data = g_tool.exesqlbatch('select code from hy.iknow_name order by code', None)
        for row in data:
            ld = g_tool.exesqlone('select date from hy.iknow_data where code=%s order by date desc limit 1',(row[0],))
            if len(ld)!=0:
                self.__codes[row[0]]=ld[0]
            else:
                self.__codes[row[0]]='1982-09-04'
                
    def _codes(self):
        codes = self.__codes.keys()
        codes.sort()
        return codes

    def _cleardir(self,dir):
        if os.path.isdir(dir):
            cwd = os.getcwd()
            os.chdir(dir)
            g_iu.execmd('rm -fr *')
            os.chdir(cwd)
        else:
            g_iu.mkdir(dir)
        
    def save(self,dir):
        self._reload()
        clis = self._codes()
        total = float(len(clis))
        handled = 1
        self._cleardir(dir)
        self._logger.info('hysplit save task start....')
        for code in clis:
            data = g_tool.exesqlbatch('select code,date,open,high,low,close,volh,volwy from hy.iknow_data where code=%s order by date',(code,))
            ofn = os.path.join(dir,'%s.csv'%code)
            g_iu.dumpfile(ofn,data)
            self._logger.info('hysplit save handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
            handled = handled+1
        self._logger.info('hysplit save task done....')

    def _stdv(self,val,ev,std):
        stdv = 0.0
        if std!=0:
            stdv = (val-ev)/std
        return float('%0.4f'%stdv)

    def _standardization(self,need):
        prices = 0.0
        volwy = 0.0
        for row in need:
            prices = prices + row[1] + row[2] + row[3] + row[4]
            volwy = volwy + row[5]
        pev = prices/(len(need)*4.0)
        vev = volwy/float(len(need))
        prices = 0.0
        volwy = 0.0
        for row in need:
            prices = prices + (row[1]-pev)**2 + (row[2]-pev)**2 + (row[3]-pev)**2 + (row[4]-pev)**2
            volwy = volwy + (row[5]-vev)**2
        pstd = prices**0.5
        vstd = volwy**0.5
        lis = []
        tmp = list(copy.deepcopy(need))
        while len(tmp)>0:
            row = tmp.pop()
            for i in range(1,len(row)-1):
                lis.append(self._stdv(row[i],pev,pstd))
            lis.append(self._stdv(row[-1],vev,vstd))
        return tuple(lis)
        
    def _standardization2(self,need):
        prices = 0.0
        for row in need:
            prices = prices + row[1] + row[2] + row[3] + row[4]
        pev = prices/(len(need)*4.0)
        prices = 0.0
        for row in need:
            prices = prices + (row[1]-pev)**2 + (row[2]-pev)**2 + (row[3]-pev)**2 + (row[4]-pev)**2
        pstd = prices**0.5
        lis = []
        tmp = list(copy.deepcopy(need[-2:]))
        while len(tmp)>0:
            row = tmp.pop()
            for i in range(1,len(row)-1):
                lis.append(self._stdv(row[i],pev,pstd))
        return tuple(lis)

    def _nfv(self,cur,next1,next2):
        hb = 0
        if next1[2]>cur[2]:
            hb = 1
        lb = 0
        if next1[3]<cur[3]:
            lb = 1
        k = 0
        if next1[4]>next1[1]:
            k = 1
        hp = 0
        if (hb==1) and (next1[2]>next2[2]):
            hp = 1
        lp = 0
        if (lb==1) and (next1[3]<next2[3]):
            lp = 1
        return '%d%d%d%d%d'%(hb,lb,k,hp,lp)
        
    def importlib(self,dir,db,table):
        self._logger.info('hysplit importlib task start dir[%s] db[%s] table[%s]....'%(dir,db,table))
        files = os.listdir(dir)
        files.sort()
        total = float(len(clis))
        handled = 1
        for fn in files:
            ffn = os.path.join(dir,fn.strip())
            g_iu.importdata(ffn,table,db)
            self._logger.info('hysplit importlib handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
            handled = handled+1
        self._logger.info('hysplit importlib task done dir[%s] db[%s] table[%s]....'%(dir,db,table))

    def collect(self,idir,odir):
        self._logger.info('hysplit collect task start....')
        self._cleardir(odir)
        clis = self._codes()
        libdir = os.path.join(odir,'library')
        g_iu.mkdir(libdir)
        total = float(len(clis))
        handled = 1
        for code in clis:
            data = g_tool.exesqlbatch('select date,open,high,low,close,volwy from hy.iknow_data where code=%s order by date',(code,))
            if len(data)<360:
                continue
            mat = []
            ofn = os.path.join(libdir,'%s.csv'%code)
            for i in range(5,len(data)-2):
                date = data[i][0]
                if date<'2005-01-01':
                    continue
                need = data[i-5:i]
                stdvec = self._standardization(need)
                nfv = self._nfv(data[i],data[i+1],data[i+2])
                mat.append((code,date)+stdvec+(nfv,))
            g_iu.dumpfile(ofn,mat)
            self._logger.info('hysplit collect handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
            handled = handled+1
        self._logger.info('hysplit collect task done....')
        return libdir
        
    def collect3(self,idir,odir):
        self._logger.info('hysplit collect3 task start....')
        self._cleardir(odir)
        clis = self._codes()
        libdir = os.path.join(odir,'library3')
        g_iu.mkdir(libdir)
        total = float(len(clis))
        handled = 1
        for code in clis:
            data = g_tool.exesqlbatch('select date,open,high,low,close,volwy from hy.iknow_data where code=%s order by date',(code,))
            if len(data)<360:
                continue
            mat = []
            ofn = os.path.join(libdir,'%s.csv'%code)
            for i in range(3,len(data)-2):
                date = data[i][0]
                if date<'2005-01-01':
                    continue
                need = data[i-3:i]
                stdvec = self._standardization(need)
                nfv = self._nfv(data[i],data[i+1],data[i+2])
                mat.append((code,date)+stdvec+(nfv,))
            g_iu.dumpfile(ofn,mat)
            self._logger.info('hysplit collect3 handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
            handled = handled+1
        self._logger.info('hysplit collect3 task done....')
        return libdir
        
    def _fv(self,cur,prev1,prev2):
        hb = 0
        if cur[2]>prev1[2]:
            hb = 1
        lb = 0
        if cur[3]<prev1[3]:
            lb = 1
        k = 0
        if cur[4]>cur[1]:
            k = 1
        vol0 = 0
        if cur[4]!=cur[1]:
            vol0 = ((cur[4]-cur[1])/abs((cur[4]-cur[1])))*cur[5]
        vol1 = 0
        if prev1[4]!=prev1[1]:
            vol1 = ((prev1[4]-prev1[1])/abs((prev1[4]-prev1[1])))*prev1[5]
        vol2 = 0
        if prev2[4]!=prev2[1]:
            vol2 = ((prev2[4]-prev2[1])/abs((prev2[4]-prev2[1])))*prev2[5]
        v1 = 0
        if vol0-vol1>0:
            v1 = 1
        v2 = 0
        if vol0+vol2-2*vol1>0:
            v2 = 1
        return '%d%d%d%d%d'%(hb,lb,k,v1,v2)
        
    def collect2(self,idir,odir):
        self._logger.info('hysplit collect2 task start....')
        self._cleardir(odir)
        clis = self._codes()
        libdir = os.path.join(odir,'library2')
        g_iu.mkdir(libdir)
        total = float(len(clis))
        handled = 0
        for code in clis:
            handled = handled+1
            data = g_tool.exesqlbatch('select date,open,high,low,close,volwy from hy.iknow_data where code=%s order by date',(code,))
            if len(data)<360:
                continue
            mat = []
            ofn = os.path.join(libdir,'%s.csv'%code)
            for i in range(5,len(data)-2):
                date = data[i][0]
                if date<'2005-01-01':
                    continue
                need = data[i-5:i]
                stdvec = self._standardization2(need)
                fv = self._fv(data[i],data[i-1],data[i-2])
                nfv = self._nfv(data[i],data[i+1],data[i+2])
                mat.append((code,date,fv)+stdvec+(nfv,))
            g_iu.dumpfile(ofn,mat)
            self._logger.info('hysplit collect2 handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
        self._logger.info('hysplit collect2 task done....')
        return libdir

    def _range(self,stdvec,thv,day):
        d1 = g_tool.exesqlbatch('select code,date,stdo,stdh,stdl,stdc,stdv,stdo1,stdh1,stdl1,stdc1,stdv1,stdo2,stdh2,stdl2,stdc2,stdv2,stdo3,stdh3,stdl3,stdc3,stdv3,stdo4,stdh4,stdl4,stdc4,stdv4,nfv from dx.iknow_lib where date<%s and stdo>%s and stdo<%s and stdh>%s and stdh<%s and stdl>%s and stdl<%s and stdc>%s and stdc<%s and stdv>%s and stdv<%s and stdo1>%s and stdo1<%s and stdh1>%s and stdh1<%s and stdl1>%s and stdl1<%s and stdc1>%s and stdc1<%s and stdv1>%s and stdv1<%s and stdo2>%s and stdo2<%s and stdh2>%s and stdh2<%s and stdl2>%s and stdl2<%s and stdc2>%s and stdc2<%s and stdv2>%s and stdv2<%s',(day,stdvec[0]-thv,stdvec[0]+thv,stdvec[1]-thv,stdvec[1]+thv,stdvec[2]-thv,stdvec[2]+thv,stdvec[3]-thv,stdvec[3]+thv,stdvec[4]-thv,stdvec[4]+thv,stdvec[5]-thv,stdvec[5]+thv,stdvec[6]-thv,stdvec[6]+thv,stdvec[7]-thv,stdvec[7]+thv,stdvec[8]-thv,stdvec[8]+thv,stdvec[9]-thv,stdvec[9]+thv,stdvec[10]-thv,stdvec[10]+thv,stdvec[11]-thv,stdvec[11]+thv,stdvec[12]-thv,stdvec[12]+thv,stdvec[13]-thv,stdvec[13]+thv,stdvec[14]-thv,stdvec[14]+thv))
        d2 = g_tool.exesqlbatch('select code,date,stdo,stdh,stdl,stdc,stdv,stdo1,stdh1,stdl1,stdc1,stdv1,stdo2,stdh2,stdl2,stdc2,stdv2,stdo3,stdh3,stdl3,stdc3,stdv3,stdo4,stdh4,stdl4,stdc4,stdv4,nfv from dx.iknow_lib where date<%s and stdo3>%s and stdo3<%s and stdh3>%s and stdh3<%s and stdl3>%s and stdl3<%s and stdc3>%s and stdc3<%s and stdv3>%s and stdv3<%s and stdo4>%s and stdo4<%s and stdh4>%s and stdh4<%s and stdl4>%s and stdl4<%s and stdc4>%s and stdc4<%s and stdv4>%s and stdv4<%s',(day,stdvec[15]-thv,stdvec[15]+thv,stdvec[16]-thv,stdvec[16]+thv,stdvec[17]-thv,stdvec[17]+thv,stdvec[18]-thv,stdvec[18]+thv,stdvec[19]-thv,stdvec[19]+thv,stdvec[20]-thv,stdvec[20]+thv,stdvec[21]-thv,stdvec[21]+thv,stdvec[22]-thv,stdvec[22]+thv,stdvec[23]-thv,stdvec[23]+thv,stdvec[24]-thv,stdvec[24]+thv))
        dd1 = {}
        for r in d1:
            dd1[(r[0],r[1])] = r
        data = []
        for r in d2:
            if dd1.has_key((r[0],r[1])):
                data.append(r[2:])
        return data

    def _range3(self,stdvec,thv,day):
        d1 = g_tool.exesqlbatch('select code,date,stdo,stdh,stdl,stdc,stdv,stdo1,stdh1,stdl1,stdc1,stdv1,stdo2,stdh2,stdl2,stdc2,stdv2,stdo3,stdh3,stdl3,stdc3,stdv3,stdo4,stdh4,stdl4,stdc4,stdv4,nfv from dx.iknow_lib where date<%s and stdo>%s and stdo<%s and stdh>%s and stdh<%s and stdl>%s and stdl<%s and stdc>%s and stdc<%s and stdv>%s and stdv<%s and stdo1>%s and stdo1<%s and stdh1>%s and stdh1<%s and stdl1>%s and stdl1<%s and stdc1>%s and stdc1<%s and stdv1>%s and stdv1<%s and stdo2>%s and stdo2<%s and stdh2>%s and stdh2<%s and stdl2>%s and stdl2<%s and stdc2>%s and stdc2<%s and stdv2>%s and stdv2<%s',(day,stdvec[0]-thv,stdvec[0]+thv,stdvec[1]-thv,stdvec[1]+thv,stdvec[2]-thv,stdvec[2]+thv,stdvec[3]-thv,stdvec[3]+thv,stdvec[4]-thv,stdvec[4]+thv,stdvec[5]-thv,stdvec[5]+thv,stdvec[6]-thv,stdvec[6]+thv,stdvec[7]-thv,stdvec[7]+thv,stdvec[8]-thv,stdvec[8]+thv,stdvec[9]-thv,stdvec[9]+thv,stdvec[10]-thv,stdvec[10]+thv,stdvec[11]-thv,stdvec[11]+thv,stdvec[12]-thv,stdvec[12]+thv,stdvec[13]-thv,stdvec[13]+thv,stdvec[14]-thv,stdvec[14]+thv))
        return list(d1)

    def _prob(self,data):
        perf = [[row[i] for row in data] for i in range(5)]
        hbp = sum(perf[0])/float(len(data))
        lbp = sum(perf[1])/float(len(data))
        kp = sum(perf[2])/float(len(data))
        hpp = sum(perf[3])/float(len(data))
        lpp = sum(perf[4])/float(len(data))
        return (hbp,lbp,kp,hpp,lpp)
        
    def _prob2(self,data):
        perf = [[row[i] for row in data] for i in range(6)]
        hbp = sum(perf[1])/float(len(data))
        lbp = sum(perf[2])/float(len(data))
        kp = sum(perf[3])/float(len(data))
        hpp = sum(perf[4])/float(len(data))
        lpp = sum(perf[5])/float(len(data))
        return (hbp,lbp,kp,hpp,lpp)

    def distance(self,v1,v2):
        all = 0.0
        for i in range(len(v1)):
            all = all + (v1[i]-v2[i])**2
        return all**0.5
        
    def test(self,day,odir):
        self._logger.info('hysplit test[%s] task start....'%day)
        self._cleardir(odir)
        clis = self._codes()
        total = float(len(clis))
        handled = 1
        mat = []
        for code in clis:
            self._logger.info('hysplit test[%s] handle code[%s]....'%(day,code))
            data = g_tool.exesqlbatch('select date,open,high,low,close,volwy from hy.iknow_data where code=%s and date<=%s order by date desc limit 5',(code,day))
            data = list(data)
            data.sort()
            stdvec = self._standardization(data)
            rng = self._range(stdvec,0.25,day)
            self._logger.info('hysplit test[%s] handle code[%s] range[%d]....'%(day,code,len(rng)))
            tmt = []
            for row in rng:
                d = self.distance(stdvec,row[-1])
                if d<0.25:
                    tmt.append((row[-1][0],row[-1][1],row[-1][2],row[-1][3],row[-1][4]))
            if len(tmt)==0:
                continue
            self._logger.info('hysplit test[%s] handle code[%s] range[%d] hit[%d]....'%(day,code,len(rng),len(tmt)))
            tell = self._prob(tmt)
            nextday = g_tool.exesqlone('select date from hy.iknow_data where code=%s and date>%s order by date limit 1',(code,day))
            if len(nextday)==0:
                continue
            nextday = nextday[0]
            nb = g_tool.exesqlone('select hb,lb,k from hy.iknow_kinfo where code=%s and date=%s',(code,nextday))
            np = g_tool.exesqlone('select hp,lp from hy.iknow_poles where code=%s and date=%s',(code,nextday))
            if len(nb)==0:
                continue
            if len(np)==0:
                continue
            mat.append((code,day,len(tmt))+tell+nb+np)
            self._logger.info('hysplit test handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
            handled = handled+1
        ofn = os.path.join(dir,'%s.csv'%day)
        g_iu.dumpfile(ofn,mat)
        self._logger.info('hysplit test[%s] task done....'%day)
        
    def test3(self,day,odir):
        self._logger.info('hysplit test3[%s] task start....'%day)
        self._cleardir(odir)
        clis = self._codes()
        total = float(len(clis))
        handled = 1
        #mat = []
        ofn = os.path.join(odir,'%s.csv'%day)
        for code in clis:
            self._logger.info('hysplit test3[%s] handle code[%s]....'%(day,code))
            data = g_tool.exesqlbatch('select date,open,high,low,close,volwy from hy.iknow_data where code=%s and date<=%s order by date desc limit 3',(code,day))
            data = list(data)
            data.sort()
            stdvec = self._standardization(data)
            rng = self._range3(stdvec,0.35,day)
            #self._logger.info('hysplit test3[%s] handle code[%s] range[%d]....'%(day,code,len(rng)))
            tmt = []
            for row in rng:
                d = self.distance(stdvec,row[2:-1])
                if d<0.35:
                    tmt.append((int(row[-1][0]),int(row[-1][1]),int(row[-1][2]),int(row[-1][3]),int(row[-1][4])))
            if len(tmt)==0:
                continue
            self._logger.info('hysplit test3[%s] handle code[%s] range[%d] hit[%d]....'%(day,code,len(rng),len(tmt)))
            #print 'tmt string[%s]'%str(tmt)
            tell = self._prob(tmt)
            nextday = g_tool.exesqlone('select date from hy.iknow_data where code=%s and date>%s order by date limit 1',(code,day))
            if len(nextday)==0:
                continue
            nextday = nextday[0]
            nb = g_tool.exesqlone('select hb,lb,k from hy.iknow_kinfo where code=%s and date=%s',(code,nextday))
            np = g_tool.exesqlone('select hp,lp from hy.iknow_poles where code=%s and date=%s',(code,nextday))
            if len(nb)==0:
                continue
            if len(np)==0:
                continue
            g_iu.appendmat(ofn,[(code,day,len(tmt))+tell+nb+np])
            self._logger.info('hysplit test3 handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
            handled = handled+1
        #ofn = os.path.join(odir,'%s.csv'%day)
        #g_iu.dumpfile(ofn,mat)
        self._logger.info('hysplit test3[%s] task done....'%day)
        
    def _range2(self,fv,stdvec,thv,day):
        data = g_tool.exesqlbatch('select code,date,stdo,stdh,stdl,stdc,stdo1,stdh1,stdl1,stdc1,nfv from dx.iknow_lib where fv=%s and date<%s and stdo>%s and stdo<%s and stdh>%s and stdh<%s and stdl>%s and stdl<%s and stdc>%s and stdc<%s and stdo1>%s and stdo1<%s and stdh1>%s and stdh1<%s and stdl1>%s and stdl1<%s and stdc1>%s and stdc1<%s',(fv,day,stdvec[0]-thv,stdvec[0]+thv,stdvec[1]-thv,stdvec[1]+thv,stdvec[2]-thv,stdvec[2]+thv,stdvec[3]-thv,stdvec[3]+thv,stdvec[4]-thv,stdvec[4]+thv,stdvec[5]-thv,stdvec[5]+thv,stdvec[6]-thv,stdvec[6]+thv,stdvec[7]-thv,stdvec[7]+thv))
        return list(data)
        
    def _guass(self,lis):
        ev = sum(lis)/float(len(lis))
        all = 0.0
        for item in lis:
            all = all + (item-ev)**2
        std = all**0.5
        return (ev,std)
        
    def test2(self,day,odir):
        self._logger.info('hysplit test2[%s] task start....'%day)
        #self._cleardir(odir)
        g_iu.mkdir(odir)
        clis = self._codes()
        total = float(len(clis))
        handled = 1
        #mat = []
        thv = 0.1
        maxlen = 66
        hpyes = []
        lpyes = []
        hpno = []
        lpno = []
        ofn = os.path.join(odir,'%s.csv'%day)
        if os.path.isfile(ofn):
            g_iu.execmd('rm -fr %s'%ofn)
        for code in clis:
            self._logger.info('hysplit test2[%s] handle code[%s]....'%(day,code))
            data = g_tool.exesqlbatch('select date,open,high,low,close,volwy from hy.iknow_data where code=%s and date<=%s order by date desc limit 5',(code,day))
            fv = self._fv(data[0],data[1],data[2])
            data = list(data)
            data.sort()
            stdvec = self._standardization2(data)
            rng = self._range2(fv,stdvec,thv,day)
            #self._logger.info('hysplit test3[%s] handle code[%s] range[%d]....'%(day,code,len(rng)))
            tmt = []
            for row in rng:
                d = self.distance(stdvec,row[2:-1])
                if d<thv:
                    tmt.append((d,int(row[-1][0]),int(row[-1][1]),int(row[-1][2]),int(row[-1][3]),int(row[-1][4])))
            if len(tmt)==0:
                continue
            if len(tmt)>maxlen:
                tmt.sort()
                tmt = tmt[:maxlen]
            self._logger.info('hysplit test2[%s] handle code[%s] range[%d] hit[%d]....'%(day,code,len(rng),len(tmt)))
            #print 'tmt string[%s]'%str(tmt)
            tell = self._prob2(tmt)
            nextday = g_tool.exesqlone('select date from hy.iknow_data where code=%s and date>%s order by date limit 1',(code,day))
            if len(nextday)==0:
                continue
            nextday = nextday[0]
            nb = g_tool.exesqlone('select hb,lb,k from hy.iknow_kinfo where code=%s and date=%s',(code,nextday))
            np = g_tool.exesqlone('select hp,lp from hy.iknow_poles where code=%s and date=%s',(code,nextday))
            if len(nb)==0:
                continue
            if len(np)==0:
                continue
            g_iu.appendmat(ofn,[(code,day,len(tmt))+tell+nb+np])
            if np[0]==0:
                hpno.append(tell[3])
            else:
                hpyes.append(tell[3])
            if np[1]==0:
                lpno.append(tell[4])
            else:
                lpyes.append(tell[4])
            self._logger.info('hysplit test2 handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
            handled = handled+1
        hpyesgs = self._guass(hpyes)
        hpnogs = self._guass(hpno)
        lpyesgs = self._guass(lpyes)
        lpnogs = self._guass(hpno)
        f = open(os.path.join(odir,'%s_hplp.csv'%day),'w')
        f.write('hpyes:%0.4f,%0.4f\n'%(hpyesgs[0],hpyesgs[1]))
        f.write('hpno:%0.4f,%0.4f\n'%(hpnogs[0],hpnogs[1]))
        f.write('lpyes:%0.4f,%0.4f\n'%(lpyesgs[0],lpyesgs[1]))
        f.write('lpno:%0.4f,%0.4f\n'%(lpnogs[0],lpnogs[1]))
        f.close()
        #ofn = os.path.join(odir,'%s.csv'%day)
        #g_iu.dumpfile(ofn,mat)
        self._logger.info('hysplit test2[%s] task done....'%day)

    def _fv4(self,cur,prev):
        hb = 0
        if cur[2]>prev[2]:
            hb = 1
        lb = 0
        if cur[3]<prev[3]:
            lb = 1
        k = 0
        if cur[4]>cur[1]:
            k = 1
        v1 = 0
        if (cur[4]>cur[1])*cur[5]-(prev[4]>prev[1])*prev[5]>0:
            v1 = 1
        return '%d%d%d%d'%(hb,lb,k,v1)

    def _standardization4(self,need):
        prices = 0.0
        for row in need:
            prices = prices + row[1] + row[2] + row[3] + row[4]
        pev = prices/(len(need)*4.0)
        prices = 0.0
        for row in need:
            prices = prices + (row[1]-pev)**2 + (row[2]-pev)**2 + (row[3]-pev)**2 + (row[4]-pev)**2
        pstd = prices**0.5
        lis = []
        tmp = list(copy.deepcopy(need))
        while len(tmp)>0:
            row = tmp.pop()
            for i in range(1,len(row)-1):
                lis.append(self._stdv(row[i],pev,pstd))
        return tuple(lis)
        
    def _profit(self,cur,next1,next2):
        low = cur[3]
        nclose1 = next1[4]
        nclose2 = next2[4]
        p1 = (nclose1-low)/low
        p2 = (nclose2-low)/low
        h1 = (next1[2]-cur[4])/cur[4]
        l1 = (next1[3]-cur[4])/cur[4]
        return (float('%0.4f'%p1),float('%0.4f'%p2),float('%0.4f'%h1),float('%0.4f'%l1))

    def collect4(self,idir,odir):
        self._logger.info('hysplit collect4 task start....')
        self._cleardir(odir)
        clis = self._codes()
        libdir = os.path.join(odir,'library4')
        g_iu.mkdir(libdir)
        total = float(len(clis))
        handled = 0
        for code in clis:
            handled = handled+1
            data = g_tool.exesqlbatch('select date,open,high,low,close,volh from hy.iknow_data where code=%s order by date',(code,))
            if len(data)<360:
                continue
            mat = []
            ofn = os.path.join(libdir,'%s.csv'%code)
            for i in range(1,len(data)-2):
                date = data[i][0]
                if date<'2006-01-01':
                    continue
                lowf = (data[i][3]-data[i-1][4])/data[i-1][4]
                if lowf<-0.101:
                    if len(mat)>0:
                        mat.pop()
                    if len(mat)>0:
                        mat.pop()
                need = data[i-1:i+1]
                stdvec = self._standardization4(need)
                fv = self._fv4(data[i],data[i-1])
                nfv = self._nfv(data[i],data[i+1],data[i+2])
                pp = self._profit(data[i],data[i+1],data[i+2])
                mat.append((code,date,fv)+stdvec+(nfv,)+pp)
            g_iu.dumpfile(ofn,mat)
            self._logger.info('hysplit collect4 handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
        self._logger.info('hysplit collect4 task done....')
        cwd = os.getcwd()
        os.chdir(os.path.join(g_home,'tmp'))
        g_iu.execmd('python imdb.py -d %s -D dx -t iknow_lib4'%(libdir))
        os.chdir(cwd)
        return libdir
        
    def _range4(self,fv,stdvec,thv,day):
        data = g_tool.exesqlbatch('select code,date,stdo,stdh,stdl,stdc,stdo1,stdh1,stdl1,stdc1,nfv,p1,p2 from dx.iknow_lib4 where date<%s and fv=%s and stdo>%s and stdo<%s and stdh>%s and stdh<%s and stdl>%s and stdl<%s and stdc>%s and stdc<%s and stdo1>%s and stdo1<%s and stdh1>%s and stdh1<%s and stdl1>%s and stdl1<%s and stdc1>%s and stdc1<%s',(day,fv,stdvec[0]-thv,stdvec[0]+thv,stdvec[1]-thv,stdvec[1]+thv,stdvec[2]-thv,stdvec[2]+thv,stdvec[3]-thv,stdvec[3]+thv,stdvec[4]-thv,stdvec[4]+thv,stdvec[5]-thv,stdvec[5]+thv,stdvec[6]-thv,stdvec[6]+thv,stdvec[7]-thv,stdvec[7]+thv))
        return list(data)

    def _prob4(self,data):
        perf = [[row[i] for row in data] for i in range(8)]
        p1p = sum(perf[1])/float(len(data))
        p2p = sum(perf[2])/float(len(data))
        hbp = sum(perf[3])/float(len(data))
        lbp = sum(perf[4])/float(len(data))
        kp = sum(perf[5])/float(len(data))
        hpp = sum(perf[6])/float(len(data))
        lpp = sum(perf[7])/float(len(data))
        return (p1p,p2p,hbp,lbp,kp,hpp,lpp)

    def test4(self,day,odir):
        self._logger.info('hysplit test4[%s] task start....'%day)
        #self._cleardir(odir)
        g_iu.mkdir(odir)
        clis = self._codes()
        self._logger.info('hysplit test4[%s] handle code[%d]....'%(day,len(clis)))
        total = float(len(clis))
        handled = 1
        mat = []
        thv = 0.1
        maxlen = 131
        ofn = os.path.join(odir,'%s.csv'%day)
        if os.path.isfile(ofn):
            g_iu.execmd('rm -fr %s'%ofn)
        for code in clis:
            #self._logger.info('hysplit test4[%s] handle code[%s]....'%(day,code))
            data = g_tool.exesqlbatch('select date,open,high,low,close,volh from hy.iknow_data where code=%s and date<=%s order by date desc limit 2',(code,day))
            fv = self._fv4(data[0],data[1])
            data = list(data)
            data.sort()
            stdvec = self._standardization4(data)
            rng = self._range4(fv,stdvec,thv,day)
            tmt = []
            #self._logger.info('hysplit test4[%s] handle code[%s] rng[%d]....'%(day,code,len(rng)))
            for row in rng:
                d = self.distance(stdvec,row[2:-3])
                if d<thv:
                    tmt.append((d,row[-2],row[-1],int(row[-3][0]),int(row[-3][1]),int(row[-3][2]),int(row[-3][3]),int(row[-3][4])))
            if len(tmt)==0:
                continue
            if len(tmt)>maxlen:
                tmt.sort()
                tmt = tmt[:maxlen]
            tell = self._prob4(tmt)
            mat.append((code,day,len(tmt))+tell)
            g_iu.appendmat(ofn,[(code,day,len(tmt))+tell])
            self._logger.info('hysplit test4 handle progress[%0.2f%%] code[%s] range[%d] hit[%d]....'%(100*(handled/total),code,len(rng),len(tmt)))
            handled = handled+1
        mat.sort(key=lambda x:x[3])
        ofns = os.path.join(odir,'%s_s.csv'%day)
        g_iu.dumpfile(ofns,mat)
        self._logger.info('hysplit test4[%s] task done....'%day)
        

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-s', '--save', action='store_true', dest='save',default=False, help='save data from db first')
    parser.add_option('-i', '--input', action='store', dest='input',default=None, help='input dir')
    parser.add_option('-o', '--output', action='store', dest='output',default=None, help='output dir')
    parser.add_option('-d', '--db', action='store', dest='db',default=None, help='db name')
    parser.add_option('-l', '--library', action='store', dest='library',default=None, help='library table name')
    parser.add_option('-t', '--tell', action='store', dest='tell',default=None, help='tell table name')
    parser.add_option('-D', '--day', action='store', dest='day',default=None, help='tell day')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    ik = hyiknow()
    if ops.input:
        if ops.save:
            ik.save(ops.input)
        if ops.output:
            libdir = ik.collect4(ops.input,ops.output)
            if ops.db and ops.library:
                ik.importlib(libdir,ops.db,ops.library)
    if ops.day:
        ik.test4(ops.day,os.path.join(os.path.join(g_home,'library0423'),'test4'))
    
    
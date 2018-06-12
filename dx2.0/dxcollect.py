#!/usr/bin/python

import os
import sys
import urllib2
import logging
import string
import re
import datetime
import time
import random
import socket
import commands
import MySQLdb
from bs4 import BeautifulSoup
from optparse import OptionParser
from logging.handlers import RotatingFileHandler

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil
from iktool import iktool
from iktool import ikdata
from iktool import ikrecord

g_iu = ikutil()
g_tool = iktool()

class hyclct:
    def __init__(self):
        self._codes = []
        self._data = {}
        g_tool.conn('hy')
        data = g_tool.exesqlbatch('select distinct code from hy.iknow_name order by code', None)
        for row in data:
            self._codes.append(row[0])
        self._logger = g_iu.createlogger('hyclct',os.path.join(os.path.join(g_home,'log'),'hyclct.log'),logging.INFO)
        
    def __del__(self):
        pass

    def _cleardir(self,dir):
        if os.path.isdir(dir):
            cwd = os.getcwd()
            os.chdir(dir)
            g_iu.execmd('rm -fr *')
            os.chdir(cwd)
        else:
            g_iu.mkdir(dir)
        
    def _stdv(self,val,ev,std):
        stdv = 0.0
        if std!=0:
            stdv = (val-ev)/std
        return float('%0.4f'%stdv)
        
    def _fv(self,cur,prev1,prev2):
        hb = 0
        if cur.high>prev1.high:
            hb = 1
        lb = 0
        if cur.low<prev1.low:
            lb = 1
        k = 0
        if cur.close>cur.open:
            k = 1
        hb1 = 0
        if prev1.high>prev2.high:
            hb1 = 1
        lb1 = 0
        if prev1.low<prev2.low:
            lb1 = 1
        k1 = 0
        if prev1.close>prev2.open:
            k1 = 1
        vol0 = 0
        if cur.close!=cur.open:
            vol0 = ((cur.close-cur.open)/abs((cur.close-cur.open)))*cur.volh
        vol1 = 0
        if prev1.close!=prev1.open:
            vol1 = ((prev1.close-prev1.open)/abs((prev1.close-prev1.open)))*prev1.volh
        vol2 = 0
        if prev2.close!=prev2.open:
            vol2 = ((prev2.close-prev2.open)/abs((prev2.close-prev2.open)))*prev2.volh
        v1 = 0
        if vol0-vol1>0:
            v1 = 1
        v2 = 0
        if vol0+vol2-2*vol1>0:
            v2 = 1
        return '%d%d%d%d%d%d%d%d'%(hb,lb,k,v1,hb1,lb1,k1,v2)
        
    def _nfv(self,cur,next1,next2):
        hb = 0
        if next1.high>cur.high:
            hb = 1
        lb = 0
        if next1.low<cur.low:
            lb = 1
        k = 0
        if next1.close>next1.open:
            k = 1
        hp = 0
        if (hb==1) and (next1.high>next2.high):
            hp = 1
        lp = 0
        if (lb==1) and (next1.low<next2.low):
            lp = 1
        return '%d%d%d%d%d'%(hb,lb,k,hp,lp)
        
    def _profit(self,cur,next1):
        h1 = (next1.high-cur.close)/cur.close
        l1 = (next1.low-cur.close)/cur.close
        return (float('%0.4f'%h1),float('%0.4f'%l1))
        
    def _standardization(self,cur,prev1,prev2):
        pev = (cur.ev()+prev1.ev()+prev2.ev())/3.0
        prices = 0.0
        prices = prices + (cur.open-pev)**2 + (cur.high-pev)**2 + (cur.low-pev)**2 + (cur.close-pev)**2
        prices = prices + (prev1.open-pev)**2 + (prev1.high-pev)**2 + (prev1.low-pev)**2 + (prev1.close-pev)**2
        prices = prices + (prev2.open-pev)**2 + (prev2.high-pev)**2 + (prev2.low-pev)**2 + (prev2.close-pev)**2
        pstd = prices**0.5
        lis = []
        lis.append(self._stdv(cur.open,pev,pstd))
        lis.append(self._stdv(cur.high,pev,pstd))
        lis.append(self._stdv(cur.low,pev,pstd))
        lis.append(self._stdv(cur.close,pev,pstd))
        lis.append(self._stdv(prev1.open,pev,pstd))
        lis.append(self._stdv(prev1.high,pev,pstd))
        lis.append(self._stdv(prev1.low,pev,pstd))
        lis.append(self._stdv(prev1.close,pev,pstd))
        lis.append(self._stdv(prev2.open,pev,pstd))
        lis.append(self._stdv(prev2.high,pev,pstd))
        lis.append(self._stdv(prev2.low,pev,pstd))
        lis.append(self._stdv(prev2.close,pev,pstd))
        return tuple(lis)
        
    def importlib(self,dir,db,table):
        self._logger.info('hyclct importlib task start dir[%s] db[%s] table[%s]....'%(dir,db,table))
        files = os.listdir(dir)
        files.sort()
        total = float(len(clis))
        handled = 1
        for fn in files:
            ffn = os.path.join(dir,fn.strip())
            g_iu.importdata(ffn,table,db)
            self._logger.info('hyclct importlib handle progress[%0.2f%%] file[%s]....'%(100*(handled/total),fn.strip()))
            handled = handled+1
        self._logger.info('hyclct importlib task done dir[%s] db[%s] table[%s]....'%(dir,db,table))
        
    def collect(self,idir,odir):
        self._logger.info('hyclct collect task start....')
        self._cleardir(odir)
        clis = self._codes
        libdir = os.path.join(odir,'dxcollect')
        g_iu.mkdir(libdir)
        total = float(len(clis))
        handled = 0
        for code in clis:
            handled = handled+1
            data = ikdata()
            data.load(code)
            if data.length()<360:
                continue
            mat = []
            ofn = os.path.join(libdir,'%s.csv'%code)
            for i in range(3,data.length()-2):
                date = data.get(i).date
                if date<'2006-01-01':
                    continue
                lowf = (data.get(i).low-data.get(i-1).close)/data.get(i-1).close
                if lowf<-0.101:
                    if len(mat)>0:
                        mat.pop()
                    if len(mat)>0:
                        mat.pop()
                fv = self._fv(data.get(i),data.get(i-1),data.get(i-2))
                stdvec = self._standardization(data.get(i),data.get(i-1),data.get(i-2))
                nfv = self._nfv(data.get(i),data.get(i+1),data.get(i+2))
                pp = self._profit(data.get(i),data.get(i+1))
                mat.append((code,date,fv)+stdvec+(nfv,)+pp)
            g_iu.dumpfile(ofn,mat)
            self._logger.info('hyclct collect handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
        self._logger.info('hyclct collect task done....')
        
    def c1(self,idir,odir):
        self._logger.info('hyclct c1 task start....')
        self._cleardir(odir)
        clis = self._codes
        libdir = os.path.join(odir,'c1')
        g_iu.mkdir(libdir)
        total = float(len(clis))
        handled = 0
        for code in clis:
            handled = handled+1
            data = ikdata()
            data.load(code)
            if data.length()<360:
                continue
            mat = []
            ofn = os.path.join(libdir,'%s.csv'%code)
            for i in range(7,data.length()-2):
                date = data.get(i).date
                if date<'2006-01-01':
                    continue
                lowf = (data.get(i).low-data.get(i-1).close)/data.get(i-1).close
                if lowf<-0.101:
                    if len(mat)>0:
                        mat.pop()
                    if len(mat)>0:
                        mat.pop()
                volwy = 0.0
                for j in range(5):
                    volwy = volwy+data.get(i-j+2).volwy
                if ((data.get(i-1).volwy-data.get(i-2).volwy)/(volwy/5.0)>3):
                
                fv = self._fv(data.get(i),data.get(i-1),data.get(i-2))
                stdvec = self._standardization(data.get(i),data.get(i-1),data.get(i-2))
                nfv = self._nfv(data.get(i),data.get(i+1),data.get(i+2))
                pp = self._profit(data.get(i),data.get(i+1))
                mat.append((code,date,fv)+stdvec+(nfv,)+pp)
            g_iu.dumpfile(ofn,mat)
            self._logger.info('hyclct collect handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
        self._logger.info('hyclct c1 task done....')

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

    ik = hyclct()
    if ops.input and ops.output:
        libdir = ik.collect(ops.input,ops.output)
        if ops.db and ops.library:
            ik.importlib(libdir,ops.db,ops.library)





        
#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import commands
from logging.handlers import RotatingFileHandler
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')
    
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('dxbase')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'dxbase.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class kdata:
    def __init__(self):
        self.code =''
        self.date =''
        self.open = 0.0
        self.high = 0.0
        self.low  = 0.0
        self.close = 0.0
        self.volh  = 0.0
        self.volwy = 0.0
    

class wonderdata:
    def __init__(self):
        self.code =''
        self.date =''
        self.hb  = 0
        self.lb = 0
        self.k = 0
        self.hp = 0
        self.lp = 0
        
class iksetup:
    def __init__(self):
        self._minusefullength=360
        self._defaultstart = '2005-01-01'
        self._datadir = os.path.join(g_home,'dxdata')
        self._basedir = os.path.join(g_home,'dxbase')
        self._fvdir = os.path.join(g_home,'dxfv')
        if not os.path.isdir(self._basedir):
            os.makedirs(self._basedir)
        if not os.path.isdir(self._fvdir):
            os.makedirs(self._fvdir)

    def __del__(self):
        pass
        
    def execmd(self,cmd):
        status,output = commands.getstatusoutput(cmd)
        g_logger.info('execute command[%s],status[%d],output[%s]'%(cmd,status,output.strip()))
        return status

    def _csv2kdata(self,filename):
        f = open(filename,'r')
        rows = f.readlines()
        f.close()
        mat = []
        for r in rows:
            its = r.strip().split(',')
            if len(its)==8:
                data = kdata()
                data.code=its[0].strip()
                data.date=its[1].strip()
                data.open=float(its[2])
                data.high=float(its[3])
                data.low=float(its[4])
                data.close=float(its[5])
                data.volh=float(its[6])
                data.volwy=float(its[7])
                mat.append(data)
        return mat
        
    def _basek(self,cur,last):
        hb = 0
        lb = 0
        if cur.high > last.high:
            hb = 1
        if cur.low < last.low:
            lb = 1
        k = 0
        if cur.close>cur.open:
            k = 1
        return (hb,lb,k)

    def _stdv(self,lis):
        ev = sum(lis)/float(len(lis))
        all = 0
        for item in lis:
            all = all + (item-ev)**2
        std = all**0.5
        stdv = 0.0
        if std!=0:
            stdv = (lis[-1]-ev)/std
        return stdv

    def _poles(self,cur,prev,next):
        hp = 0
        lp = 0
        if (cur.high>prev.high) and (cur.high>next.high):
            hp = 1
        if (cur.low<prev.low) and (cur.low<next.low):
            lp = 1
        return (hp,lp)

    def _genwonder(self,current,prev,next):
        wonder = wonderdata()
        poles = self._poles(current,prev,next)
        base = self._basek(current,prev)
        wonder.code = current.code
        wonder.date = current.date
        wonder.hb  = base[0]
        wonder.lb = base[1]
        wonder.k = base[2]
        wonder.hp = poles[0]
        wonder.lp = poles[1]
        return wonder
        
    def _linar(self,vector):
        line = ''
        for it in vector:
            if type(it) == type(1.0):
                line = line + '%0.4f,'%it
            elif type(it) == type(1):
                line = line + '%d,'%it
            else:
                line = line + '%s,'%str(it)
        return line[:-1]
        
    def _dumpfile(self,filename,mat):
        f = open(filename,'w')
        for r in mat:
            if type(r) == type([]) or type(r) == type(()):
                f.write(u'%s\n'%self._linar(r))
            else:
                f.write(u'%s\n'%str(r))
        f.close()

    def _loadcsv(self,filename):
        f = open(filename,'r')
        rows = f.readlines()
        f.close()
        mat = []
        for r in rows:
            its = r.strip().split(',')
            lis = []
            for i in range(len(its)):
                lis.append(its[i])
            mat.append(tuple(lis))
        return mat

    def _cleardir(self,dir):
        if os.path.isdir(dir):
            cwd = os.getcwd()
            os.chdir(dir)
            self.execmd('rm -fr *')
            os.chdir(cwd)
        else:
            os.makedirs(self.dir)
        
    def generate_base(self):
        g_logger.info('dxbase generate_base handle start....')
        indir = self._datadir
        outdir = self._basedir
        self._cleardir(outdir)
        files = os.listdir(indir)
        files.sort()
        total = float(len(files))
        handled = 1
        for fn in files:
            baseofn = os.path.join(outdir,fn.strip())
            ffn = os.path.join(indir,fn.strip())
            g_logger.info('dxbase generate_base deal with file[%s]'%ffn)
            mat = self._csv2kdata(ffn)
            amt = []
            if len(mat)<=self._minusefullength:
                handled = handled+1
                continue
            for i in range(self._minusefullength,len(mat)-2):
                if mat[i].date<self._defaultstart:
                    continue
                need = mat[i-4:i+1]
                openlis = []
                highlis = []
                lowlis = []
                closelis = []
                volwylis = []
                for item in need:
                    openlis.append(item.open)
                    highlis.append(item.high)
                    lowlis.append(item.low)
                    closelis.append(item.close)
                    volwylis.append(item.volwy)
                stdopen = self._stdv(openlis)
                stdhigh = self._stdv(highlis)
                stdlow = self._stdv(lowlis)
                stdclose = self._stdv(closelis)
                stdvolwy = self._stdv(volwylis)
                wonder = self._genwonder(mat[i+1],mat[i],mat[i+2])
                if (mat[i+1].low-mat[i].close)/mat[i].close<=-0.101:
                    continue
                fv = '%d%d%d%d%d'%(wonder.hb,wonder.lb,wonder.k,wonder.hp,wonder.lp)
                amt.append((mat[i].code,mat[i].date,stdopen,stdhigh,stdlow,stdclose,stdvolwy,wonder.hb,wonder.lb,wonder.k,wonder.hp,wonder.lp,fv))
            self._dumpfile(baseofn,amt)
            g_logger.info('dxbase generate_base handle progress[%0.2f%%] file[%s]....'%(100*(handled/total),fn.strip()))
            handled = handled+1
        g_logger.info('dxbase generate_base handle done....')
        
    def split_fv(self):
        g_logger.info('dxbase split_fv handle start....')
        odir = self._fvdir
        self._cleardir(odir)
        indir = self._basedir
        files = os.listdir(indir)
        files.sort()
        total = float(len(files))
        handled = 1
        for fn in files:
            ffn = os.path.join(indir,fn.strip())
            g_logger.info('dxbase split_fv deal with file[%s]'%ffn)
            mat = self._loadcsv(ffn)
            for row in mat:
                fv = row[-1]
                ofn = os.path.join(odir,'%s.csv'%fv)
                f = open(ofn,'a')
                f.write('%s\n'%self._linar(row))
                f.close()
            g_logger.info('dxbase split_fv handle progress[%0.2f%%] file[%s]....'%(100*(handled/total),fn.strip()))
            handled = handled+1
        g_logger.info('dxbase split_fv handle done....')
        
    def _extvector(self,row):
        try:
            stdopen = float(row[2])
            stdhigh = float(row[3])
            stdlow = float(row[4])
            stdclose = float(row[5])
            stdvolwy = float(row[6])
        except Exception,e:
            g_logger.info('dxbase _extvector exception[%s] code[%s] date[%s]'%(e,row[0],row[1]))
            return None
        return (stdopen,stdhigh,stdlow,stdclose,stdvolwy)

    def learn(self,fv):
        logger = logging.getLogger('fv')
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logfile = os.path.join(logd,'%s.log'%fv)
        rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
        rh.setLevel(logging.INFO)
        fmter = logging.Formatter(formatstr)
        rh.setFormatter(fmter)
        logger.addHandler(rh)
        logger.setLevel(logging.INFO)
        logger.info('dxbase learn fv[%s] handle start....'%fv)
        ifn = os.path.join(self._fvdir,'%s.csv'%fv)
        mat = self._loadcsv(ifn)
        center = None
        alld = 10000000
        total = float(len(mat))
        handled = 1
        for row in mat:
            vec = self._extvector(row)
            ds = []
            for r in mat:
                if r[0]==row[0] and r[1]==row[1]:
                    continue
                v = self._extvector(r)
                d = ((vec[0]-v[0])**2+(vec[1]-v[1])**2+(vec[2]-v[2])**2+(vec[3]-v[3])**2+(vec[4]-v[4])**2)**0.5
                ds.append(d)
            dsum = sum(ds)
            if dsum<alld:
                alld = dsum
                center = row
            logger.info('dxbase learn handle progress[%0.2f%%] fv[%s]....'%(100*(handled/total),fv))
            handled = handled+1
        ofn = os.path.join(slef._fvdir,'centers.csv')
        dev = alld/float(len(mat)-1)
        f = open(ofn,'a')
        f.write('%s,%0.4f,%s,%s,%s,%s,%s,%s,%s\n'%(center[-1],dev,center[0],center[1],center[2],center[3],center[4],center[5],center[6]))
        f.close()
        logger.info('dxbase learn fv[%s] handle done....'%fv)

    def learn_ev(self):
        g_logger.info('dxbase learn_ev handle start....')
        idir = self._fvdir
        files = os.listdir(idir)
        files.sort()
        fmt = []
        for fn in files:
            if fn.strip()=='centers.csv':
                continue
            ifn = os.path.join(idir,fn.strip())
            fv = fn.strip()[:5]
            mat = self._loadcsv(ifn)
            center = None
            total = float(len(mat))
            handled = 1
            openlis = []
            highlis = []
            lowlis = []
            closelis = []
            volwylis = []
            prog = 0.0
            for row in mat:
                vec = self._extvector(row)
                openlis.append(vec[0])
                highlis.append(vec[1])
                lowlis.append(vec[2])
                closelis.append(vec[3])
                volwylis.append(vec[4])
                pg = 100*(handled/total)
                if pg-prog>1: 
                    g_logger.info('dxbase learn_ev handle progress[%0.2f%%] file[%s]....'%(pg,ifn))
                    prog = pg
                handled = handled+1
            oev = sum(openlis)/float(len(openlis))
            hev = sum(highlis)/float(len(highlis))
            lev = sum(lowlis)/float(len(lowlis))
            cev = sum(closelis)/float(len(closelis))
            vev = sum(volwylis)/float(len(volwylis))
            ds = []
            for row in mat:
                vec = self._extvector(row)
                d = ((vec[0]-oev)**2+(vec[1]-hev)**2+(vec[2]-lev)**2+(vec[3]-cev)**2+(vec[4]-vev)**2)**0.5
                ds.append(d)
            dev = sum(ds)/float(len(mat))
            fmt.append((fv,'%0.4f'%dev,'%0.4f'%oev,'%0.4f'%hev,'%0.4f'%lev,'%0.4f'%cev,'%0.4f'%vev))
        ofn = os.path.join(self._fvdir,'centers_ev.csv')
        self._dumpfile(ofn,fmt)
        g_logger.info('dxbase learn_ev  handle done....')

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-g', '--generate', action='store_true', dest='generate',default=False, help='generate attr and base from data')
    parser.add_option('-p', '--split', action='store_true', dest='split',default=False, help='split for base')
    parser.add_option('-l', '--learn', action='store_true', dest='learn',default=False, help='learn for base')
    parser.add_option('-v', '--fv', action='store', dest='fv',default=None, help='learn for fv')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    ik = iksetup()
    if ops.generate:
        ik.generate_base()
    if ops.split:
        ik.split_fv()
    if ops.learn:
        ik.learn_ev()
    
    
    
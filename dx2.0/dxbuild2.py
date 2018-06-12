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
g_logger = logging.getLogger('dx2')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'dx2.log')
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
        
    def kval(self):
        if self.close>self.open:
            return 1
        return 0
    
    def opensrc(self):
        if self.high!=self.low:
            return (self.open-self.low)/(self.high-self.low)
        return 0.5

    def closesrc(self):
        if self.high!=self.low:
            return (self.close-self.low)/(self.high-self.low)
        return 0.5

class attrdata:
    def __init__(self):
        self.code =''
        self.date =''
        self.hb  = 0
        self.lb = 0
        self.k = 0
        self.stdzdf = 0
        self.stdzf = 0
        self.stdcsrc = 0
        self.stdvolwy = 0
        self.usebase = 0
        self.wonder = None

    def fv(self):
        return '%d%d%d'%(self.hb,self.lb,self.k)

    def linar(self):
        return '%s,%s,%s,%0.4f,%0.4f,%0.4f,%0.4f'%(self.code,self.date,self.fv(),self.stdzdf,self.stdzf,self.stdcsrc,self.stdvolwy)
        
    def connect(self):
        return '%s,%s,%s,%0.4f,%0.4f,%0.4f,%0.4f,%d,%d,%d,%d,%d'%(self.code,self.date,self.fv(),self.stdzdf,self.stdzf,self.stdcsrc,self.stdvolwy,self.wonder.hb,self.wonder.lb,self.wonder.k,self.wonder.hp,self.wonder.lp)

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
    def __init__(self,ddir,bdir):
        self._minusefullength=360
        self._minlength=60
        self._defaultstart = '2005-01-01'
        self._datadir = ddir
        self._basedir = bdir
        if not os.path.isdir(bdir):
            os.makedirs(bdir)

    def __del__(self):
        pass
        
    def execmd(self,cmd):
        status,output = commands.getstatusoutput(cmd)
        g_logger.info('execute command[%s],status[%d],output[%s]'%(cmd,status,output.strip()))
        return status
        
    def _importdata(self,csvfn,tabname,db='dx'):
        sfn = os.path.join(os.path.join(g_home,'tmp'),'%s.sql'%tabname)
        sql = "load data infile '%s' into table %s fields terminated by ',' optionally enclosed by \'\"\' escaped by \'\"\'  lines terminated by '\\n';"%(csvfn,tabname)
        f = open(sfn,'w')
        f.write('%s'%sql)
        f.close()
        cmd = 'mysql -u root -p123456 %s < %s'%(db,sfn)
        return self.execmd(cmd)

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
        k = 1
        if cur.close>cur.open:
            k = 2
        elif cur.close<cur.open:
            k = 0
        return (hb,lb,k)

    def _stdv(self,lis):
        ev = sum(lis)/float(len(lis))
        all = 0
        for item in lis:
            all = all + (item-ev)**2
        std = all**0.5
        stdv = (lis[0]-ev)/std
        return stdv
        
    def _transfer(self,data):
        zdfmat = []
        zfmat = []
        csrcmt = []
        volwymt = []
        for i in range(1,len(data)):
            yc = data[i-1].close
            open = data[i].open
            high = data[i].high
            low = data[i].low
            close = data[i].close
            volwy = data[i].volwy
            zdf = (close-yc)/yc
            zf = (high-low)/yc
            csrc = 0.5
            if high!=low:
                csrc = (close-low)/(high-low)
            zdfmat.append(zdf)
            zfmat.append(zf)
            csrcmt.append(csrc)
            volwymt.append(volwy)
        return (zdfmat,zfmat,csrcmt,volwymt)

    def _moreinfo(self,data):
        tmats = self._transfer(data)
        stdzdf =  self._stdv(tmats[0])
        stdzf =  self._stdv(tmats[1])
        stdcsrc =  self._stdv(tmats[2])
        stdvolwy =  self._stdv(tmats[3])
        return (stdzdf,stdzf,stdcsrc,stdvolwy)

    def _poles(self,cur,prev,next):
        hp = 0
        lp = 0
        if (cur.high>prev.high) and (cur.high>next.high):
            hp = 1
        if (cur.low<prev.low) and (cur.low<next.low):
            lp = 1
        return (hp,lp)

    def _genattr(self,need):
        info = self._basek(need[-1],need[-2])
        mi = self._moreinfo(need)
        attr = attrdata()
        attr.code = need[-1].code
        attr.date = need[-1].date
        attr.hb  = info[0]
        attr.lb = info[1]
        attr.k = info[2]
        attr.stdzdf = mi[0]
        attr.stdzf = mi[1]
        attr.stdcsrc = mi[2]
        attr.stdvolwy = mi[3]
        return attr

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

    def _dumpbase(self,mat,filename):
        f = open(filename,'w')
        for attr in mat:
            f.write(u'%s\n'%attr.connect())
        f.close()

    def setup(self):
        g_logger.info('dx2 setup handle start....')
        print 'dx setup handle start....'
        indir = self._datadir
        basedir = self._basedir
        files = os.listdir(indir)
        files.sort()
        total = float(len(files))
        handled = 1
        for fn in files:
            baseofn = os.path.join(basedir,fn.strip())
            ffn = os.path.join(indir,fn.strip())
            g_logger.info('dx setup deal with file[%s]'%ffn)
            mat = self._csv2kdata(ffn)
            amt = []
            if len(mat)<=self._minusefullength:
                handled = handled+1
                continue
            for i in range(self._minusefullength,len(mat)-2):
                if mat[i].date<self._defaultstart:
                    continue
                need = mat[i-self._minlength:i+1]
                attr = self._genattr(need)
                wonder = self._genwonder(mat[i+1],mat[i],mat[i+2])
                if (mat[i+1].low-mat[i].close)/mat[i].close<=-0.101:
                    continue
                attr.wonder = wonder
                amt.append(attr)
            self._dumpbase(amt,baseofn)
            g_logger.info('dx setup handle progress[%0.2f%%] file[%s]....'%(100*(handled/total),fn.strip()))
            handled = handled+1
        print 'dx setup handle done....'
        g_logger.info('dx setup handle done....')

    def _inputdir(self,dir,dbname,tabname):
        files = os.listdir(dir)
        files.sort()
        for fn in files:
            fn = fn.strip()
            self._importdata(os.path.join(dir,fn),tabname,dbname)
            g_logger.info('import db[%s] table[%s] file[%s]...'%(dbname,tabname,fn))

    def importdb(self):
        basedir = self._basedir
        self._inputdir(basedir,'dx','iknow_base2')

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-g', '--generate', action='store_true', dest='generate',default=False, help='generate attr and base from data')
    parser.add_option('-s', '--savedb', action='store_true', dest='savedb',default=False, help='savedb for base')
    parser.add_option('-i', '--input', action='store', dest='input',default=None, help='data dir')
    parser.add_option('-o', '--output', action='store', dest='output',default=None, help='output dir')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    if ops.input and ops.output:
        bdir = ops.output
        ik = iksetup(ops.input,bdir)
        if ops.generate:
            ik.setup()
        if ops.savedb:
            ik.importdb()
    
    
    
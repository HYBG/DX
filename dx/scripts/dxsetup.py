#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil

g_iu = ikutil()

class iksetup:
    def __init__(self):
        self._minlength=360
        self._defaultstart = '2005-01-01'

    def __del__(self):
        pass

    def _baseattr(self,currow,lastrow,beforerow):
        CODE = 0
        DATE = 1
        OPEN = 2
        HIGH = 3
        LOW = 4
        CLOSE = 5
        VOLH = 6
        openzdf = (currow[OPEN]-lastrow[CLOSE])/lastrow[CLOSE]
        highzdf = (currow[HIGH]-lastrow[CLOSE])/lastrow[CLOSE]
        lowzdf = (currow[LOW]-lastrow[CLOSE])/lastrow[CLOSE]
        closezdf = (currow[CLOSE]-lastrow[CLOSE])/lastrow[CLOSE]
        osrc = 0.5
        csrc = 0.5
        if currow[HIGH]!=currow[LOW]:
            osrc = (currow[OPEN]-currow[LOW])/(currow[HIGH]-currow[LOW])
            csrc = (currow[CLOSE]-currow[LOW])/(currow[HIGH]-currow[LOW])
        hb = 0
        lb = 0
        if currow[HIGH] > lastrow[HIGH]:
            hb = 1
        if currow[LOW] < lastrow[LOW]:
            lb = 1
        k = 0
        if currow[CLOSE]>currow[OPEN]:
            k = 1
        vol = (currow[CLOSE]-currow[OPEN])*currow[VOLH]
        yvol = (lastrow[CLOSE]-lastrow[OPEN])*lastrow[VOLH]
        bvol = (beforerow[CLOSE]-beforerow[OPEN])*beforerow[VOLH]
        v1 = 0
        if (vol-yvol)>0:
            v1 = 1
        v2 = 0
        if (vol+bvol-2*yvol)>0:
            v2 = 1
        useful = 1
        if lowzdf<=-0.11:
            useful = 0
        return ('%0.4f'%openzdf,'%0.4f'%highzdf,'%0.4f'%lowzdf,'%0.4f'%closezdf,hb,lb,k,v1,v2,useful)
        
    def _stdv(self,lis):
        ev = sum(lis)/float(len(lis))
        all = 0
        for item in lis:
            all = all + (item-ev)**2
        std = all**0.5
        stdv = (lis[0]-ev)/std
        return stdv
        
    def _transfer(self,data):
        OPEN = 2
        HIGH = 3
        LOW = 4
        CLOSE = 5
        zdfmat = []
        zfmat = []
        osrcmt = []
        csrcmt = []
        for i in range(1,len(data)):
            yc = data[i-1][5]
            open = data[i][2]
            high = data[i][3]
            low = data[i][4]
            close = data[i][5]
            zdf = (close-yc)/yc
            zf = (high-low)/yc
            osrc = 0.5
            csrc = 0.5
            if high!=low:
                osrc = (open-low)/(high-low)
                csrc = (close-low)/(high-low)
            zdfmat.append(zdf)
            zfmat.append(zf)
            osrcmt.append(osrc)
            csrcmt.append(csrc)
        return (zdfmat,zfmat,osrcmt,csrcmt)
        
    def _divstd(self,stdv):
        div = 2
        if stdv<-0.43:
            div = 1
        elif stdv>0.43:
            div = 3
        return div
        
    def _moreinfo(self,data):
        tmats = self._transfer(data)
        divstdzdf =  self._divstd(self._stdv(tmats[0]))
        divstdzf =  self._divstd(self._stdv(tmats[1]))
        divstdosrc =  self._divstd(self._stdv(tmats[2]))
        divstdcsrc =  self._divstd(self._stdv(tmats[3]))
        return (divstdzdf,divstdzf,divstdosrc,divstdcsrc)
        
    def _poles(self,row,prev,next):
        HIGH = 3
        LOW = 4
        hp = 0
        lp = 0
        if (row[HIGH]>prev[HIGH]) and (row[HIGH]>next[HIGH]):
            hp = 1
        if (row[LOW]<prev[LOW]) and (row[LOW]<next[LOW]):
            lp = 1
        return (hp,lp)

    def setup(self):
        g_iu.log(logging.INFO,'dx setup handle start....')
        indir = '/var/data/iknow/save'
        attrdir = '/var/data/iknow/attr2'
        basedir = '/var/data/iknow/base2'
        g_iu.mkdir(attrdir)
        g_iu.mkdir(basedir)
        files = os.listdir(indir)
        files.sort()
        total = float(len(files))
        handled = 1
        for fn in files:
            attrofn = os.path.join(attrdir,fn.strip())
            baseofn = os.path.join(basedir,fn.strip())
            ffn = os.path.join(indir,fn.strip())
            mat = g_iu.loadcsv(ffn,{2:type(1.0),3:type(1.0),4:type(1.0),5:type(1.0),6:type(1.0),7:type(1.0)})
            amt = []
            bmt = []
            if len(mat)<=self._minlength:
                handled = handled+1
                continue            
            for i in range(self._minlength,len(mat)-1):
                if mat[i][1]<self._defaultstart:
                    continue
                info = self._baseattr(mat[i],mat[i-1],mat[i-2])
                need = mat[i-120:i+1]
                mi = self._moreinfo(need)
                poles = self._poles(mat[i],mat[i-1],mat[i+1])
                amt.append((mat[i][0],mat[i][1])+info+mi+poles)
            g_iu.dumpfile(attrofn,amt)
            for i in range(len(amt)-1):
                fv = '%d%d%d%d%d'%(amt[i][6],amt[i][7],amt[i][8],amt[i][9],amt[i][10])
                bmt.append((amt[i][0],amt[i][1],fv,amt[i][12],amt[i][13],amt[i][14],amt[i][15],amt[i+1][6],amt[i+1][7],amt[i+1][8],amt[i+1][16],amt[i+1][17],amt[i+1][2],amt[i+1][3],amt[i+1][4],amt[i+1][5]))
            g_iu.dumpfile(baseofn,bmt)
            g_iu.log(logging.INFO,'dx setup handle progress[%0.2f%%] file[%s]....'%(100*(handled/total),fn.strip()))
            handled = handled+1
        g_iu.log(logging.INFO,'dx setup handle done....')
        
    def _inputdir(self,dir,dbname,tabname):
        files = os.listdir(dir)
        for fn in files:
            fn = fn.strip()
            g_iu.importdata(os.path.join(dir,fn),tabname,dbname)
            g_iu.log(logging.INFO,'import db[%s] table[%s] file[%s]...'%(dbname,tabname,fn))
        
    def importdb(self):
        attrdir = '/var/data/iknow/attr2'
        basedir = '/var/data/iknow/base2'
        self._inputdir(attrdir,'dx','iknow_attr2')
        self._inputdir(basedir,'dx','iknow_base2')

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-g', '--generate', action='store_true', dest='generate',default=False, help='generate attr and base from data')
    parser.add_option('-i', '--importdb', action='store_true', dest='importdb',default=False, help='importdb for attr and base')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    ik = iksetup()
    if ops.generate:
        ik.setup()
    if ops.importdb:
        ik.importdb()
    
    
    
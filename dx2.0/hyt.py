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
from bs4 import BeautifulSoup
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil
from iktool import iktool

g_iu = ikutil()
g_tool = iktool()

def his(fn,outfv,outkd,outmd):
    dicf = {}
    dickd = {}
    dicmd = {}
    mat = g_iu.loadcsv(fn,{2:type(1.0),3:type(1),4:type(1),5:type(1),6:type(1.0),7:type(1.0),8:type(1.0)})
    for row in mat:
        print 'fn[%s] code[%s] date[%s]'%(fn,row[0],row[1])
        fv = row[3]
        kdv = row[4]
        mdv = row[5]
        vr = row[2]
        if dicf.has_key(fv):
            dicf[fv].append(vr)
        else:
            dicf[fv] = [vr]
        if dickd.has_key(kdv):
            dickd[kdv].append(vr)
        else:
            dickd[kdv] = [vr]
        if dicmd.has_key(mdv):
            dicmd[mdv].append(vr)
        else:
            dicmd[mdv] = [vr]
    matf = []
    for k in dicf.keys():
        vrlis = dicf[k]
        vrlis.sort()
        print 'fn[%s] fv[%d] count[%d]'%(fn,k,len(dicf[k]))
        matf.append((k,len(dicf[k]),vrlis[-1],vrlis[0],vrlis[len(vrlis)/2]))
    matf.sort(reverse=True,key=lambda x:x[1])
    g_iu.dumpfile(os.path.join(os.path.join(g_home,'tmp'),outfv),matf)

    matkd = []
    for k in dickd.keys():
        vrlis = dickd[k]
        vrlis.sort()
        print 'fn[%s] kdv[%d] count[%d]'%(fn,k,len(dickd[k]))
        matkd.append((k,len(dickd[k]),vrlis[-1],vrlis[0],vrlis[len(vrlis)/2]))
    matkd.sort(reverse=True,key=lambda x:x[1])
    g_iu.dumpfile(os.path.join(os.path.join(g_home,'tmp'),outkd),matkd)

    matmd = []
    for k in dicmd.keys():
        vrlis = dicmd[k]
        vrlis.sort()
        print 'fn[%s] mdv[%d] count[%d]'%(fn,k,len(dicmd[k]))
        matmd.append((k,len(dicmd[k]),vrlis[-1],vrlis[0],vrlis[len(vrlis)/2]))
    matmd.sort(reverse=True,key=lambda x:x[1])
    g_iu.dumpfile(os.path.join(os.path.join(g_home,'tmp'),outmd),matmd)

def clean(filename,output):
    mat = g_iu.loadcsv(filename,{2:type(1.0),3:type(1),4:type(1),5:type(1),6:type(1.0),7:type(1.0),8:type(1.0)})
    nwt = []
    for row in mat:
        if (row[1]>'2005-12-06' and row[1]<'2008-11-04') or (row[1]>'2014-03-20' and row[1]<'2016-01-27'):
            continue 
        nwt.append(row)
    fn = os.path.join(os.path.join(g_home,'tmp'),output)
    g_iu.dumpfile(fn,nwt)

if __name__ == "__main__":


    g_tool.conn('hyik')
    fnh = os.path.join(os.path.join(g_home,'tmp'),'high.csv')
    fnl = os.path.join(os.path.join(g_home,'tmp'),'low.csv')
    '''codes = g_tool.exesqlbatch('select distinct code from ik_tags',None)
    for code in codes:
        code = code[0]
        math = []
        matl = []
        data = g_tool.exesqlbatch('select date,highr,lowr,csrc from ik_future where code=%s and nextn=7',(code,))
        print 'dealing with code[%s]...'%code
        for i in range(1,len(data)-1):
            if abs(data[i][1]-data[i][2])>10:
                if (data[i][2]<data[i-1][2] and data[i][2]<data[i+1][2]) or (data[i][1]>data[i-1][1] and data[i][1]>data[i+1][1]):
                    if data[i][2]<-5 and data[i][1]!=0 and abs(data[i][2]/data[i][1])>3:
                        feat = g_tool.exesqlone('select vr,fv4,kdv3,macdv3 from ik_feature where code=%s and date=%s',(code,data[i][0]))
                        if len(feat)!=0 and feat[0]:
                            math.append((code,data[i][0],feat[0],feat[1],feat[2],feat[3],data[i][1],data[i][2],data[i][3]))
                if (data[i][2]>data[i-1][2] and data[i][2]>data[i+1][2]) or (data[i][1]<data[i-1][1] and data[i][1]<data[i+1][1]):
                    if data[i][1]>5 and data[i][2]!=0 and abs(data[i][1]/data[i][2])>3:
                        feat = g_tool.exesqlone('select vr,fv4,kdv3,macdv3 from ik_feature where code=%s and date=%s',(code,data[i][0]))
                        if len(feat)!=0 and feat[0]:
                            matl.append((code,data[i][0],feat[0],feat[1],feat[2],feat[3],data[i][1],data[i][2],data[i][3]))
        g_iu.appendmat(fnh,math)
        g_iu.appendmat(fnl,matl)'''
    
    clean(fnl,'low_c.csv')
    clean(fnh,'high_c.csv')
    
    #his(fnl,'fvlow.csv','kdlow.csv','mdlow.csv')
    #his(fnh,'fvhigh.csv','kdhigh.csv','mdhigh.csv')
    
    
            



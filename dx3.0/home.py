#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import string
import re
import datetime
from optparse import OptionParser
reload(sys)
sys.setdefaultencoding('utf-8')

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-f', '--file', action='store', dest='file',default=None, help='input filename')
    parser.add_option('-o', '--output', action='store', dest='output',default=None, help='output filename')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)
        
    if ops.file and ops.output:
        f = open(ops.file,'r')
        lines = f.readlines()
        f.close()
        dic = {}
        block = None
        blis = []
        for line in lines:
            line = line.strip()
            if len(line)==0:
                continue
            items = line.split(',')
            if len(items)==1:
                dic[items[0]] = []
                block = items[0]
                blis.append(items[0])
            elif len(items)==2:
                dic[block].append((items[0],items[1]))

        body = ''
        for blk in blis:
            length = len(dic[blk])
            rows = length/6
            if length%6 != 0:
                rows = length/6 + 1
            trs = ''
            for i in range(rows):
                b = ''
                for j in range(6):
                    if i*6+j<length:
                        b = b + '<th><span class="item"><a href="%s" target="_blank">%s</a></span></th>'%(dic[blk][i*6+j][1].strip(),dic[blk][i*6+j][0])
                    #else:
                    #    b = b + '<th><span class="item"></span></th>'
                tr = '<tr>%s</tr>'%b
                trs = trs + tr
            block = '<h2>%s</h2><table width="800" height="80" border="1">%s</table>'%(blk,trs)
            body = body + block
        txt = '<html xmlns="http://www.w3.org/1999/xhtml"><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/><title>汉尧科技</title><style type="text/css">.item {font-size: 24px}</style></head><body><h1>HY Tech</h1>%s</body></html>'%body
        f = open(ops.output,'w')
        f.write('%s\n'%txt)
        f.close()

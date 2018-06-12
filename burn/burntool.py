#!/usr/bin/python

import os
import sys
import string
import re
import datetime
import time
import math
import urllib2
import commands
from PIL import Image
from optparse import OptionParser


if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-i', '--input', action='store', dest='input',default=None, help='input dir')
    parser.add_option('-o', '--output', action='store', dest='output',default=None, help='output dir')
    parser.add_option('-w', '--width', action='store', type='int', dest='width',default=None, help='width')
    parser.add_option('-H', '--height', action='store', type='int', dest='height',default=None, help='height')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    if ops.input and ops.output and ops.width and ops.height:
        files = os.listdir(ops.input)
        if os.path.isdir(ops.output):
            status,output = commands.getstatusoutput('rm -fr %s'%ops.output)
        os.makedirs(ops.output)
        files.sort()
        for fn in files:
            fn = fn.strip()
            format = fn.split('.')[1]
            ffn = os.path.join(ops.input,fn)
            im = Image.open(ffn)
            out = im.resize((ops.width,ops.height))
            ofn = os.path.join(ops.output,fn)
            out.save(ofn,format)


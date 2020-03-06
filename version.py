import fileinput
import os
import re
import sys

parts = sys.argv[1].replace('v', '').split('.')
dir = os.path.dirname(os.path.realpath(__file__))

with fileinput.FileInput(dir + '/zigpy_cc/__init__.py', inplace=True, backup='.bak') as file:
    for line in file:
        line = re.sub(r'(MAJOR_VERSION =).*', '\\1 ' + parts[0], line)
        line = re.sub(r'(MINOR_VERSION =).*', '\\1 ' + parts[1], line)
        line = re.sub(r'(PATCH_VERSION =).*', '\\1 ' + parts[2], line)
        print(line, end='')

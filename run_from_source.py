#!/usr/bin/env python

import sys
from os.path import join, dirname, realpath

base_path = dirname(realpath(__file__))
source_path = join(base_path, "src", "main", "python")
script_path = join(base_path, "src", "main", "scripts", "cf")

sys.path.insert(0, source_path)
exec(open(script_path, 'r').read())

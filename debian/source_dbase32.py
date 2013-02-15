"""
Apport package hook for dbase32 (requires Apport 2.5 or newer).

(c) 2013 Novacut Inc
Author: Jason Gerard DeRose <jderose@novacut.com>
"""

def add_info(report):
    report['CrashDB'] = "{'impl': 'launchpad', 'project': 'dbase32'}"


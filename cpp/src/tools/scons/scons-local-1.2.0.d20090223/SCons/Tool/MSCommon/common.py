#
# Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009 The SCons Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__revision__ = "src/engine/SCons/Tool/MSCommon/common.py 4043 2009/02/23 09:06:45 scons"

__doc__ = """
Common helper functions for working with
"""

import copy
import os
import subprocess
import re

import SCons.Util

logfile = os.environ.get('SCONS_MSCOMMON_DEBUG')
if logfile:
    try:
        import logging
    except ImportError:
        debug = lambda x: open(logfile, 'a').write(x + '\n')
    else:
        logging.basicConfig(filename=logfile, level=logging.DEBUG)
        debug = logging.debug
else:
    debug = lambda x: None


# TODO(sgk): unused
def is_win64():
    """Return true if running on windows 64 bits."""
    # Unfortunately, python does not seem to have anything useful: neither
    # sys.platform nor os.name gives something different on windows running on
    # 32 bits or 64 bits. Note that we don't care about whether python itself
    # is 32 or 64 bits here
    value = "Software\Wow6432Node"
    yo = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, value)[0]
    if yo is None:
        return 0
    else:
        return 1


def read_reg(value):
    return SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, value)[0]

# Functions for fetching environment variable settings from batch files.


def normalize_env(env, keys):
    """Given a dictionary representing a shell environment, add the variables
    from os.environ needed for the processing of .bat files; the keys are
    controlled by the keys argument.

    It also makes sure the environment values are correctly encoded.

    Note: the environment is copied"""
    normenv = {}
    if env:
        for k in env.keys():
            normenv[k] = copy.deepcopy(env[k]).encode('mbcs')

        for k in keys:
            if os.environ.has_key(k):
                normenv[k] = os.environ[k].encode('mbcs')

    return normenv


def get_output(vcbat, args=None, env=None):
    """Parse the output of given bat file, with given args."""
    if args:
        debug("Calling '%s %s'" % (vcbat, args))
        popen = subprocess.Popen('"%s" %s & set' % (vcbat, args),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 env=env)
    else:
        debug("Calling '%s'" % vcbat)
        popen = subprocess.Popen('"%s" & set' % vcbat,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 env=env)

    # Use the .stdout and .stderr attributes directly because the
    # .communicate() method uses the threading module on Windows
    # and won't work under Pythons not built with threading.
    stdout = popen.stdout.read()
    if popen.wait() != 0:
        raise IOError(popen.stderr.read().decode("mbcs"))

    output = stdout.decode("mbcs")
    return output


def parse_output(output, keep=("INCLUDE", "LIB", "LIBPATH", "PATH")):
    # dkeep is a dict associating key: path_list, where key is one item from
    # keep, and pat_list the associated list of paths

    # TODO(1.5):  replace with the following list comprehension:
    #dkeep = dict([(i, []) for i in keep])
    dkeep = dict(map(lambda i: (i, []), keep))

    # rdk will  keep the regex to match the .bat file output line starts
    rdk = {}
    for i in keep:
        rdk[i] = re.compile('%s=(.*)' % i, re.I)

    def add_env(rmatch, key):
        plist = rmatch.group(1).split(os.pathsep)
        for p in plist:
            # Do not add empty paths (when a var ends with ;)
            if p:
                p = p.encode('mbcs')
                # XXX: For some reason, VC98 .bat file adds "" around the PATH
                # values, and it screws up the environment later, so we strip
                # it.
                p = p.strip('"')
                dkeep[key].append(p)

    for line in output.splitlines():
        for k, v in rdk.items():
            m = v.match(line)
            if m:
                add_env(m, k)

    return dkeep


# TODO(sgk): unused
def output_to_dict(output):
    """Given an output string, parse it to find env variables.

    Return a dict where keys are variables names, and values their content"""
    envlinem = re.compile(r'^([a-zA-z0-9]+)=([\S\s]*)$')
    parsedenv = {}
    for line in output.splitlines():
        m = envlinem.match(line)
        if m:
            parsedenv[m.group(1)] = m.group(2)
    return parsedenv


# TODO(sgk): unused
def get_new(l1, l2):
    """Given two list l1 and l2, return the items in l2 which are not in l1.
    Order is maintained."""

    # We don't try to be smart: lists are small, and this is not the bottleneck
    # is any case
    new = []
    for i in l2:
        if i not in l1:
            new.append(i)

    return new

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:

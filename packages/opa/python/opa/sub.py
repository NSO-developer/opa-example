# -*- mode: python; python-indent: 4 -*-

#
# opa-example: This code is modified from examples.ncs/getting-started/developing-with-ncs/1-cdb-py/packages/cdb/python/plaincdbsub/plaincdbsub.py
#    The interesting part is the method send_data which is the integration towards opa.
#

import _ncs
import _ncs.cdb as cdb
import _ncs.maapi as maapi
from ncs_pyvm import NcsPyVM
import sys

import json
import socket
import threading
import opa
_schemas_loaded = False

# This low level cdb subscriber subscribes to changes under the path
# /devices/device{ex0}/config
# Whenever a change occurs there, the code iterates through the
# change and prints the values. Thus to trigger this subscription code
# go into the ncs_cli and commit any change under the subscription
# path. For example:

# ncs_cli -u admin
# admin connected from 127.0.0.1 using console on iron.local
# admin@iron> configure
# dmin@iron% set devices device ex0 config sys syslog server 4.5.6.7 enabled
# [ok][2012-07-05 12:57:59]

# [edit]
# admin@iron% commit
# Commit complete.

# will trigger the subscription code, the code logs and the data will end up
# in ./logs/ncs-python-vm-cdb.log (relative to where the ncs daemon executes)

# The code runs in an 'application' component, it implements
# the ApplicationComponent interface, this includes the run() method
# so the code will run in a Thread.

def recv_all_and_close(c_sock, c_id):
    data = ''
    while True:
        buf = c_sock.recv(4096)
        if buf:
            data += buf.decode('utf-8')
        else:
            c_sock.close()
            return data

def read_config(m, th, path):
    dev_flags= (_ncs.maapi.CONFIG_JSON)
    c_id = _ncs.maapi.save_config(m, th, dev_flags, path)
    c_sock = socket.socket()
    (ncsip, ncsport) = m.getpeername()
    _ncs.stream_connect(c_sock, c_id, 0, ncsip, ncsport)
    data=recv_all_and_close(c_sock, c_id);
    return data


class Subscriber(object):
    def __init__(self, prio, path, debug):
        self.sock = socket.socket()
        self.sock = socket.socket()
        self.path = path
        self.debug = debug
        self.prio = prio
        global _schemas_loaded

        self.ms = socket.socket()
        maapi.connect(sock=self.ms, ip='127.0.0.1',
                      port=_ncs.NCS_PORT)
        if _schemas_loaded is False:
            maapi.load_schemas(self.ms)
            _schemas_loaded = True

        maapi.start_user_session(self.ms, 'admin', 'test', [], '127.0.0.1', _ncs.PROTO_TCP)
        self.th = maapi.start_trans(self.ms, _ncs.RUNNING, _ncs.READ)
        cdb.connect(self.sock, type=cdb.DATA_SOCKET, ip='127.0.0.1',
                    port=_ncs.NCS_PORT, path=self.path)
        self.subid = cdb.subscribe(self.sock, self.prio, 0, self.path)
        cdb.subscribe_done(self.sock)
        self.debug("Subscription {0}, subscribed to {1}".format(self.subid,
                                                                self.path))

    def wait(self):
        cdb.read_subscription_socket(self.sock)

    def ack(self):
        cdb.sync_subscription_socket(self.sock, cdb.DONE_PRIORITY)

    def send_data(self):
        # This sends all data in /topology to opa to be placed as base documents under /topology
        # The implementation is simple and always sends the entire topology, a more efficient implementation
        # would send only the updates.
        try:
            cr = read_config(self.ms, self.th, "/topology")            
            j = json.loads(cr)
            j = j['data']['l3vpn:topology']
            self.debug("Sending to OPA: " + json.dumps(j))
            r= opa.send_to_opa('topoology', j)
            self.debug("Result from OPA : {} {}".format(r,r.text))
        except Exception,e:
            self.debug("Error: {} {}".format(e, sys.exc_info()[0]))

    def diff_iter_loop(self):
        while True:
            self.send_data()
            self.wait()
            self.ack()
    def close(self):
        cdb.end_session(self.sock)
        cdb.close(self.sock)


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------

class Sub(object):
    def __init__(self, *args, **kwds):
        # Setup the NCS object, containing mechanisms
        # for communicating between NCS and this User code.
        self._ncs = NcsPyVM(*args, **kwds)
        self.debug('--- Service INIT OBJECT')
        # Register our 'finish' callback
        self._finish_cb = lambda: self.finish()

        self.sub = Subscriber(prio=100,
                              path="/topology",
                              debug=self.debug)

        self._ncs.reg_finish(self._finish_cb)

        self._stopevent = threading.Event()

    # This method is supposed to start the User application
    def run(self):
        self.debug('Running diff iter loop')
        self.sub.diff_iter_loop()

    # Just a convenient logging function
    def debug(self, line):
        self._ncs.debug(line)

    # Callback that will be invoked by NCS when the system is shutdown.
    # Make sure to shutdown the User code, including any User created threads.
    def finish(self):
        self.debug(' PlainSub in finish () =>\n')
        self.sub.close()
        self._stopevent.set()
        self.debug(' PlainSub in finish () => ok\n')

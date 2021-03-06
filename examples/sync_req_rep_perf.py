#------------------------------------------------------------------
# Test for synchronous client behaviour using DEALER-ROUTER pattern
#
#

import sys
sys.path.append("..")

import multiprocessing
import time
import json
import handlers
import moebius
from moebius.constants import STRATEGY_QUEUE


class Timer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            print 'elapsed time: %f ms' % self.msecs


#-------------------------------------------------------------
# specific client which is derived from basic REQ/REP client
#
class Client(moebius.utils.ReqRepClient):
    def send(self, message):
        super(Client, self).send(message=message)

    def on_recv(self, message):
        print message
        exit(0)


def start_server(port):

    rules = [
        {
            'command': 'reply',
            'handler': (STRATEGY_QUEUE, handlers.ReplyHandlerEchoNoWait)
        }
    ]
    router = moebius.ZMQRouter(rules)
    srv = moebius.ZMQServer('tcp://127.0.0.1:%s' % port, router, 1)
    print 'Server started'
    srv.start()


def start_sync_client_strategy(port, id):
    cl = Client(
        address='tcp://127.0.0.1:%s' % port,
        identity='Client%s' % id
    )
    message = {
        'command': 'reply'
    }
    cl.connect()
    print "Send message by %s" % cl.id
    m = json.dumps(message)

    cnt = 10000
    with Timer() as t:
        for i in range(cnt):
            cl.send_with_reply(m)
    print "=> elasped time is: %s s" % t.secs
    print "=> performance (q/s): %d" % (cnt / t.secs)
    #print reply


if __name__ == "__main__":
    port = 19876

    cnt = 0
    if len(sys.argv) > 1:
        cnt = int(sys.argv[1])
    if cnt <= 0:
        cnt = 1

    s = multiprocessing.Process(target=start_server, args=(port,))
    s.start()
    child = []

    for i in xrange(cnt):
        child.append(
            multiprocessing.Process(
                target=start_sync_client_strategy,
                args=(port, i,)))
        child[i].start()

    for i in xrange(cnt):
        child[i].join()

    s.terminate()

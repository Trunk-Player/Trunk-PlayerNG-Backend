import gevent.monkey

gevent.monkey.patch_all()
from trunkplayer_ng.mqtt import GeventMqttExample, launch


import multiprocessing
from psycogreen.gevent import patch_psycopg
from django_db_geventpool.utils import close_connection


# import logging

# logger = logging.getLogger(__name__)

bind = "0.0.0.0:42069"
keep_alive=5

workers = 1
worker_class = 'gevent'
# threads = 500

limit_request_fields=10000

user=1000
group=1000

timeout=300
graceful_timeout=120

max_requests=150000

wsgi_app='trunkplayer_ng.wsgi'


def post_fork(server, worker):
    patch_psycopg()
    worker.log.info("Monkey Patched Thread 🙊")

@close_connection
def foo_func():
    #logger.debug("[-] DB CONN CLOSED")
    ...
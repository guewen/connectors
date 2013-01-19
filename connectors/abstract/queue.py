# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Guewen Baconnier
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
import random
import os
import errno
from Queue import Queue, Empty
from functools import total_ordering  # FIXME only since 2.7
from operator import itemgetter

from openerp.osv import orm, fields
from openerp import pooler
from .session import Session
from .tasks import OpenERPJob, STARTED , QUEUED, DONE, FAILED

_logger = logging.getLogger(__name__)

# TODO implement a memory queue
# on start: take all the pending tasks
# on write of a task: create a task in the queue
# on end of the task: remove it
# warning with multiprocess: only 1 process should
# take the pending tasks


class AbstractQueue(object):

    job_cls = None

    def __init__(self, key):
        """ """

    def enqueue(self, session, func, *args, **kwargs):
        """Put a job in the queue"""

    def dequeue(self, session):
        """ Take the first job from the queue and return it """

    @classmethod
    def dequeue_first(cls, session, queues):
        """ """


class JobsQueue(AbstractQueue):
    """ Implementation """

    job_cls = OpenERPJob

    def __init__(self, key):
        self._key = key
        self._queue = Queue()

    def enqueue(self, session, func, *args, **kwargs):
        """Put a job in the queue"""
        job = self.job_cls.create(session, func, args, kwargs)
        self._queue.put_nowait(job)  # XXX blocking?
        _logger.debug('Job %s enqueued', job)

    def dequeue(self, session):
        """ Take the first job from the queue and return it """
        try:
            job_id = self._queue.get_nowait()
        except Empty as err:
            job_id = None
        if job_id is None:
            return None
        try:
            job = self.job_cls.fetch(session, job_id)
        except:
            # TODO handle:
            # - no job (recall dequeue to continue to the next)
            # - job fetching error
            raise
        _logger.debug('Fetched job %s', job)
        return job

    @classmethod
    def dequeue_first(cls, session, queue_set):
        """
        :param session: `Session`
        :param queue_set: `QueueSet`
        """
        for queue in queue_set:
            job = queue.dequeue(session)
            if job is not None:
                _logger.debug('Dequeued %s from queue %s', job, queue)
                return job, queue
        return None

    def __repr__(self):
        return 'JobsQueue(%r)' % self._key

    def __str__(self):
        return '<JobsQueue \'%s\'>' % self._key


class QueueSet(object):

    def __init__(self, *queues):
        self._queues = set(queues)

    def __iter__(self):
        for queue in self._queues:
            yield queue


class PriorityQueueSet(QueueSet):

    default_priority = 10

    def __init__(self, *queues):
        """ Allows to assign a priority to each queue.
        If a priority is not defined, it uses a default priority with the value
        of `default_priority`.

        :param queues: each arg is a tuple with a queue and a priority
        """
        queues_set = []
        for queue in queues:
            if isinstance(queue, tuple):
                queues_set.append(queue)
            else:
                queues_set.append((queue, self.default_priority))
        self._queues = sorted(queues_set, key=itemgetter(1))

    def __iter__(self):
        """ Introduces some randomization to allow queues with a lower priority
        to be chosen sometimes before a queue with a higher priority.
        The more the difference is great, the less a lower priority will have a
        chance to be chosen.
        """
        queues = list(self._queues)

        ordered_queues = []
        for _ in xrange(len(queues)):
            higher_priority = max(queue[1] for queue in queues)
            rand = random.randint(0, higher_priority)
            queue = next(que for que in queues if que[1] >= rand)
            ordered_queues.append(queue[0])
            queues.remove(queue)

        for queue in ordered_queues:
            yield queue


class Worker(object):

    queue_cls = JobsQueue

    def __init__(self, session, queue_set):
        self.session = session
        self.log = _logger
        self.queue_set = queue_set

    def fork_and_run_job(self, job):
        """ Fork the process and give it a job """
        pid = os.fork()
        if pid == 0:  # child
            self._do_forked(job)
        else:  # parent
            self.log.debug('Forked with pid: %d', pid)
            # XXX [Errno 10] No child processes
            # have to set signal handlers
            # while True:
            #     os.waitpid(pid, 0)

    def _do_forked(self, job):
        """ Child fork stuff """
        random.seed()
        self.log = logging.getLogger('fork')

        success = self._do_forked_job(job)

        # exit the fork
        os._exit(int(not success))

    def _do_forked_job(self, job):
        """ Execute the forked job """
        self.log.debug('Starting job', job)

        try:
            result = job.perform()
            job.set_status(DONE, result=result)
        except:
            # TODO traceback
            job.set_status(FAILED, traceback=None)
            # TODO how to handle the exception?
            return False
        return True

    def work(self):
        """ """
        self.log.info('Start %s', self)
        while True:
            try:
                result = self.queue_cls.dequeue_first(
                        self.session, self.queue_set)
                if result is None:
                    break
            except Exception as err:
                self.log.exception(err)
                # which exceptions and how?
                continue

            job, queue = result
            job.set_status(STARTED)
            self.fork_and_run_job(job)

        self.log.info('Stop %s', self)


def test1(a, b):
    _logger.debug('test1 %s %s', a, b)

def test2(a, b=None):
    _logger.debug('test2 %s %s', a, b)

from openerp.osv import orm

class res_users(orm.Model):
    _inherit = 'res.users'

    def test(self, cr, uid, ids, context=None):
        session = Session(cr,
                          uid,
                          self.pool,
                          self._name,
                          context=context)
        queue1.enqueue(session, test1, ['a', 1])
        queue1.enqueue(session, test1, ['a', 1])
        queue2.enqueue(session, test1, ['b', 1])
        queue2.enqueue(session, test2, ['b'], {'b': 2})
        queue2.enqueue(session, test2, ['b'], {'b': 2})
        Worker(session, PriorityQueueSet((queue1, 10), (queue2, 30))).work()
        return True


queue1 = JobsQueue('queue1')
queue2 = JobsQueue('queue2')


def on_start_queues():
    """ Assign all pending jobs to queues

    Must be called when OpenERP starts.

    Warning: if OpenERP has many processes with Gunicorn only 1 process must
    take the jobs.
    """


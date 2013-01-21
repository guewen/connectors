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
import sys
import traceback
from Queue import Queue, Empty
from functools import wraps
from copy import copy
from datetime import datetime

from openerp.osv import orm, fields
from openerp import pooler
from .session import Session
from .tasks import OpenERPJob, STARTED , QUEUED, DONE, FAILED

_logger = logging.getLogger(__name__)


# decorators
class task(object):

    def __init__(self, queue):
        assert isinstance(queue, AbstractQueue), "%s: invalid queue" % queue
        self.queue = queue

    def __call__(self, func):
        @wraps(func)
        def delay(session, *args, **kwargs):
            self.queue.enqueue_args(session, func, args=args, kwargs=kwargs)
        func.delay = delay
        return func

# TODO periodic_task?


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
        self.key = key
        self._queue = Queue()

    def enqueue(self, session, func, *args, **kwargs):
        """Create a Job and enqueue it in the queue"""
        only_after = kwargs.pop('only_after', None)

        return self.enqueue_args(session, func, args=args,
                                 kwargs=kwargs, only_after=only_after)

    def enqueue_job(self, job, only_after=None):
        job.queue = self.key
        job.date_enqueued = datetime.now()
        job.only_after = only_after
        job.store()

        self._queue.put_nowait(job)  # XXX blocking?
        _logger.debug('Job %s enqueued', job)

    def enqueue_args(self, session, func, args=None, kwargs=None,
                     only_after=None):
        job = self.job_cls.create(session, func, args, kwargs)
        self.enqueue_job(job, only_after=only_after)

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
        return 'JobsQueue(%r)' % self.key

    def __str__(self):
        return '<JobsQueue \'%s\'>' % self.key


class QueueSet(object):

    def __init__(self, *queues):
        self.queues = set(queues)

    def __iter__(self):
        for queue in self.queues:
            yield queue


class PriorityQueueSet(QueueSet):

    default_priority = 10

    def __init__(self, *queue_tuples):
        """ Allows to assign a priority to each queue.
        If a priority is not defined, it uses a default priority with the value
        of `default_priority`.

        A priority is a chance to be selected more often, not an absolute
        order between queues.

        :param queues: each arg is a tuple with a queue and a priority
        """
        queues = set()
        priorities = {}
        for queue in queue_tuples:
            if isinstance(queue, tuple):
                priorities[queue[0]] = queue[1]
                queues.add(queue[0])
            else:
                priorities[queue] = self.default_priority
                queues.add(queue)
        self.queues = queues
        self.priorities = priorities

    def ratios(self, queues):
        """ Creates a range of int per queue based on their priority
        """
        ranges = {}
        queues_prior = dict((queue, prior) for queue, prior
                            in self.priorities.iteritems()
                            if queue in queues)

        start = 0
        maximum = 0
        for queue, priority in queues_prior.iteritems():
            ranges[queue] = xrange(start, start + priority)
            maximum = start + priority
            start += priority
        maximum = start - 1
        return ranges, maximum

    def __iter__(self):
        """ Introduces some randomization to allow queues with a lower priority
        to be chosen sometimes before a queue with a higher priority.
        The more the difference is great, the less a lower priority will have a
        chance to be chosen.
        """
        queues = copy(self.queues)

        ordered_queues = []
        for _ in xrange(len(queues)):
            ratios, maximum = self.ratios(queues)
            rand = random.randint(0, maximum)
            queue = next(que for que, qrange in ratios.iteritems()
                         if rand in qrange)
            ordered_queues.append(queue)
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

        with self.session.own_transaction() as subsession:
            # XXX better way to use the subsession?
            # use a local stack of sessions?
            job.session = subsession
            success = self._do_forked_job(job)

        job.session = self.session

        # exit the fork
        os._exit(int(not success))

    def _do_forked_job(self, job):
        """ Execute the forked job """
        self.log.debug('Starting job', job)

        try:
            result = job.perform()
            job.set_state(DONE, result=result)
        except:
            # TODO allow to pass a pipeline of exception
            # handlers (log errors, send by email, ...)
            exc_info = sys.exc_info()
            exc_string = ''.join(
                traceback.format_exception_only(*exc_info[:2]) +
                traceback.format_exception(*exc_info))
            self.log.error(exc_string)
            job.set_state(FAILED, exc_info=exc_string)
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
            job.set_state(STARTED)
            self.fork_and_run_job(job)

        self.log.info('Stop %s', self)



from openerp.osv import orm

class res_users(orm.Model):
    _inherit = 'res.users'

    def test(self, cr, uid, ids, context=None):
        session = Session(cr,
                          uid,
                          self.pool,
                          self._name,
                          context=context)
        queue1.enqueue_args(session, test1, ('a', 1))
        queue1.enqueue_args(session, test1, ('a', 1))
        queue2.enqueue_args(session, test1, ('b', 1))
        queue2.enqueue_args(session, test2, ('b',), {'b': 2})
        queue2.enqueue_args(session, test2, ('b',), {'b': 2})

        test1.delay(session, 'a', 1)
        test1.delay(session, 'a', 1)
        test2.delay(session, 'a', 2)
        test2.delay(session, 'b', 1)
        test2('b', 10)
        Worker(session, PriorityQueueSet((queue1, 10), (queue2, 30))).work()
        return True


queue1 = JobsQueue('queue1')
queue2 = JobsQueue('queue2')


@task(queue1)
def test1(a, b):
    _logger.debug('test1 %s %s', a, b)


@task(queue2)
def test2(a, b=None):
    _logger.debug('test2 %s %s', a, b)


def on_start_queues():
    """ Assign all pending jobs to queues

    Must be called when OpenERP starts.

    Warning: if OpenERP has many processes with Gunicorn only 1 process must
    take the jobs.
    """


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
from multiprocessing import Queue
from functools import total_ordering  # FIXME only since 2.7

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

    def __init__(self, session, key, priority=999):
        """ """

    def enqueue(self, func, *args, **kwargs):
        """Put a job in the queue"""

    def dequeue(self):
        """ Take the first job from the queue and return it """

    def __eq__(self, other):
        """ """

    def __lt__(self, other):
        """ """

    def __hash__(self):
        """ """

    @classmethod
    def dequeue_by_priority(cls, queues):
        """ """

@total_ordering
class MultiprocessQueue(object):
    """ Implementation """

    job_cls = OpenERPJob

    def __init__(self, session, key, priority=999):
        self.session = session
        self._key = key
        self._queue = Queue()
        self.priority = priority

    def enqueue(self, func, *args, **kwargs):
        """Put a job in the queue"""
        job = self.job_cls.create(self.session, func, args, kwargs)
        self._queue.put_nowait(job)  # XXX blocking?

    def dequeue(self):
        """ Take the first job from the queue and return it """
        job_id = self._queue.get_nowait()
        if job_id is None:
            return None
        try:
            job = self.job_cls.fetch(self.session, job_id)
        except:
            # TODO handle:
            # - no job (recall dequeue to continue to the next)
            # - job fetching error
            raise
        return job

    def __repr__(self):
        return 'MultiprocessQueue(%r)' % self._key

    def __str__(self):
        return '<MultiprocessQueue \'%s\'>' % self._key

    def __eq__(self, other):
        if not isinstance(other, Queue):
            raise TypeError('Cannot compare queues to other objects.')
        return self._key == other._key

    def __lt__(self, other):
        if not isinstance(other, Queue):
            raise TypeError('Cannot compare queues to other objects.')
        return self.priority < other.priority

    def __hash__(self):
        return hash(self._key)

    @classmethod
    def dequeue_by_priority(cls, queues):
        queues = sorted(queues)
        for queue in queues:
            job = queue.dequeue()
            if job is not None:
                return job, queue
        return None


class Worker(object):

    queue_cls = Queue

    def __init__(self, session, queues):
        self.session = session
        self.log = _logger
        if not isinstance(queues, (list, tuple)):
            queues = [queues]
        self.queues = queues

    def fork_and_run_job(self, job):
        """ Fork the process and give it a job """
        pid = os.fork()
        if pid == 0:  # child
            self._do_forked(job)
        else:  # parent
            self.log.debug('Forked with pid: %d', pid)
            while True:
                os.waitpid(pid, 0)

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
                result = self.queue_cls.dequeue_by_priority(
                        self.session, self.queues)
                if result is None:
                    break
            except:
                # which exceptions and how?
                continue

            job, queue = result
            job.set_status(STARTED)
            self.fork_and_run_job(job)

        self.log.info('Stop %s', self)

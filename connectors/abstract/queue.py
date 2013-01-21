# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Guewen Baconnier
#
#    Queues inspired by Celery and rq-python
#    Some part of code may be: Copyright 2012 Vincent Driessen
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
from Queue import Queue, Empty
from copy import copy
from datetime import datetime

from .session import Session
from .jobs import OpenERPJob, STARTED , QUEUED, DONE, FAILED
from .tasks import task

_logger = logging.getLogger(__name__)


def on_start_queues():
    """ Assign all pending jobs to queues

    Must be called when OpenERP starts.

    Warning: if OpenERP has many processes with Gunicorn only 1 process must
    take the jobs.
    """
    # TODO


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
            # TODO find a more efficient and clever algo
            ratios, maximum = self.ratios(queues)
            rand = random.randint(0, maximum)
            queue = next(que for que, qrange in ratios.iteritems()
                         if rand in qrange)
            ordered_queues.append(queue)
            queues.remove(queue)

        for queue in ordered_queues:
            yield queue

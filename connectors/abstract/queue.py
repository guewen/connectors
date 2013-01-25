# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Guewen Baconnier
#
#    Queues inspired by Celery and rq-python
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
from Queue import PriorityQueue
from datetime import datetime

from .session import Session
from .jobs import Job, QUEUED, DONE, FAILED

_logger = logging.getLogger(__name__)


class JobsQueue(object):
    """ Implementation """

    job_cls = Job
    instance = None

    def __init__(self):
        self._queue = PriorityQueue()

    def enqueue_resolve_args(self, session, func, *args, **kwargs):
        """Create a Job and enqueue it in the queue"""
        priority = kwargs.pop('priority', None)
        only_after = kwargs.pop('only_after', None)

        return self.enqueue(session, func, args=args,
                            kwargs=kwargs, priority=priority,
                            only_after=only_after)

    def enqueue_job(self, session, job):
        job.state = QUEUED
        job.date_enqueued = datetime.now()
        job.user_id = session.uid
        job.store(session)

        self._queue.put_nowait(job)
        _logger.debug('%s enqueued', job)

    def enqueue(self, session, func, args=None, kwargs=None,
                priority=None, only_after=None):
        job = self.job_cls(func=func, args=args, kwargs=kwargs,
                           priority=priority, only_after=only_after)
        self.enqueue_job(session, job)

    def dequeue(self):
        """ Take the first job from the queue and return it """
        job = self._queue.get()
        _logger.debug('Fetched job %s', job)
        return job


JobsQueue.instance = JobsQueue()

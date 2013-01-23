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
from Queue import PriorityQueue, Empty
from copy import copy
from datetime import datetime

from .session import Session
from .jobs import OpenERPJob, STARTED , QUEUED, DONE, FAILED

_logger = logging.getLogger(__name__)


def on_start_put_in_queues():
    """ Assign all pending jobs to queues

    Must be called when OpenERP starts.

    Warning: if OpenERP has many processes with Gunicorn only 1 process must
    take the jobs.
    """
    # TODO


class JobsQueue(object):
    """ Implementation """

    job_cls = OpenERPJob
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

    def enqueue_job(self, job):
        job.date_enqueued = datetime.now()
        job.store()

        self._queue.put_nowait(job.id)
        _logger.debug('Job %s enqueued', job)

    def enqueue(self, session, func, args=None, kwargs=None,
                priority=None, only_after=None):
        job = self.job_cls(session, func=func, args=args, kwargs=kwargs,
                           priority=priority, only_after=only_after)
        self.enqueue_job(job)

    def dequeue(self):
        """ Take the first job from the queue and return it """
        # try:
        #     job_id = self._queue.get_nowait()
        # except Empty as err:
        #     return None
        job_id = self._queue.get()
        _logger.debug('Fetched job %s', job_id)
        return job_id

    def fetch_job(self, session, job_id):
        return self.job_cls.fetch(session, job_id)


JobsQueue.instance = JobsQueue()

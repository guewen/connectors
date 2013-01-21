# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Camptocamp SA
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

import os
import errno
import sys
import traceback
import logging
import random

from .queue import JobsQueue
from .jobs import OpenERPJob, STARTED, DONE, FAILED

_logger = logging.getLogger(__name__)


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
            # XXX find a better way to use the subsession in the job
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

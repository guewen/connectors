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

from StringIO import StringIO
import traceback
import logging
import threading
import time

import openerp
from .jobs import Job, STARTED, DONE, FAILED
from .queue import JobsQueue
from .session import Session
from .exceptions import (NoSuchJobError,
                         NotReadableJobError,
                         FailedJobError,
                         RetryableJobError)

_logger = logging.getLogger(__name__)

WAIT_REGISTRY_TIME = 20  # seconds


class Worker(threading.Thread):

    def __init__(self, db_name, queue=JobsQueue.instance):
        super(Worker, self).__init__()
        self.queue = queue
        self.db_name = db_name
        self.registry = openerp.pooler.get_pool(db_name)
        self.started = False

    def run_job(self, job):
        """ """
        db = openerp.sql_db.db_connect(self.db_name)
        cr = db.cursor()

        with Session(cr, openerp.SUPERUSER_ID, self.registry) as session:
            try:
                try:
                    job.refresh(session)
                except NoSuchJobError:
                    return
                except NotReadableJobError:
                    # will be put in failed by the enclosing try/except
                    _logger.debug('Cannot read: %s', job)
                    raise
                job.set_state(session, STARTED)
                _logger.debug('Starting: %s', job)
                result = job.perform(session)
                _logger.debug('Done: %s', job)
                job.set_state(session, DONE, result=result)
            except RetryableJobError:
                # TODO: implement the retryable errrors:
                # retryable should be requeued with a only_after date
                raise NotImplementedError('RetryableJobError to implement')
            except FailedJobError, Exception:  # XXX Exception?
                # TODO allow to pass a pipeline of exception
                # handlers (log errors, send by email, ...)
                buff = StringIO()
                traceback.print_exc(file=buff)
                _logger.error(buff.getvalue())
                # the session cursor may be in an bad state
                error_session = Session(
                        db.cursor(), openerp.SUPERUSER_ID, self.registry)
                with error_session:
                    job.set_state(error_session, FAILED,
                                  exc_info=buff.getvalue())
                raise

    def run(self):
        """ """
        while True:
            while (self.registry.ready and
                   'connectors.installed' in self.registry.models):
                if not self.started:
                    # TODO: ensure that in multiprocess, the jobs are
                    # loaded in one queue only
                    self.on_start_put_in_queue()
                    self.started = True
                job = self.queue.dequeue()
                try:
                    self.run_job(job)
                except:
                    continue

            _logger.debug('%s waiting for registry for %d seconds',
                          self,
                          WAIT_REGISTRY_TIME)
            time.sleep(WAIT_REGISTRY_TIME)

    def on_start_put_in_queue(self):
        """ Assign all pending jobs to the queue

        Must be called when OpenERP starts.

        Warning: if OpenERP has many processes with Gunicorn only 1 process must
        take the jobs.
        """
        db = openerp.sql_db.db_connect(self.db_name)
        cr = db.cursor()
        with Session(cr, openerp.SUPERUSER_ID, self.registry) as session:
            cr.execute("SELECT uuid FROM jobs_storage "
                       "WHERE state in ('queued', 'started') "
                       "FOR UPDATE ")
            uuids = cr.fetchall()
            if uuids:
                _logger.debug('Enqueue %d jobs on start of the worker.', len(uuids))
                for uuid in [uuid for uuid, in uuids]:
                    job = Job(job_id=uuid)
                    job.refresh(session)
                    JobsQueue.instance.enqueue_job(session, job)


def start_service():
    registries = openerp.modules.registry.RegistryManager.registries
    for db_name, registry in registries.iteritems():
        worker = Worker(db_name)
        worker.daemon = True
        worker.start()

start_service()

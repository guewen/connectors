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
from .jobs import OpenERPJob, STARTED, DONE, FAILED
from .queue import JobsQueue
from .session import Session

_logger = logging.getLogger(__name__)

WAIT_REGISTRY_TIME = 20  # seconds

class Worker(threading.Thread):

    def __init__(self, db_name, queue=JobsQueue.instance):
        super(Worker, self).__init__()
        self.queue = queue
        self.db_name = db_name
        self.registry = openerp.pooler.get_pool(db_name)

    def run_job(self, job_id):
        """ """
        result = None
        failed = False
        db = openerp.sql_db.db_connect(self.db_name)
        cr = db.cursor()

        with Session(cr, openerp.SUPERUSER_ID, self.registry) as session:
            try:
                try:
                    job = self.queue.fetch_job(session, job_id)
                except:
                    # TODO handle:
                    # - no job (recall dequeue to continue to the next)
                    # - job fetching error
                    raise
                job.set_state(STARTED)
                _logger.debug('Starting job: %s', job)
                result = job.perform()
                job.set_state(DONE, result=result)
            except:
                # TODO allow to pass a pipeline of exception
                # handlers (log errors, send by email, ...)
                buff = StringIO()
                traceback.print_exc(file=buff)
                _logger.error(buff.getvalue())
                job.set_state(FAILED, exc_info=buff.getvalue())
                raise

    def run(self):
        """ """
        while True:
            while (self.registry.ready and
                   'connectors.installed' in self.registry.models):
                job_id = self.queue.dequeue()
                try:
                    self.run_job(job_id)
                except:
                    continue

            _logger.debug('%s waiting for registry for %d seconds',
                          repr(self),
                          WAIT_REGISTRY_TIME)
            time.sleep(WAIT_REGISTRY_TIME)


def start_service():
    registries = openerp.modules.registry.RegistryManager.registries
    for db_name, registry in registries.iteritems():
        worker = Worker(db_name)
        worker.daemon = True
        worker.start()

start_service()

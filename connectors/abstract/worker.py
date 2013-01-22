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

import StringIO
import traceback
import logging
import threading

import openerp
from .jobs import OpenERPJob, STARTED, DONE, FAILED
from .queue import JobsQueue
from .session import Session

_logger = logging.getLogger(__name__)


class Worker(threading.Thread):

    def __init__(self, session, dbname, queue=JobsQueue.instance):
        super(Worker, self).__init__()
        self.session = session
        self.queue = queue
        self.dbname = dbname

    def run_job(self, job):
        """ """
        result = None
        failed = False
        try:
            with self.session.own_transaction() as subsession:
                # XXX find a better way to use the subsession in the job
                # use a local stack of sessions?
                job.session = subsession

                _logger.debug('Starting job: %s', job)
                result = job.perform()  # result of the task
                job.set_state(DONE, result=result)
        except:
            # TODO allow to pass a pipeline of exception
            # handlers (log errors, send by email, ...)
            buff = StringIO.StringIO()
            traceback.print_exc(file=buff)
            _logger.error(buff.getvalue())
            job.session = self.session
            job.set_state(FAILED, exc_info=buff.getvalue())

        return result

    def run(self):
        """ """
        _logger.info('Start %s', self)
        while True:
            try:
                job = self.queue.dequeue(self.session)
                if job is None:
                    continue
            except Exception as err:
                _logger.exception(err)
                # which exceptions and how?
                continue

            job.set_state(STARTED)
            self.run_job(job)

        _logger.info('Stop %s', self)


# TODO remove those lines of test
db = openerp.sql_db.db_connect('openerp_magento7')
cr = db.cursor()
registry = openerp.pooler.get_pool('openerp_magento7')
session = Session(cr, openerp.SUPERUSER_ID, registry)
try:
    worker = Worker(session, 'openerp_magento7')
    worker.daemon = True
    worker.start()
finally:
    cr.close()

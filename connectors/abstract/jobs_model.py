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

from openerp.osv import orm, fields

from .queue import JobsQueue
from .session import Session
from .jobs import Job


class JobsStorageModel(orm.Model):
    """ Job status and result.
    """
    _name = 'jobs.storage'

    _log_access = False

    _columns = {
        'uuid': fields.char('UUID', readonly=True, select=True),
        'name': fields.char('Description', readonly=True),
        'func_string': fields.char('Task', readonly=True),
        'func': fields.text('Pickled Job Function', readonly=True),
        # TODO: use the constants from module .tasks
        'state': fields.selection([('queued', 'Queued'),
                                   ('started', 'Started'),
                                   ('failed', 'Failed'),
                                   ('done', 'Done')],
                                  string='State',
                                  readonly=True),
        'exc_info': fields.text('Traceback', readonly=True),
        'result': fields.text('Result', readonly=True),
        'date_created': fields.datetime('Created Date', readonly=True),
        'date_started': fields.datetime('Start Date', readonly=True),
        'date_enqueued': fields.datetime('Enqueue Time', readonly=True),
        'date_done': fields.datetime('Date Done', readonly=True),
        'only_after': fields.datetime('Execute only after'),
        }

    def requeue(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        session = Session(cr, uid, self.pool, context=context)
        for dbjob in self.browse(cr, uid, ids, context=context):
            if dbjob.state == 'failed':
                job = Job(job_id=dbjob.uuid)
                job.refresh(session)
                JobsQueue.instance.enqueue_job(session, job)
        return True

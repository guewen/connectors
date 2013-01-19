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

import logging
from uuid import uuid4
from datetime import datetime

from openerp.osv import orm, fields

PENDING = 'pending'
QUEUED = 'queued'
DONE = 'done'
STARTED = 'started'
FAILED = 'failed'

_logger = logging.getLogger(__name__)


class TasksRegistry(object):

    def __init__(self):
        self.tasks = {}

    def get(self, task):
        if task in self.tasks:
            return self.tasks[task]
        raise ValueError('No matching task found')

    def register(self, task_name, function):
        self.tasks[task_name] = function


class AbstractJob(object):
    """ Job metadata
    """

    storage = None  # class which handle the storage

    @classmethod
    def create(cls, session, func, args, kwargs, job_id=None):
        """ Create a job """

    @classmethod
    def exists(cls, session, job_id):
        """Returns if a job still exists in the storage."""

    @classmethod
    def fetch(cls, session, job_id):
        """Fetch and read a job from the storage and instanciate it
        """
        job = cls(session, id=job_id)
        job.refresh()
        return job

    def __init__(self, session, id=None):
        self.session = session

        self._id = id

        self.created_at = datetime.now()
        self.ended_at = None
        self._only_after = None

        self._result = None
        self._status = None

        self.meta = {}

    def save(self):
        """ Store the Job """

    def refresh(self):
        """ read again the metadata from the storage """

    def cancel(self):
        """ Cancel a job """

    def perform(self):
        """ Execute a job """

    @property
    def state(self):
        return self._status

    @property
    def id(self):
        """Job ID for this instance, this is a UUID
        """
        if self._id is None:
            self._id = unicode(uuid4())
        return self._id

    def status(self):
        """Returns the status of the job."""

    def set_status(self, status, result=None, traceback=None):
        """Change the status of the job."""

    def __repr__(self):
        return '<Job %s>' % self.id


class OpenERPJob(AbstractJob):
    """Implementation of a job on an OpenERP storage"""

    @classmethod
    def create(cls, session, func, args, kwargs, job_id=None):
        """ Create a job """
        return cls(session)

    @classmethod
    def exists(cls, session, job_id):
        """Returns if a job still exists in the storage."""
        stor = session.pool.get('job.storage')
        jobs = stor.search(session.cr,
                           session.uid,
                           [('uuid', '=', job_id)],
                           context=session.context,
                           limit=1)
        if jobs:
            return True
        return False

    def save(self):
        """ Store the Job """
        stor = self.session.pool.get('job.storage')
        vals = dict(uuid=self.id,
                    state=self.state,
                    pickled=None,  # TODO
                    traceback=None,
                    result=None,
                    date_done=None,
                    later_date=None)
        stor.create(self.session.cr,
                    self.session.uid,
                    vals,
                    self.session.context)


# TODO handle only the storage of the jobs
class AbstractJobStorage(object):
    """ Task status and result.

    It is called faux queue because it is not a real queue which
    runs all the time (by many processes eventually).
    Instead, it is launched by OpenERP crons and process as many
    tasks as it can.

    This is an acceptable implementation for a PoC which requires
    minimal dependencies (no workers, no message queue database).

    It can be replaced by a real queue.

    The task model need to be implemented in the connectors, for
    example::

        TASKS = TasksRegistry()


        class faux_queue_magento(FauxQueue, orm.Model):
            _name = 'faux.queue.magento'

            task_registry = TASKS

        faux_queue_magento.register_queue('default', 'Default queue')
        faux_queue_magento.register_queue('orders', 'Sales Orders')

    The registry serving the tasks of the queue
    must be defined in ``task_registry``

    With the code above, you will have 2 queues and you will
    need one cron per queue. It can be used as a prioritization.

    """

    task_registry = None  # to be defined in implementations

    @classmethod
    def register_queue(cls, name, string):
        if not hasattr(cls, '_queues'):
            cls._queues = []
        cls._queues.append((name, string))

    def _get_queues(self, cr, uid, context=None):
        if not hasattr(self, '_queues'):
            return []
        return self._queues

    _rec_name = 'queue'

    _columns = {
        'queue': fields.selection(_get_queues, string='Queue'),
        'task': fields.char('Task'),
        'args': fields.serialized('Arguments'),
        'state': fields.selection([('pending', 'Pending'),
                                   ('done', 'Done')],
                                  string='State',
                                  readonly=True),
        'traceback': fields.text('Traceback', readonly=True),
        'result': fields.text('Result', readonly=True),
        'date_done': fields.datetime('Date Done', readonly=True),
        'later_date': fields.datetime('Execute after'),
        }

    _defaults = {
        'state': 'pending',
        }

    def delay(self, cr, uid, queue, task, **kwargs):
        self.create(cr, uid, {'queue': queue, 'task': task, 'args': kwargs})
        return True

    def _get_task(self, task_name):
        if self.task_registry is None:
            raise ValueError('task_registry not defined')
        return self.task_registry.get(task_name)

    def run(self, cr, uid, queue, max_count=None, context=None):
        _logger.debug('Starting execution of tasks on '
                      'the queue \'%s\'', queue)
        task_ids = self.search(
                cr, uid,
                [('queue', '=', queue),
                 ('state', '=', 'pending')],
                limit=max_count,
                context=context)
        session = Session(cr, uid, self.pool, None, context=context)
        for task_id in task_ids:
            # lock the row to avoid to be processed by another job
            sql = "SELECT id FROM %s " % self._table
            sql += "WHERE id = %s FOR UPDATE"
            # TODO catch lock exceptions
            cr.execute(sql, (task_id,))

            task = self.browse(cr, uid, task_id, context=context)

            # the session create a cursor and manage its transactional state
            with session.own_transaction() as subsession:
                _logger.debug('Execute task %d (%s) on the queue \'%s\'',
                              task_id, task.task, queue)
                try:
                    self._get_task(task.task)(subsession, **task.args)
                except Exception as err:  # XXX catch which exception?
                    msg = ''.join(traceback.format_exception(*sys.exc_info()))
                    task.write({'traceback': msg})
                    _logger.exception('Error during execution of task: %d',
                                      task_id)
                else:
                    task.write({'state': 'done', 'traceback': False})

            # release lock on the row
            session.commit()

        _logger.debug('Finished execution of tasks on the queue \'%s\'', queue)
        return True

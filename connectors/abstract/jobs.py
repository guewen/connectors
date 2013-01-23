# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Camptocamp SA
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
import importlib
import inspect
from uuid import uuid4
from cPickle import loads, dumps, UnpicklingError # XXX check errors
from datetime import datetime

from openerp import SUPERUSER_ID
from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from .exceptions import NoSuchJobError, NotReadableJobError

QUEUED = 'queued'
DONE = 'done'
STARTED = 'started'
FAILED = 'failed'

DEFAULT_PRIORITY = 10  # used by the PriorityQueue to sort the jobs


_logger = logging.getLogger(__name__)


class JobStorage(object):

    def store(self):
        """ Store a job """

    def refresh(self):
        """ Read the job's data from the storage """

    def cancel(self):
        """ Cancel a job """

    def write_state(self, state, result=None, exc_info=None):
        """ Change the state of a job """

    def exists(self):
        """Returns if a job still exists in the storage."""


class OpenERPJobStorage(JobStorage):
    """ Store a job on OpenERP """

    _storage_model_name = 'jobs.storage'

    def __init__(self, job, session):
        super(OpenERPJobStorage, self).__init__()
        self.session = session
        self.job = job
        self._openerp_id = None
        self.storage_model = self.session.pool.get(self._storage_model_name)
        assert self.storage_model is not None, ("Model %s not found" %
                                                self._storage_model_name)

    def exists(self):
        """Returns if a job still exists in the storage."""
        jobs = self.storage_model.search(self.session.cr,
                                         self.session.uid,
                                         [('uuid', '=', self.job.id)],
                                         context=self.session.context,
                                         limit=1)
        if jobs:
            return True
        return False

    def store(self):
        """ Store the Job """
        vals = dict(uuid=self.job.id,
                    state=self.job.state,
                    name=self.job.func_string)

        vals['func'] = dumps((self.job.func_name,
                              self.job.args,
                              self.job.kwargs))

        if self.job.date_created:
            vals['date_created'] = self.job.date_created.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)

        if self.job.date_enqueued:
            vals['date_enqueued'] = self.job.date_enqueued.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)
        if self.job.only_after:
            vals['only_after'] = self.job.only_after.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)

        if self.openerp_id:
            self.storage_model.write(
                    self.session.cr,
                    self.session.uid,
                    self.openerp_id,
                    vals,
                    self.session.context)
        else:
            self.storage_model.create(
                    self.session.cr,
                    self.session.uid,
                    vals,
                    self.session.context)
        self.session.commit()

    @property
    def openerp_id(self):
        if self._openerp_id is None:
            job_ids = self.storage_model.search(
                    self.session.cr,
                    SUPERUSER_ID,
                    [('uuid', '=', self.job.id)],
                    context=self.session.context,
                    limit=1)
            if job_ids:
                self._openerp_id = job_ids[0]

        return self._openerp_id

    def refresh(self):
        """ read again the metadata from the storage """
        if self.openerp_id is None:
            raise NoSuchJobError(
                    '%s does no longer exists in the storage.' % self.job)
        stored = self.storage_model.browse(self.session.cr,
                                           self.session.uid,
                                           self.openerp_id,
                                           context=self.session.context)

        func = loads(str(stored.func))

        (self.job.func_name,
         self.job.args,
         self.job.kwargs) = func
        if stored.date_enqueued:
            self.job.date_enqueued = datetime.strptime(
                    stored.date_enqueued, DEFAULT_SERVER_DATETIME_FORMAT)

        if stored.date_started:
            self.job.date_started = datetime.strptime(
                    stored.date_started, DEFAULT_SERVER_DATETIME_FORMAT)

        if stored.date_done:
            self.job.date_done = datetime.strptime(
                    stored.date_done, DEFAULT_SERVER_DATETIME_FORMAT)

        if stored.only_after:
            self.job.only_after = datetime.strptime(
                    stored.only_after, DEFAULT_SERVER_DATETIME_FORMAT)

        self.job.state = stored.state
        self.job.result = loads(str(stored.result)) if stored.result else None
        self.job.exc_info = stored.exc_info if stored.exc_info else None

    def write_state(self):
        """Change the state of the job."""
        vals = {'state': self.job.state}

        if self.job.exc_info is not None:
            vals['exc_info'] = self.job.exc_info
        if self.job.result is not None:
            vals['result'] = dumps(self.job.result)

        if self.job.date_started:
            vals['date_started'] = self.job.date_started.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)
        if self.job.date_done:
            vals['date_done'] = self.job.date_done.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)
        if self.job.only_after:
            vals['only_after'] = self.job.only_after.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)

        self.storage_model.write(self.session.cr,
                                 self.session.uid,
                                 self.openerp_id,
                                 vals,
                                 context=self.session.context)
        self.session.commit()


class Job(object):
    """ Job metadata """

    def __init__(self, job_id=None, func=None,
                 args=None, kwargs=None, priority=None,
                 only_after=None, storage_cls=OpenERPJobStorage):
        if args is None:
            args = ()
        assert isinstance(args, tuple), "%s: args are not a tuple" % args
        if kwargs is None:
            kwargs = {}

        assert isinstance(kwargs, dict), "%s: kwargs are not a dict" % kwargs
        assert not(job_id is None and func is None), "job_id or func is required"

        self.state = None

        self.func_name = None
        if func:
            if inspect.ismethod(func):
                raise NotImplementedError('Jobs on instances are not supported')
            elif inspect.isfunction(func):
                self.func_name = '%s.%s' % (func.__module__, func.__name__)
            else:
                self.func_name = func  # str

        self._id = job_id

        self.args = args
        self.kwargs = kwargs

        self.only_after = only_after
        self.priority = priority
        if self.priority is None:
            self.priority = DEFAULT_PRIORITY

        self.storage_cls = storage_cls

        self.date_created = datetime.now()
        self.date_enqueued = None
        self.date_started = None
        self.date_done = None

        self.result = None
        self.exc_info = None

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)

    def perform(self, session):
        """ Execute a job """
        self.result = self.func(session, *self.args, **self.kwargs)
        return self.result

    @property
    def func_string(self):
        if self.func_name is None:
            return None
        args = [repr(arg) for arg in self.args]
        kwargs = ['%s=%r' % (key, val) for key, val
                  in self.kwargs.iteritems()]
        return '%s(%s)' % (self.func_name, ', '.join(args + kwargs))

    @property
    def id(self):
        """Job ID, this is a UUID
        """
        if self._id is None:
            self._id = unicode(uuid4())
        return self._id

    @property
    def func(self):
        func_name = self.func_name
        if func_name is None:
            return None

        module_name, func_name = func_name.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, func_name)

    def store(self, session):
        """ Store the Job """
        storage = self.storage_cls(self, session)
        storage.store()

    def refresh(self, session):
        """ read again the metadata from the storage """
        storage = self.storage_cls(self, session)
        try:
            storage.refresh()
        except NoSuchJobError:
            raise
        except Exception as err:
            raise NotReadableJobError(err)

    def cancel(self, session):
        """ Cancel a job """
        storage = self.storage_cls(self, session)
        storage.cancel()

    def set_state(self, session, state, result=None, exc_info=None):
        """Change the state of the job."""
        self.state = state

        if state == DONE:
            self.date_done = datetime.now()
        if state == STARTED:
            self.date_started = datetime.now()

        if result is not None:
            self.result = result

        if exc_info is not None:
            self.exc_info = exc_info

        storage = self.storage_cls(self, session)
        storage.write_state()

    def __repr__(self):
        return '<Job %s, priority:%d>' % (self.id, self.priority)


class JobsStorageModel(orm.Model):
    """ Job status and result.
    """
    _name = 'jobs.storage'

    _log_access = False

    _columns = {
        'uuid': fields.char('UUID', readonly=True, select=True),
        'name': fields.char('Task', readonly=True),
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

    _defaults = {
        'state': 'pending',
        }

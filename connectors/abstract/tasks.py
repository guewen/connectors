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
import importlib
import inspect
from uuid import uuid4
from datetime import datetime
from cPickle import loads, dumps, UnpicklingError

from openerp.osv import orm, fields


PENDING = 'pending'
QUEUED = 'queued'
DONE = 'done'
STARTED = 'started'
FAILED = 'failed'

_logger = logging.getLogger(__name__)


class AbstractJob(object):
    """ Job metadata
    """

    storage = None  # class which handle the storage

    @classmethod
    def create(cls, session, func, args=None, kwargs=None):
        """ Create a job """
        if args is None:
            args = ()
        assert isinstance(args, tuple), "%s: args are not a tuple" % args
        if kwargs is None:
            kwargs = {}
        assert isinstance(kwargs, dict), "%s: kwargs are not a dict" % kwargs
        job = cls(session)
        if inspect.ismethod(func):
            job._instance = func.im_self
            job._func_name = func.__name__
        elif inspect.isfunction(func):
            job._func_name = '%s.%s' % (func.__module__, func.__name__)
        else:
            job._func_name = func  # str

        job._args = args
        job._kwargs = kwargs
        job.name = job.func_string()
        return job

    @classmethod
    def exists(cls, session, job_id):
        """Returns if a job still exists in the storage."""

    @classmethod
    def fetch(cls, session, job):
        """Fetch and read a job from the storage and instanciate it
        """
        if isinstance(job, basestring):
            job = cls(session, job_id=job)
        job.refresh()
        return job

    def __init__(self, session, job_id=None):
        self.session = session

        self._id = job_id

        self.date_created = datetime.now()
        self.date_enqueued = None
        self.date_started = None
        self.date_done = None
        self.only_after = None

        self.queue = None
        self.name = None
        self._func_name = None
        self._instance = None
        self._args = None
        self._kwargs = None

        self._result = None
        self._state = None
        self.exc_info = None

    def store(self):
        """ Store the Job """

    def refresh(self):
        """ read again the metadata from the storage """

    def cancel(self):
        """ Cancel a job """

    def perform(self):
        """ Execute a job """
        self._result = self.func(*self.args, **self.kwargs)
        return self._result

    def func_string(self):
        if self.func_name is None:
            return None
        args = [repr(arg) for arg in self.args]
        kwargs = ['%s=%r' % (key, val) for key, val
                  in self.kwargs.iteritems()]
        return '%s(%s)' % (self.func_name, ', '.join(args + kwargs))

    @property
    def id(self):
        """Job ID for this instance, this is a UUID
        """
        if self._id is None:
            self._id = unicode(uuid4())
        return self._id

    @property
    def instance(self):
        return self._instance

    @property
    def func_name(self):
        return self._func_name

    @property
    def func(self):
        func_name = self.func_name
        if func_name is None:
            return None

        if self.instance:
            return getattr(self.instance, func_name)

        module_name, func_name = func_name.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, func_name)

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def state(self):
        """Returns the state of the job."""
        return self._state

    def set_state(self, state, result=None, traceback=None):
        """Change the state of the job."""

    def __repr__(self):
        return '<Job %s>' % self.id


class OpenERPJob(AbstractJob):
    """Implementation of a job on an OpenERP storage"""

    _storage_model_name = 'jobs.storage'

    @classmethod
    def exists(cls, session, job_id):
        """Returns if a job still exists in the storage."""
        stor = session.pool.get(cls._storage_model_name)
        jobs = stor.search(session.cr,
                           session.uid,
                           [('uuid', '=', job_id)],
                           context=session.context,
                           limit=1)
        if jobs:
            return True
        return False

    def __init__(self, session, job_id=None):
        super(OpenERPJob, self).__init__(session, job_id=job_id)
        self.storage_model = self.session.pool.get(self._storage_model_name)
        assert self.storage_model is not None, ("Model %s not found" %
                                                self._storage_model_name)
        self._openerp_id = None

    def store(self):
        """ Store the Job """
        vals = dict(uuid=self.id,
                    state=self.state,
                    queue=self.queue,
                    name=self.func_name,
                    date_started=None,  # TODO complete assignments
                    date_enqueued=None,
                    date_done=None,
                    only_after=None)

        vals['func'] = dumps((self.instance,
                              self.func_name,
                              self.args,
                              self.kwargs))

        if self.exc_info is not None:
            vals['exc_info'] = self.exc_info
        if self._result is not None:
            vals['result'] = self._result

        self.storage_model.create(self.session.cr,
                                  self.session.uid,
                                  vals,
                                  self.session.context)
        self.session.commit()

    @property
    def openerp_id(self):
        if self._openerp_id is None:
            job_ids = self.storage_model.search(
                    self.session.cr,
                    self.session.uid,
                    [('uuid', '=', self.id)],
                    self.session.context,
                    limit=1)
            if job_ids:
                self._openerp_id = job_ids[0]

        return self._openerp_id

    def refresh(self):
        """ read again the metadata from the storage """
        stored = self.storage_model.browse(self.session.cr,
                                           self.session.uid,
                                           self.openerp_id,
                                           context=self.session.context)

        self._instance, self._func_name, self._args, self._kwargs = loads(str(stored.func))
        self.date_created = stored.date_created
        self.date_started = stored.date_started if stored.date_started else None
        self.date_enqueued = stored.date_enqueued if stored.date_enqueued else None
        self.date_done = stored.date_done if stored.date_done else None
        self.only_after = stored.only_after if stored.only_after else None
        self._state = stored.state
        self._result = loads(str(stored.result)) if stored.result else None
        self.exc_info = stored.exc_info if stored.exc_info else None

    def set_state(self, state, result=None, exc_info=None):
        """Change the state of the job."""
        vals = dict(state=state)
        if result is not None:
            vals['result'] = dumps(result)
        if exc_info is not None:
            vals['exc_info'] = exc_info
        self.storage_model.write(self.session.cr,
                                 self.session.uid,
                                 self.openerp_id,
                                 vals,
                                 context=self.session.context)
        self.session.commit()



# TODO handle only the storage of the jobs
class JobsStorage(orm.Model):
    """ Job status and result.
    """
    _name = 'jobs.storage'

    _rec_name = 'queue'
    _log_access = False

    _columns = {
        'uuid': fields.char('UUID', readonly=True, select=True),
        'queue': fields.char('Queue', readonly=True),
        'name': fields.char('Task', readonly=True),
        'func': fields.text('Pickled Job Function', readonly=True),
        # TODO: use the constants from module .tasks
        'state': fields.selection([('pending', 'Pending'),
                                   ('queued', 'Queued'),
                                   ('started', 'Started'),
                                   ('failed', 'Failed'),
                                   ('done', 'Done')],
                                  string='State',
                                  readonly=True),
        'exc_info': fields.text('Traceback', readonly=True),
        'result': fields.text('Result', readonly=True),
        'date_created': fields.datetime('Create Date', readonly=True),
        'date_started': fields.datetime('Start Date', readonly=True),
        'date_enqueued': fields.datetime('Enqueue Time', readonly=True),
        'date_done': fields.datetime('Date Done', readonly=True),
        'only_after': fields.datetime('Execute only after'),
        }

    _defaults = {
        'state': 'pending',
        }

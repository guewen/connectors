# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Guewen Baconnier
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

"""
Implements producers of the events

"""

import logging

from openerp.osv import orm
from openerp import pooler
from openerp.osv.osv import object_proxy
from .events import on_record_create, on_record_write, on_record_unlink, \
        on_sale_order_status_change, on_workflow_signal
from .connector import Session

_logger = logging.getLogger(__name__)


class connectors_installed(orm.AbstractModel):
    """Empty model used to know if the module is
    installed on the database or not."""
    _name = 'connectors.installed'


# generic producers of events on models
class model_producers(object_proxy):
    """ Proxy around the orm Models which tracks the changes
    on the records and fires the events.
    """

    def execute_cr(self, cr, uid, model, method, *args, **kw):
        """
        :param str model: name of the model whose values are being changed
        :param str method: create, read, write, unlink, action or workflow action

        """
        res = super(model_producers, self).execute_cr(
                cr, uid, model, method, *args, **kw)

        pool = pooler.get_pool(cr.dbname)
        # avoid to fire events when the module is not installed
        if not 'connectors.installed' in pool.models:
            return res

        context = kw.get('context')

        session = lambda: Session(  # lazy evaluation
                cr,
                uid,
                pool,
                context=context)
        if method == 'create':
            on_record_create.fire(session(), model, res)
        elif method == 'write':
            ids = args[0]
            vals = args[1]
            if isinstance(ids, (long, int)):
                ids = [ids]
            for res_id in ids:
                on_record_write.fire(session(), model, res_id, vals.keys())
        elif method == 'unlink':
            ids = args[0]
            if isinstance(ids, (long, int)):
                ids = [ids]
            for res_id in ids:
                on_record_unlink.fire(session, model, res_id)
        # TODO: implements action, workflow action?

        return res

    def exec_workflow_cr(self, cr, uid, obj, signal, *args):
        res = super(model_producers, self).exec_workflow_cr(
                cr, uid, obj, signal, *args)
        res_id = args[0]
        # no context?
        on_workflow_signal.fire(
            Session(
                cr,
                uid,
                pooler.get_pool(cr.dbname)),
            obj,
            res_id,
            signal)
        return res

model_producers()


# register consumers on the events:
def task_created(session, model_name, record_id):
    """ here belongs the task(s) creation """
    _logger.info("A %s with id %d has been created" % (model_name, record_id))

on_record_create.subscribe(task_created)


def task_written(session, model_name, record_id, fields):
    """ here belongs the task(s) creation """
    _logger.info("A %s with id %d has been updated on fields %s" %
            (model_name, record_id, fields))

on_record_write.subscribe(task_written)


def task_unlinked(session, model_name, record_id):
    """ here belongs the task(s) creation """
    _logger.info("A %s with id %d has been deleted" % (model_name, record_id))

on_record_unlink.subscribe(task_unlinked)



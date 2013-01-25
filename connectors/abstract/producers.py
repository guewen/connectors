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

from openerp.osv import orm
from openerp import pooler
from openerp.osv.osv import object_proxy
from .session import Session
from .events import (on_record_create,
                     on_record_write,
                     on_record_unlink,
                     on_workflow_signal)


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

        session = Session(cr, uid, pool, model, context=context)
        if method == 'create':
            on_record_create.fire(model, session, res)

        elif method == 'write':
            ids = args[0]
            vals = args[1]
            if isinstance(ids, (long, int)):
                ids = [ids]
            for res_id in ids:
                on_record_write.fire(model, session, res_id, vals.keys())

        elif method == 'unlink':
            ids = args[0]
            if isinstance(ids, (long, int)):
                ids = [ids]
            for res_id in ids:
                on_record_unlink.fire(model, session, res_id)
        # TODO: implements action, workflow action?

        return res

    def exec_workflow_cr(self, cr, uid, obj, signal, *args):
        res = super(model_producers, self).exec_workflow_cr(
                cr, uid, obj, signal, *args)
        res_id = args[0]
        on_workflow_signal.fire(
            obj,
            Session(
                cr,
                uid,
                pooler.get_pool(cr.dbname),
                obj),
            res_id,
            signal)
        return res

model_producers()

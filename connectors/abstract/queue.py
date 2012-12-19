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
from contextlib import closing
from openerp.osv import orm, fields
from openerp import pooler
from .connector import REGISTRY, Session


class FauxQueue(object):
    """ Implementation of a queue on top of the OpenERP crons.

    It is called faux queue because it is not a real queue which
    runs all the time (by many processes eventually).
    Instead, it is launched by OpenERP crons and process as many
    tasks as it can.

    This is an acceptable implementation for a PoC which requires
    minimal dependencies (no workers, no message queue database).

    It can be replaced by a real queue.

    This is an `AbstractModel` and has to be implemented in the
    connectors, for example::

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
    }

    def delay(self, cr, uid, queue, task, args):
        self.create(cr, uid, {'queue': queue, 'task': task, 'args': args})
        return True

    def _get_task(self, task_name):
        if self.task_registry is None:
            raise ValueError('task_registry not defined')
        return self.task_registry.get(task_name)

    def run(self, cr, uid, queue, max_count=None, context=None):
        task_ids = self.search(
                cr, uid,
                [('queue', '=', queue)],
                limit=max_count,
                context=context)
        session = Session(cr, uid, self.pool, context=context)
        for task_id in task_ids:
            # FIXME remove
            self.write(cr, uid, task_id, {'args': {'model_name': 'product.product', 'record_id': 3}})
            # lock the row to avoid to be processed by another job
            sql = "SELECT id FROM %s " % self._table
            sql += "WHERE id = %s FOR UPDATE"
            # TODO catch lock exceptions
            cr.execute(sql, (task_id,))
            task = self.browse(cr, uid, task_id, context=context)

            # the session create a cursor and manage its transactional state
            # check if the tasks should handle that or the run
            with session.own_transaction() as subsession:
                self._get_task(task.task)(subsession, **task.args)

            # release lock on the row
            session.commit()
        return True


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

from openerp.osv import orm, fields
from ..abstract.queue import FauxQueue
from ..abstract.connector import TasksRegistry, \
        SingleImport


TASKS = TasksRegistry()


class faux_queue_magento(FauxQueue, orm.Model):
    _name = 'faux.queue.magento'
    task_registry = TASKS

faux_queue_magento.register_queue('default', 'Default queue')
faux_queue_magento.register_queue('orders', 'Sales Orders')



def import_generic(session, model_name=None, record_id=None, mode='create'):
    """ Import a record from the external referential

    Use keyword arguments for the task arguments

    :param session: `Session` object
    :param model_name: name of the model as str
    :param record_id: id of the record on the external referential
    :param mode: 'create' or 'update'
    """
    # FIXME: not sure that we want forcefully a new cr
    # when we run the task, could it be called from a `_get_dependencies`
    # as instance?
    # should we commit as well?
    with session.own_transaction() as subsession:
        importer = SingleImport(
                subsession, model_name, record_id, mode=mode, with_commit=True)
        importer.import_record()


TASKS.register('import_generic', import_generic)

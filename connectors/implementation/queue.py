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

from openerp.osv import orm
from ..abstract.queue import FauxQueue
from ..abstract.tasks import TasksRegistry


TASKS = TasksRegistry()


class faux_queue_magento(FauxQueue, orm.Model):
    _name = 'faux.queue.magento'
    task_registry = TASKS

faux_queue_magento.register_queue('default', 'Default queue')
faux_queue_magento.register_queue('orders', 'Sales Orders')

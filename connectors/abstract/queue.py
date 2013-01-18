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
import logging
import traceback
import sys

from contextlib import closing
from openerp.osv import orm, fields
from openerp import pooler
from .session import Session

_logger = logging.getLogger(__name__)

# TODO implement a memory queue
# on start: take all the pending tasks
# on write of a task: create a task in the queue
# on end of the task: remove it
# warning with multiprocess: only 1 process should
# take the pending tasks on start


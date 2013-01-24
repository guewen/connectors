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

"""
Register consumers on the events

Example consumers which display a debug log when
an event is fired.
"""

import logging

from .events import (on_record_create,
                     on_record_write,
                     on_record_unlink,
                     on_workflow_signal)

_logger = logging.getLogger(__name__)


@on_record_create
def log_created(session, record_id):
    """ here belongs the task(s) creation """
    _logger.debug("A %s with id %d has been created", session.model_name, record_id)


@on_record_write
def log_written(session, record_id, fields):
    """ here belongs the task(s) creation """
    _logger.debug("A %s with id %d has been updated on fields %s",
            session.model_name, record_id, fields)


@on_record_unlink
def log_unlinked(session, record_id):
    """ here belongs the task(s) creation """
    _logger.debug("A %s with id %d has been deleted", session.model_name, record_id)



@on_workflow_signal
def log_workflow_signal(session, record_id, signal):
    """ here belongs the task(s) creation """
    _logger.debug("Workflow signal %s received on %s "
                  "with id %d", signal, session.model_name, record_id)

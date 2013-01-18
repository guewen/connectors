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
"""
from ..abstract.events import (
        on_record_create,
        on_record_write,
        on_record_unlink
        )
from .events import (
        on_stock_picking_tracking_number,
        on_sale_order_status_change
        )

_MODEL_NAMES = ('product.product', 'res.partner')


def record_created(session, record_id):
    """ here belongs the task(s) creation """
    # TODO: open modification of the queue to use
    # TODO: task created could be different according to the model
    # example: loop on referentials of the record and create a task per
    # referential
    session.pool.get('faux.queue.magento').delay(
            session.cr, session.uid,
            'default',
            'export_generic',
            model_name=session.model_name,
            record_id=record_id,
            mode='create',
            referential_id=1)

on_record_create.subscribe(record_created,
                           model_names=_MODEL_NAMES)


def record_written(session, record_id, fields):
    """ here belongs the task(s) creation """
    session.pool.get('faux.queue.magento').delay(
            session.cr, session.uid,
            'default',
            'export_generic',
            model_name=session.model_name,
            record_id=record_id,
            mode='update',
            fields=fields,
            referential_id=1)

on_record_write.subscribe(record_written,
                          model_names=_MODEL_NAMES)


def record_unlinked(session, record_id):
    """ here belongs the task(s) creation """
    # XXX

on_record_unlink.subscribe(record_unlinked,
                           model_names=_MODEL_NAMES)


# TODO on_sale_order_status_change, on_stock_picking_tracking_number

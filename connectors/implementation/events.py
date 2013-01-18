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

from ..abstract.events import Event

__all__ = [
    'on_stock_picking_tracking_number',
    'on_sale_order_status_change',
]


# implemented at base_sale_multichannels level

on_sale_order_status_change = Event()
"""
`on_sale_order_status_change` is fired when the status of a sale order
has changed.

Listeners should take the following arguments:

 * session: `Session` object
 * record_id: id of the sale order

"""

on_stock_picking_tracking_number = Event()
"""
`on_stock_picking_tracking_number` is fired when a tracking number has been entered
on a packing.

Listeners should take the following arguments:

 * session: `Session` object
 * record_id: id of the packing

"""

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
from ..abstract.events import on_stock_picking_tracking_number
from ..abstract.connector import Session


class stock_picking(orm.Model):

    _inherit = 'stock.picking'

    def write(self, cr, uid, ids, vals, context=None):
        res = super(stock_picking, self).write(
                cr, uid, ids, vals, context=context)
        if vals.get('carrier_tracking_ref'):
            for res_id in ids:
                on_stock_picking_tracking_number.fire(
                    Session(cr, uid, self.pool, context=context), res_id)
        return res
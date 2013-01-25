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

from openerp.osv import orm, fields


class external_referential_service(orm.Model):
    _name = 'external.referential.service'
    _description = 'External Services'

    _columns = {
        'name': fields.char('Service Name', readonly=True, required=True),
        'version': fields.char('Version', readonly=True),
        }


class external_referential(orm.Model):
    _name = 'external.referential'
    _description = 'External Referential'

    _columns = {
        'name': fields.char('Name', required=True),
        'service_id': fields.many2one(
            'external.referential.service',
            'External Service',
            required=True),
        'service': fields.related(
            'service_id',
            'name',
            type='char',
            string='Service',
            readonly=True),
        'version': fields.related(
            'service_id',
            'version',
            type='char',
            string='Version',
            readonly=True),
        'location': fields.char('Location'),
        'username': fields.char('Username'),
        'password': fields.char('Password'),
    }


class ir_model_data(orm.Model):
    _inherit = 'ir.model.data'

    _columns = {
        'referential_id':fields.many2one(
            'external.referential',
            'External Referential'),
    }

    _sql_constraints = [
        ('external_reference_uniq_per_object',
         'unique(model, res_id, referential_id)',
         'You cannot have on record with multiple external '
         'id for a same referential'),
    ]

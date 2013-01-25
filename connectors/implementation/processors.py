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

from ..abstract.processors import BaseProcessor
from .references import Magento, Magento1700


@Magento
class Product(BaseProcessor):
    model_name = 'product.product'


@Magento
class Partner(BaseProcessor):
    model_name = 'res.partner'

    direct_import = [('name', 'name'),
                     ('email', 'email')]


# example of specific mapping for version 1.7
@Magento1700
class Partner1700(Partner):
    model_name = 'res.partner'

    def name(self, attribute, record):
        # XXX use base_partner_surname
        if ' ' in record[attribute]:
            parts = record[attribute].split(' ')
            firstname = parts[0]
            lastname = (' ').join(parts[1:])
        else:
            firstname = '-'
            lastname = record[attribute]
        return {'firstname': firstname, 'lastname': lastname}

    direct_import = [('lastname', 'name'),
                     ('email', 'email'),
                     ('street', 'street'),
                     ('city', 'city')]

    direct_export = [('email', 'email'),
                     ('street', 'street'),
                     ('city', 'city')]

    method_export = [('name', name)]

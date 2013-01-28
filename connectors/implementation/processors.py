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

from ..abstract.processors import (ToReferenceProcessor,
                                   FromReferenceProcessor,
                                   mapping)
from .references import Magento, Magento1700


@Magento
class ToRefProduct(ToReferenceProcessor):
    model_name = 'product.product'

@Magento
class FromRefProduct(FromReferenceProcessor):
    model_name = 'product.product'


@Magento
class FromRefPartner(FromReferenceProcessor):
    model_name = 'res.partner'

    direct = [('name', 'name'),
              ('email', 'email')]

@Magento1700
class FromRefPartner1700(FromRefPartner):

    direct = [('lastname', 'name'),
              ('email', 'email'),
              ('street', 'street'),
              ('city', 'city')]


@Magento1700
class ToRefPartner1700(ToReferenceProcessor):
    model_name = 'res.partner'

    @mapping(changed_by=['name', 'firstname'])
    def name(self, record):
        # XXX use base_partner_surname
        if ' ' in record['name']:
            parts = record['name'].split(' ')
            firstname = parts[0]
            lastname = (' ').join(parts[1:])
        else:
            firstname = '-'
            lastname = record['name']
        return {'firstname': firstname, 'lastname': lastname}

    @mapping
    def email(self, record):
        return {'email': record['email']}

    direct = [('street', 'street'),
              ('city', 'city')]

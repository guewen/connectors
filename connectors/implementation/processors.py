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

from ..abstract.processors import AbstractModelProcessor
from .references import Magento, Magento1700


class Product(AbstractModelProcessor):
    model_name = 'product.product'

Magento.register_processor(Product)


class Partner(AbstractModelProcessor):
    model_name = 'res.partner'

    direct_import = [('name', 'name')]

Magento.register_processor(Partner)


# example of specific mapping for version 1.7
class Partner1700(Partner):
    model_name = 'res.partner'

    direct_import = [('name', 'name'),
                     ('test', 'test')]

Magento1700.register_processor(Partner1700)

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

from ..abstract.processors import AbstractProcessor, AbstractModelProcessor
from ..abstract.connector import REGISTRY
from .references import Magento1600, Magento1700


class MagentoProcessor(AbstractProcessor):
    """ Base Magento Processor """


class Magento1600Processor(MagentoProcessor):
    """ Concrete class for Magento 1.6 """
    reference = Magento1600

REGISTRY.register_mapping(Magento1600Processor)


class Magento1700Processor(MagentoProcessor):
    """ Concrete class for Magento  1.7"""
    reference = Magento1700

REGISTRY.register_mapping(Magento1700Processor)


class MagentoModelProcessor(AbstractModelProcessor):
    """ Base Magento Model Processor """


class Product(MagentoModelProcessor):
    model_name = 'product.product'

Magento1600.register_model_processor(Product)
Magento1700.register_model_processor(Product)


class Partner(MagentoModelProcessor):
    model_name = 'res.partner'

    direct_import = [('name', 'name')]

Magento1600.register_model_processor(Partner)
Magento1700.register_model_processor(Partner)

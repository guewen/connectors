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

import logging
from ..abstract.references import Reference, RecordReferrer
from ..abstract.connector import REGISTRY

_logger = logging.getLogger(__name__)

Magento1600 = Reference('magento', '1.6')
Magento1700 = Reference('magento', '1.7')


class SaleOrderReferrer(RecordReferrer):
    model_name = 'sale.order'
    # FIXME we must have a mean to put "Magento"
    # which is valid for all versions
    reference = Magento1700

    # example: change behavior of links


REGISTRY.register_record_referrer(SaleOrderReferrer)


class ResPartnerReferrer(RecordReferrer):
    model_name = 'res.partner'
    reference = Magento1700

    def to_openerp(self, external_id):
        """ Give the OpenERP ID for an external ID """
        return 10

    def to_external(self, openerp_id):
        """ Give the external ID for an OpenERP ID """
        return 15

    def bind(self, external_id, openerp_id):
        """ Create the link between an external ID and an OpenERP ID """
        _logger.debug('bind openerp_id %s with external_id %s', openerp_id, external_id)


REGISTRY.register_record_referrer(ResPartnerReferrer)

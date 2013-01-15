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
from ..abstract.binders import ModelRecordBinder
from .references import Magento

_logger = logging.getLogger(__name__)


class MagentoBinder(ModelRecordBinder):
    """ Generic Binder for Magento """


class SaleOrderBinder(MagentoBinder):
    model_name = 'sale.order'

Magento.register_binder(SaleOrderBinder)


class ResPartnerBinder(ModelRecordBinder):
    model_name = 'res.partner'

    def to_openerp(self, referential_id, external_identifier):
        """ Give the OpenERP ID for an external ID

        :param referential_id: id of the external.referential
        :param external_identifier: `ExternalIdentifier` for which
            we want the OpenERP ID
        :return: OpenERP ID of the record
        """
        return 10

    def to_external(self, referential_id, openerp_id):
        """ Give the external ID for an OpenERP ID

        :param referential_id: id of the external.referential
        :param openerp_id: OpenERP ID for which we want the
            external id
        :return: `ExternalIdentifier` of the record
        """
        return 15

    def bind(self, referential_id, external_identifier, openerp_id):
        """ Create the link between an external ID and an OpenERP ID

        :param referential_id: id of the external.referential
        :param external_identifier: `ExternalIdentifier` to bind
        :param openerp_id: OpenERP ID to bind
        """
        _logger.debug('bind openerp_id %s with external_id %s',
                      openerp_id, external_identifier)


Magento.register_binder(ResPartnerBinder)

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

from ..abstract.synchronizers import SingleImport, SingleExport
from ..abstract.exceptions import InvalidDataError
from .references import Magento, Magento1700


@Magento
class ResPartnerImport(SingleImport):

    model_name = 'res.partner'

    def _get_external_data(self, external_id):
        # delegate a call to the backend
        return {'name': 'Guewen Baconnier'}

    def _validate_data(self, data):
        if data.get('name') is None:
            raise InvalidDataError('Missing name')


# if Magento 1.7 needs a different synchronization:
@Magento1700
class ResPartner1700Import(SingleImport):

    model_name = 'res.partner'

    def _get_external_data(self, external_id):
        # delegate a call to the backend
        return {'name': 'Guewen Baconnier with Magento 1.7'}

    def _validate_data(self, data):
        if data.get('name') is None:
            raise InvalidDataError('Missing name')


@Magento
class ResPartnerExport(SingleExport):
    model_name = 'res.partner'

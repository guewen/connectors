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

from ..abstract.adapters import ExternalRecordsAdapter
from .references import Magento
from magento import Customer

_logger = logging.getLogger(__name__)


class MagentoLocation(object):

    def __init__(self, location, username, password):
        self.location = location
        self.username = username
        self.password = password


class MagentoRecordsAdapter(ExternalRecordsAdapter):
    """ External Records Adapter for Magento """

    def __init__(self, reference, magento):
        super(MagentoRecordsAdapter, self).__init__(reference)
        self.magento = magento

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, id, attributes=None):
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, id, data):
        """ Update records on the external system """
        raise NotImplementedError

    def unlink(self, id):
        """ Delete a record on the external system """
        raise NotImplementedError


@Magento
class ResPartnerAdapter(MagentoRecordsAdapter):

    model_name = 'res.partner'

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        with Customer(self.magento.location,
                      self.magento.username,
                      self.magento.password) as api:
            rows = api.list(filters)
            return [row['entity_id'] for row in rows]

    def read(self, id, attributes=None):
        """ Returns the information of a record """
        with Customer(self.magento.location,
                      self.magento.username,
                      self.magento.password) as api:
            return api.info(id, attributes)

    def create(self, data):
        """ Create a record on the external system """
        _logger.debug('create data on Magento %s', data)
        with Customer(self.magento.location,
                      self.magento.username,
                      self.magento.password) as api:
            return api.create(data)

    def write(self, id, data):
        """ Update records on the external system """
        _logger.debug('write data on Magento %s', data)
        with Customer(self.magento.location,
                      self.magento.username,
                      self.magento.password) as api:
            return api.update(id, data)

    def unlink(self, id):
        """ Delete a record on the external system """
        with Customer(self.magento.location,
                      self.magento.username,
                      self.magento.password) as api:
            return api.delete(id)

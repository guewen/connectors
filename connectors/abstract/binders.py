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


class ExternalIdentifier(dict):
    """ Most of the time, on an external system, a record is identified
    by a unique ID. However occasionaly, it is identified by an ID and a
    second key, or even no ID at all but some keys.

    Instances of this class encapsulate the identifier(s) for a external
    record.

    The instance should support pickling because an
    `ExternalIdentifier` can be stored in a job.
    """

class Binder(object):
    """ For one record of a model, capable to find an external or
    internal id, or create the link between them
    """

    model_name = None  # define in sub-classes

    @classmethod
    def match(cls, model):
        """ Identify the class to use
        """
        if cls.model_name is None:
            raise NotImplementedError
        return cls.model_name == model._name

    def __init__(self, session):
        self.session = session
        self.model = self.session.pool.get(self.model_name)

    def to_openerp(self, referential_id, external_identifier):
        """ Give the OpenERP ID for an external ID

        :param referential_id: id of the external.referential
        :param external_identifier: `ExternalIdentifier` for which
            we want the OpenERP ID
        :return: OpenERP ID of the record
        """

    def to_external(self, referential_id, openerp_id):
        """ Give the external ID for an OpenERP ID

        :param referential_id: id of the external.referential
        :param openerp_id: OpenERP ID for which we want the
            external id
        :return: `ExternalIdentifier` of the record
        """

    def bind(self, referential_id, external_identifier, openerp_id):
        """ Create the link between an external ID and an OpenERP ID

        :param referential_id: id of the external.referential
        :param external_identifier: `ExternalIdentifier` to bind
        :param openerp_id: OpenERP ID to bind
        """

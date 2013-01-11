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


class ModelRecordBinder(object):
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

    def to_openerp(self, external_id):
        """ Give the OpenERP ID for an external ID """

    def to_external(self, openerp_id):
        """ Give the external ID for an OpenERP ID """

    def bind(self, external_id, openerp_id):
        """ Create the link between an external ID and an OpenERP ID """

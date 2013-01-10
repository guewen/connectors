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

class Reference(object):
    """ A reference represents an external system
    like Magento, Prestashop, Redmine, ...
    """
    def __init__(self, service, version):
        self.service = service
        self.version = version

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return vars(self) == vars(other)

    def __repr__(self):
        return 'Reference(\'%s\', \'%s\')' % (self.service, self.version)



class RecordReferrer(object):
    """ For one record of a model, capable to find an external or
    internal id, or create the link between them
    """

    model_name = None  # default
    reference = None

    @classmethod
    def match(cls, reference, model):
        """ Identify the class to use
        """
        return (model._name == cls.model_name and
                reference == reference)

    def __init__(self, model, reference):
        """
        :param model: instance of the model
        :param reference: XXX external.referential?
        """
        self.model = model
        self.reference = reference

    def to_openerp(self, external_id):
        """ Give the OpenERP ID for an external ID """

    def to_external(self, openerp_id):
        """ Give the external ID for an OpenERP ID """

    def bind(self, external_id, openerp_id):
        """ Create the link between an external ID and an OpenERP ID """

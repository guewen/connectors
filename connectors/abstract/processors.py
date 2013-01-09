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


class AbstractProcessor(object):
    """ Transform a record to a defined output
    """

    reference = None  # has to be defined in subclasses

    processors = {}

    @classmethod
    def match(cls, reference):
        """ Find the appropriate class to transform
        the record

        :param reference: `Reference` instance for
            which we want a transformation
        """
        if cls.reference is None:
            raise NotImplementedError
        return reference == cls.reference

    @classmethod
    def register_model_processor(cls, processor):
        """ Register the processor for a model """
        cls.processors[processor.model_name] = processor

    def __init__(self, connector):
        self.connector = connector

    def processor(self, model):
        """ return an instance processor for a model

        :param model: instance of the model
        :return: instance of the concrete `AbstractModelProcessor`
                 for the model
        """
        return self.processors[model._name](self.connector)

    def to_openerp(self, record, defaults=None):
        """ Transform an external record to an OpenERP record
        """
        return self.processor(self.connector.model)\
                .to_openerp(record, defaults=defaults)

    def to_reference(self, record, defaults=None):
        """ Transform an OpenERP record to an external record
        """
        return self.processor(self.connector.model)\
                .to_reference(record, defaults=defaults)


class AbstractModelProcessor(object):
    """ Transform a record to a defined output
    """

    # name of the OpenERP model, to be defined in concrete classes
    model_name = None

    direct_import = []
    method_import = []
    sub_import = []  # sub import of o2m

    direct_export = []
    method_export = []
    sub_export = []  # sub export of o2m

    def __init__(self, connector):
        self.connector = connector
        # shortcut
        self.model = self.connector.model

    def to_openerp(self, record, defaults=None, parent_values=None):
        """ Transform an external record to an OpenERP record

        :param record: record to transform
        :param defaults: dict of default values when attributes are not set
        :param parent_values: openerp record of the containing object
            (e.g. sale_order for a sale_order_line)
        """
        if defaults is None:
            defaults = {}
        else:
            result = dict(defaults)

        for ref_attr, oerp_attr in self.direct_import:
            result[oerp_attr] = record.get(ref_attr, False)

        for ref_attr, meth in self.method_import:
            vals = meth(self, ref_attr, record)
            if isinstance(vals, dict):
                result.update(vals)

        for ref_attr, (oerp_attr, sub_cls) in self.sub_import:
            attr = record[ref_attr]  # not compatible with all record types
            sub = sub_cls(self.connector)
            vals = sub._o2m_to_openerp(attr, parent_value=result)
            result[oerp_attr] = vals

        return result

    def to_reference(self, record, defaults=None):
        """ Transform an OpenERP record to an external record
        """

    def _o2m_to_openerp(self, records, parent_values=None):
        """ return values of a one2many to put in the main record
        do not create the records!
        """
        # XXX get default values
        result = []
        for record in records:
            vals = self.to_openerp(record, defaults=None)
            result.append((0, 0, vals))
        return result

# m2o should be imported by the connector before the transformation

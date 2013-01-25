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


class Processor(object):
    """ Base class for processors """

    model_name = None

    def __init__(self, session, reference):
        self.session = session
        self.reference = reference
        self.model = self.session.pool.get(self.model_name)

    @classmethod
    def match(cls, model):
        """ Find the appropriate class to transform
        the record

        :param reference: `Reference` instance for
            which we want a transformation
        """
        if cls.model_name is None:
            raise NotImplementedError
        if hasattr(model, '_name'):  # model instance
            model_name = model._name
        else:
            model_name = model  # str
        return cls.model_name == model_name

    def to_reference(self, record, fields=None, defaults=None):
        """ Transform an OpenERP record to an external record
        """

    def to_openerp(self, record, defaults=None, parent_values=None):
        """ Transform an external record to an OpenERP record

        :param record: record to transform
        :param defaults: dict of default values when attributes are not set
        :param parent_values: openerp record of the containing object
            (e.g. sale_order for a sale_order_line)
        """


# TODO 1 class per direction
class BaseProcessor(Processor):
    """ Transform a record to a defined output """

    # name of the OpenERP model, to be defined in concrete classes
    model_name = None

    direct_import = []
    method_import = []
    sub_import = []  # sub import of o2m

    direct_export = []
    method_export = []
    sub_export = []  # sub export of o2m


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

        # TODO: o2m
        # for ref_attr, (oerp_attr, sub_cls) in self.sub_import:
        #     attr = record[ref_attr]  # not compatible with all record types
        #     sub = sub_cls(self.synchronizer)
        #     vals = sub._o2m_to_openerp(attr, parent_value=result)
        #     result[oerp_attr] = vals

        return result

    def to_reference(self, record, fields=None, defaults=None):
        """ Transform an OpenERP record to an external record
        """
        if defaults is None:
            defaults = {}
        else:
            result = dict(defaults)
        # TODO: fields

        for oerp_attr, ref_attr in self.direct_export:
            result[ref_attr] = record[oerp_attr]

        for oerp_attr, meth in self.method_export:
            vals = meth(self, oerp_attr, record)
            if isinstance(vals, dict):
                result.update(vals)

        # TODO submappings (one2many)
        return result

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

# m2o should be imported by the synchronizer before the transformation

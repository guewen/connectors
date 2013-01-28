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

from collections import Callable

# directions
TO_REFERENCE = 'to_reference'
FROM_REFERENCE = 'from_reference'


def mapping(*args, **kwargs):
    """ Decorator declarating a mapping for a field

    ``changed_by`` is a list of field names which should trigger the
    mapping.
    If ``changed_by`` is empty, the mapping is always active.  As
    far as possible, it should be used, thus, when we do an update
    on only a small number of fields on a record, the size of the
    output record will be limited to only the fields having to be
    modified.
    """
    def register_mapping(**opts):
        def wrapper(func):
            func.is_mapping = True
            func.changed_by = opts.get('changed_by')
            return func
        return wrapper

    if len(args) == 1 and isinstance(args[0], Callable):
        return register_mapping(**kwargs)(*args)
    return register_mapping(**kwargs)


class MetaProcessor(type):
    def __init__(cls, name, bases, attrs):
        for key, value in attrs.iteritems():
            mapping = getattr(value, 'is_mapping', None)
            if mapping:
                changed_by = value.changed_by
                cls.method.append((value, changed_by))


class Processor(object):
    """ Transform a record to a defined output

    Sub-conversions are conversion of records in a record. For instance::

        <sale>
          <ref>100001</ref>
          <name>Guewen Baconnier</name>
          <lines>
            <line>
              <item>Product 1</item>
              <unit>1</unit>
              <price>10</price>
            </line>
            <line>
              <item>Product 2</item>
              <unit>1</unit>
              <price>10</price>
            </line>
          </lines>
        </sale>

    A sub-conversion will be necessary to convert the lines.
    """

    __metaclass__ = MetaProcessor

    # name of the OpenERP model, to be defined in concrete classes
    model_name = None
    # direction of the conversion (TO_REFERENCE or FROM_REFERENCE)
    direction = None
    # name of of the parent model ('sale.order' for instance)
    # used for conversions of sub-records
    child_of = None

    def __init__(self, session, reference):
        self.session = session
        self.reference = reference
        self.model = self.session.pool.get(self.model_name)

    @classmethod
    def match(cls, model, direction, child_of=None):
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
        return (cls.model_name == model_name and
                cls.direction == direction and
                cls.child_of == child_of)

    direct = []
    method = []
    children = []  # conversion of sub-records

    def convert(self, record, fields=None, defaults=None, parent_values=None):
        """ Transform an external record to an OpenERP record or the opposite

        :param record: record to transform
        :param defaults: dict of default values when attributes are not set
        :param parent_values: openerp record of the containing object
            (e.g. sale_order for a sale_order_line)
        """
        if defaults is None:
            defaults = {}
        else:
            result = dict(defaults)

        if fields is None:
            fields = {}

        for from_attr, to_attr in self.direct:
            if (fields is None or from_attr in fields):
                # XXX not compatible with all
                # record type (wrap
                # records in a standard class representation?)
                result[from_attr] = record[to_attr]

        for meth in self.method:
            changed_by = None
            if len(meth) == 2:
                meth, changed_by = meth

            if (changed_by is not None and
                    not isinstance(changed_by, (tuple, list))):
                changed_by = [changed_by]

            if (fields is None or
                    changed_by is None or
                    set(fields).intersection(changed_by)):
                vals = meth(self, record)
                if isinstance(vals, dict):
                    result.update(vals)
                else:
                    raise ValueError('%s: invalid return value for the '
                                     'mapping method %s' % (vals, meth))

        for attr, model in self.children:
            if (fields is None or attr in fields):
                processor_class = self.reference.get_processor(model,
                                                               self.direction,
                                                               self.model_name)
                processor = processor_class(self.session, self.reference)
                content = record[attr]  # XXX not compatible with
                                        # all record types
                vals = self._sub_convert(content, processor,
                                         parent_values=result)
                result[attr] = vals

        return result

    def _sub_convert(self, records, processor, parent_values=None):
        """ return values of a one2many to put in the main record
        do not create the records!
        """
        raise NotImplementedError


class ToReferenceProcessor(Processor):
    # direction of the conversion (TO_REFERENCE or FROM_REFERENCE)
    direction = TO_REFERENCE

    def _sub_convert(self, records, processor, parent_values=None):
        """ return values of a one2many to put in the main record
        do not create the records!
        """
        # XXX get default values?
        result = []
        for record in records:
            vals = processor.convert(record,
                                     parent_values=parent_values,
                                     defaults=None)
            result.append(vals)
        return result


class FromReferenceProcessor(Processor):
    # direction of the conversion (TO_REFERENCE or FROM_REFERENCE)
    direction = FROM_REFERENCE

    def _sub_convert(self, records, processor, parent_values=None):
        """ return values of a one2many to put in the main record
        do not create the records!
        """
        # XXX get default values?
        result = []
        for record in records:
            vals = processor.convert(record,
                                     parent_values=parent_values,
                                     defaults=None)
            result.append((0, 0, vals))
        return result

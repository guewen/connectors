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
from .binders import ExternalIdentifier

_logger = logging.getLogger(__name__)


class Synchronizer(object):
    """ Base class for synchronizers """

    # implement in sub-classes
    model_name = None
    synchronization_type = None

    def work(self, *args, **kwargs):
        """ Placeholder for the synchronisation """

    @classmethod
    def match(cls, synchronization_type, model):
        """ Find the good class """
        if hasattr(model, '_name'):  # model instance
            model_name = model._name
        else:
            model_name = model  # str
        return (cls.synchronization_type == synchronization_type and
                cls.model_name == model_name)


class SingleImport(Synchronizer):

    model_name = None  # implement in sub-classes
    synchronization_type = 'import_record'

    def __init__(self, reference, session, model_name, referential_id):
        self.reference = reference
        self.session = session
        self.model = self.session.pool.get(model_name)

        self.referential_id = referential_id  # sometimes it can be a shop...
        ref_obj = self.session.pool.get('external.referential')
        self.referential = ref_obj.browse(self.session.cr,
                                          self.session.uid,
                                          self.referential_id,
                                          context=self.session.context)
        self._binder = None
        self._external_adapter = None
        self._processor = None

    @property
    def binder(self):
        if self._binder is None:
            raise ValueError('A binder is missing for %s' % self)
        return self._binder

    @binder.setter
    def binder(self, binder):
        self._binder = binder

    @property
    def external_adapter(self):
        if self._external_adapter is None:
            raise ValueError('An external_adapter is missing for %s' % self)
        return self._external_adapter

    @external_adapter.setter
    def external_adapter(self, external_adapter):
        self._external_adapter = external_adapter

    @property
    def processor(self):
        if self._processor is None:
            raise ValueError('A processor is missing for %s' % self)
        return self._processor

    @processor.setter
    def processor(self, processor):
        self._processor = processor

    def work(self, external_id, mode, with_commit=False):
        """ Import the record

        Delegates the knowledge to specialized instances
        """
        assert mode in ('create', 'update'), "mode should be create or update"

        # TODO adapter for external APIs?
        ext_data = self._get_external_data(external_id)

        if self._has_to_skip(external_id, ext_data):
            return

        # import the missing linked resources
        self._import_dependencies(ext_data)

        # default_values = self._default_values()

        transformed_data = self._transform_data(ext_data)

        # special check on data before import
        self._validate_data(transformed_data)
        if mode == 'create':
            openerp_id = self._create(transformed_data)
        else:
            openerp_id = self.binder.to_openerp(self.referential,
                                                external_id)
            openerp_id = self._update(openerp_id, transformed_data)

        if openerp_id:
            self.binder.bind(self.referential,
                             external_id,
                             openerp_id)

        if with_commit:
            self.session.commit()

        if hasattr(self, '_after_commit'):
            if with_commit is False:
                raise ValueError('An _after_commit method is declared '
                                 'but SingleImport is initialized without commit')
            getattr(self, '_after_commit')()

        return openerp_id

    def _has_to_skip(self, external_id, external_data):
        # delegate a check of existence of external_id
        return False

    def _get_external_data(self, external_id):
        # delegate a call to the backend
        return

    def _import_dependencies(self, data):
        # call SingleImport#import for each dependency
        # no commit should be done inside of a SingleImport
        # flow
        # import m2o #1
        # import m2o #2
        # the imported records are searched again by their id
        # during the transformation
        return

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Example: pro-actively check before the ``Model.create`` if
        some fields are missing

        Raise `InvalidDataError`?
        """

    def _transform_data(self, external_data):
        # from where do come the default values?
        return self.processor.to_openerp(external_data, defaults={})

    def _create(self, data):
        # delegate creation of the record
        openerp_id = self.model.create(self.session.cr, self.session.uid,
                                       data, self.session.context)
        _logger.debug('openerp_id: %d created', openerp_id)
        return openerp_id

    def _update(self, openerp_id, data):
        # delegate update of the record
        if openerp_id:  # it has been deleted
            self.model.write(self.session.cr, self.session.uid,
                             openerp_id, data, self.session.context)
            _logger.debug('openerp_id: %d updated', openerp_id)
        else:
            return self._create(data)
        return

    # def _after_commit():
    #     """implement only if special actions need to be done
    #     after the commit"""


class SingleExport(Synchronizer):

    model_name = None  # implement in sub-classes
    synchronization_type = 'export_record'

    def __init__(self, reference, session, model_name, referential_id):
        self.reference = reference
        self.session = session
        self.model = self.session.pool.get(model_name)
        self.referential_id = referential_id  # sometimes it can be a shop...
        ref_obj = self.session.pool.get('external.referential')
        self.referential = ref_obj.browse(self.session.cr,
                                          self.session.uid,
                                          self.referential_id,
                                          context=self.session.context)
        self._reference = None
        self._binder = None
        self._external_adapter = None
        self._processor = None

    @property
    def binder(self):
        if self._binder is None:
            raise ValueError('A binder is missing for %s' % self)
        return self._binder

    @binder.setter
    def binder(self, binder):
        self._binder = binder

    @property
    def external_adapter(self):
        if self._external_adapter is None:
            raise ValueError('An external_adapter is missing for %s' % self)
        return self._external_adapter

    @external_adapter.setter
    def external_adapter(self, external_adapter):
        self._external_adapter = external_adapter

    @property
    def processor(self):
        if self._processor is None:
            raise ValueError('A processor is missing for %s' % self)
        return self._processor

    @processor.setter
    def processor(self, processor):
        self._processor = processor

    def work(self, openerp_id, mode, fields=None, with_commit=False):
        """ Export the record

        Delegates the knowledge to specialized instances

        :param mode: could be 'create' or 'update'
        """
        assert mode in ('create', 'update'), "mode should be create or update"

        if fields is None:
            fields = {}

        record = self._browse_record(openerp_id)

        if self._has_to_skip(record):
            return

        # export the missing linked resources
        self._export_dependencies(record)

        # default_values = self._default_values()

        transformed_data = self._transform_data(record, fields)

        # special check on data before import
        self._validate_data(transformed_data)
        if mode == 'create':
            external_id = self._create(transformed_data)
        else:
            external_id = self.binder.to_external(self.referential, openerp_id)
            external_id = self._update(external_id, transformed_data)

        # when update does not find a record, it can call create,
        # in such case, it will have a new identifier.
        # when update does update, it must return None
        if external_id:
            self.binder.bind(self.referential,
                             external_id,
                             openerp_id)

        if with_commit:
            self.session.commit()

        if hasattr(self, '_after_commit'):
            if with_commit is False:
                raise ValueError('An _after_commit method is declared '
                                 'but SingleExport is initialized without commit')
            getattr(self, '_after_commit')()

        return external_id

    def _has_to_skip(self, record):
        return False

    def _browse_record(self, openerp_id):
        return self.model.browse(self.session.cr,
                                 self.session.uid,
                                 openerp_id,
                                 self.session.context)

    def _export_dependencies(self, record):
        # call SingleExport#export for each dependency
        # no commit should be done inside of a SingleImport
        # flow
        return

    def _validate_data(self, data):
        """ Check if the values to export are correct

        Example: pro-actively check before the ``Model.create`` if
        some fields are missing

        Raise `InvalidDataError`?
        """

    def _transform_data(self, record, fields=None):
        # delegate a call to mapping
        # from where do come the default values?
        return self.processor.to_reference(record, fields=fields, defaults={})

    def _create(self, data):
        # delegate creation of the record
        ext_id = self.external_adapter.create(data)
        return ExternalIdentifier(id=ext_id)

    def _update(self, external_id, data):
        if external_id:
            # update
            self.external_adapter.write(external_id, data)
        else:
            return self._create(data)  # FIXME generate the full data
        return

    # def _after_commit():
    #     """implemen only if special actions need to be done
    #     after the commit"""

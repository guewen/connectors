# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Guewen Baconnier
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

import openerp.pooler
import logging

from contextlib import contextmanager
from .references import RecordReferrer, Reference

_logger = logging.getLogger(__name__)


class ConnectorRegistry(object):
    def __init__(self):
        self.connectors = set()
        self.processors = set()
        self.record_referrers = set()

    def get_connector(self, reference):
        for connector in self.connectors:
            if connector.match(reference):
                return connector
        raise ValueError('No matching connector found')

    def get_processor(self, reference):
        for processor in self.processors:
            if processor.match(reference):
                return processor
        raise ValueError('No matching processor found')

    def get_record_referrer(self, reference, model):
        for referrer in self.record_referrers:
            if referrer.match(reference, model):
                return referrer
        raise ValueError('No matching referrer found')

    def register_record_referrer(self, record_referrer):
        self.record_referrers.add(record_referrer)

    def register_connector(self, connector):
        self.connectors.add(connector)

    def register_processor(self, processor):
        self.processors.add(processor)

REGISTRY = ConnectorRegistry()


class TasksRegistry(object):

    def __init__(self):
        self.tasks = {}

    def get(self, task):
        if task in self.tasks:
            return self.tasks[task]
        raise ValueError('No matching task found')

    def register(self, task_name, function):
        self.tasks[task_name] = function


class Session(object):

    def __init__(self, cr, uid, pool, context=None, **kwargs):
        self.cr = cr
        self.uid = uid
        self.pool = pool
        if context is None:
            context = {}
        self.context = context

    @contextmanager
    def own_transaction(self):
        """ Open a new transaction and ensure that it is correctly
        closed.
        """
        db, new_pool = \
                openerp.pooler.get_db_and_pool(self.cr.dbname)
        subsession = Session(db.cursor(),
                             self.uid,
                             new_pool,
                             context=self.context)
        try:
            yield subsession
        except:
            subsession.rollback()
            raise
        else:
            subsession.commit()
        finally:
            subsession.close()

    def commit(self):
        self.cr.commit()

    def rollback(self):
        self.cr.rollback()

    def close(self):
        self.cr.close()


class SingleImport(object):

    connector_registry = REGISTRY

    def __init__(self, session, model_name, external_id, referential_id,
                 mode='create', with_commit=False, **kwargs):
        self.session = session
        self.model = self.session.pool.get(model_name)
        self.external_id = external_id
        assert mode in ('create', 'update'), "mode should be create or update"
        self.mode = mode
        self.with_commit = with_commit
        self.referential_id = referential_id  # sometimes it can be a shop...

        self._reference = None
        self.record_referrer = self.connector_registry\
                .get_record_referrer(self.reference, self.model)()

    @property
    def reference(self):
        if self._reference is None:
            # ref = self.session.pool.get('external.referential').browse(
            #     self.session.cr, self.session.uid, self.referential_id,
            #     self.session.context)
            # self._reference = Reference(ref.service, ref.version)
            self._reference = Reference('magento', '1.7')
        return self._reference

    def import_record(self):
        """ Import the record

        Delegates the knowledge to specialized instances
        """
        if self._has_to_skip():
            return

        # TODO adapter for external APIs?
        ext_data = self._get_external_data()

        # import the missing linked resources
        self._import_dependencies(ext_data)

        # default_values = self._default_values()

        transformed_data = self._transform_data(ext_data)

        # special check on data before import
        self._validate_data(transformed_data)
        if self.mode == 'create':
            openerp_id = self._create(transformed_data)
        else:
            openerp_id = self._update(transformed_data)

        if self.with_commit:
            self.session.commit()

        if hasattr(self, '_after_commit'):
            if self.with_commit is False:
                raise ValueError('An _after_commit method is declared '
                                 'but SingleImport is initialized without commit')
            getattr(self, '_after_commit')()

        return openerp_id

    def _has_to_skip(self):
        # delegate a check of existence of external_id
        return False

    def _get_external_data(self):
        # delegate a call to the backend
        return {'name': 'Guewen Baconnier'}

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
        """
        return True

    def _transform_data(self, external_data):
        processor = self.connector_registry.get_processor(self.reference)(self)
        # from where do come the default values?
        return processor.to_openerp(external_data, defaults={})

    def _create(self, data):
        # delegate creation of the record
        openerp_id = self.model.create(self.session.cr, self.session.uid,
                                       data, self.session.context)
        _logger.debug('openerp_id: %d created for external_id %s',
                      openerp_id, self.external_id)
        # bind
        self.record_referrer.bind(self.external_id, openerp_id)
        return openerp_id

    def _update(self, data):
        # delegate update of the record
        openerp_id = self.record_referrer.to_openerp(self.external_id)
        if openerp_id is None:  # it has been deleted?
            openerp_id = self._create(data)
        else:
            self.model.write(self.session.cr, self.session.uid,
                             openerp_id, data, self.session.context)
            _logger.debug('openerp_id: %d updated for external_id %s',
                          openerp_id, self.external_id)
        return openerp_id

    # def _after_commit():
    #     """implement only if special actions need to be done
    #     after the commit"""


class SingleExport(object):

    connector_registry = REGISTRY

    def __init__(self, session, model_name, record_id,
                 mode='create', with_commit=False,
                 fields=None, **kwargs):
        self.session = session
        self.model = self.session.pool.get(model_name)
        self.record_id = record_id
        assert mode in ('create', 'update'), "mode should be create or update"
        self.mode = mode
        self.with_commit = with_commit
        self.fields = fields

    def export_record(self):
        """ Import the record

        Delegates the knowledge to specialized instances

        :param mode: could be 'create' or 'update'
        """
        if self._has_to_skip():
            return

        record = self._browse_record()

        # import the missing linked resources
        self._export_dependencies(record)

        # default_values = self._default_values()

        transformed_data = self._transform_data(record)

        # special check on data before import
        self._validate_data(transformed_data)
        external_id = getattr(self, '_%s' % self.mode)(transformed_data)

        if self.with_commit:
            self.session.commit()

        if hasattr(self, '_after_commit'):
            if self.with_commit is False:
                raise ValueError('An _after_commit method is declared '
                                 'but SingleExport is initialized without commit')
            getattr(self, '_after_commit')()

        return external_id

    def _has_to_skip(self):
        # delegate a check of existence of external_id
        return False

    def _browse_record(self):
        # delegate a call to browse the record
        return

    def _export_dependencies(self, data):
        # call SingleExport#export for each dependency
        # no commit should be done inside of a SingleImport
        # flow
        return {}

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Example: pro-actively check before the ``Model.create`` if
        some fields are missing
        """
        return True

    def _transform_data(self, external_data):
        # delegate a call to mapping
        return {}

    def _create(self, data):
        # delegate creation of the record
        return

    def _update(self, data):
        # delegate update of the record
        return

    # def _after_commit():
    #     """implement only if special actions need to be done
    #     after the commit"""

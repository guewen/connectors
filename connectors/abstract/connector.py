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

_logger = logging.getLogger(__name__)


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


class AbstractSynchronisation(object):
    # TODO
    def __init__(self, *args, **kwargs):
        """
        """

    def work(self, *args, **kwargs):
        """ Placeholder for the synchronisation
        """


class SingleImport(AbstractSynchronisation):

    def __init__(self, reference, session, model_name, referential_id):
        self.reference = reference
        self.session = session
        self.model = self.session.pool.get(model_name)
        self.referential_id = referential_id  # sometimes it can be a shop...
        self._reference = None
        self._record_referrer = None

    @property
    def record_referrer(self):
        if self._record_referrer is None:
            ref = self.reference.get_record_referrer(self.model)
            self._record_referrer = ref()

        return self._record_referrer

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
            openerp_id = self.record_referrer.to_openerp(external_id)
            openerp_id = self._update(openerp_id, transformed_data)

        self.record_referrer.bind(external_id, openerp_id)

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

        Raise `InvalidDataError`?
        """

    def _transform_data(self, external_data):
        processor = self.reference.get_processor(self.model)(self)
        # from where do come the default values?
        return processor.to_openerp(external_data, defaults={})

    def _create(self, data):
        # delegate creation of the record
        openerp_id = self.model.create(self.session.cr, self.session.uid,
                                       data, self.session.context)
        _logger.debug('openerp_id: %d created', openerp_id)
        return openerp_id

    def _update(self, openerp_id, data):
        # delegate update of the record
        if openerp_id is None:  # it has been deleted?
            openerp_id = self._create(data)
        else:
            self.model.write(self.session.cr, self.session.uid,
                             openerp_id, data, self.session.context)
            _logger.debug('openerp_id: %d updated', openerp_id)
        return openerp_id

    # def _after_commit():
    #     """implement only if special actions need to be done
    #     after the commit"""


class SingleExport(AbstractSynchronisation):

    def __init__(self, reference, session, model_name, referential_id):
        self.reference = reference
        self.session = session
        self.model = self.session.pool.get(model_name)
        self.referential_id = referential_id  # sometimes it can be a shop...
        self._reference = None
        self._record_referrer = None

    @property
    def record_referrer(self):
        if self._record_referrer is None:
            ref = self.reference.get_record_referrer(self.model)
            self._record_referrer = ref()

        return self._record_referrer

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
            external_id = self.record_referrer.to_external(openerp_id)
            external_id = self._update(external_id, transformed_data)

        self.record_referrer.bind(external_id, openerp_id)

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

    def _transform_data(self, record, fields):
        # delegate a call to mapping
        return {}

    def _create(self, data):
        # delegate creation of the record
        return

    def _update(self, external_id, data):
        # delegate update of the record
        return

    # def _after_commit():
    #     """implement only if special actions need to be done
    #     after the commit"""

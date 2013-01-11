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

from .queue import TASKS
from ..abstract.synchronizers import SingleImport, SingleExport
from ..abstract.references import get_reference


def _import_generic(session, model_name=None, record_id=None, mode='create',
                    referential_id=None):
    """ Import a record from the external referential

    Use keyword arguments for the task arguments

    :param session: `Session` object
    :param model_name: name of the model as str
    :param record_id: id of the record on the external referential
    :param mode: 'create' or 'update'
    :param referential_id: id of external.referential
    """
    # extref = session.pool.get('external.referential').browse(
    #         session.cr, session.uid, referential_id, session.context)
    # ref = get_reference(extref.service, extref.version)
    ref = get_reference('magento', '1.7')

    # FIXME: not sure that we want forcefully a new cr
    # when we run the task, could it be called from a `_get_dependencies`
    # as instance?
    # should we commit as well?

    importer_cls = ref.get_synchronizer('import_record', model_name)
    importer = importer_cls(ref, session, model_name, referential_id)
    importer.work(record_id, mode, with_commit=True)

TASKS.register('import_generic', _import_generic)


def _export_generic(session, model_name=None, record_id=None,
                    mode='create', fields=None, referential_id=None):
    """ Export a record to the external referential

    Use keyword arguments for the task arguments

    :param session: `Session` object
    :param model_name: name of the model as str
    :param record_id: id of the record on the external referential
    :param mode: 'create' or 'update'
    :param fields: optional dict of fields to export, if None,
                   all the fields are exported
    :param referential_id: id of external.referential
    """
    # FIXME: not sure that we want forcefully a new cr
    # when we run the task, could it be called from a `_get_dependencies`
    # as instance?
    # should we commit as well?

    # TODO move the search of the Reference in the external.referential
    # model

    # extref = session.pool.get('external.referential').browse(
    #         session.cr, session.uid, referential_id, session.context)
    # ref = get_reference(extref.service, extref.version)
    ref = get_reference('magento', '1.7')
    exporter_cls = ref.get_synchronizer('export_record', model_name)
    exporter = exporter_cls(ref, session, model_name, referential_id)
    # if the task export with commit, it should not be called
    # for subimports
    exporter.work(record_id, mode, fields=fields, with_commit=True)


TASKS.register('export_generic', _export_generic)

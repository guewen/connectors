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
from ..abstract.connector import SingleImport, SingleExport

def import_generic(session, model_name=None, record_id=None, mode='create',
                   referential_id=None):
    """ Import a record from the external referential

    Use keyword arguments for the task arguments

    :param session: `Session` object
    :param model_name: name of the model as str
    :param record_id: id of the record on the external referential
    :param mode: 'create' or 'update'
    :param referential_id: id of external.referential
    """
    # FIXME: not sure that we want forcefully a new cr
    # when we run the task, could it be called from a `_get_dependencies`
    # as instance?
    # should we commit as well?
    with session.own_transaction() as subsession:
        importer = SingleImport(
                subsession, model_name, record_id, referential_id,
                mode=mode, with_commit=True)
        importer.import_record()


TASKS.register('import_generic', import_generic)


def export_generic(session, model_name=None, record_id=None,
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
    with session.own_transaction() as subsession:
        exporter = SingleExport(
                subsession,
                model_name,
                record_id,
                mode=mode,
                with_commit=True,
                fields=fields)
        exporter.export_record()


TASKS.register('export_generic', export_generic)

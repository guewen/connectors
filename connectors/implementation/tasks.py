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

from ..abstract.synchronizers import SingleImport, SingleExport
from ..abstract.references import get_reference
from ..abstract.tasks import task
from ..abstract.session import Session
from ..abstract.worker import Worker
from ..abstract.queue import JobsQueue

_logger = logging.getLogger(__name__)


@task
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


@task
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


# TODO clean

from openerp.osv import orm

@task
def test1(session, a, b):
    _logger.debug('test1 %s %s', a, b)


@task
def test2(session, a, b=None):
    _logger.debug('test2 %s %s', a, b)


class res_users(orm.Model):
    _inherit = 'res.users'

    def test(self, cr, uid, ids, context=None):
        session = Session(cr,
                          uid,
                          self.pool,
                          self._name,
                          context=context)

        # enqueue
        JobsQueue.instance.enqueue(session, test1, args=('a', 1))
        JobsQueue.instance.enqueue(session, test1, args=('a', 1))
        JobsQueue.instance.enqueue(session, test1, args=('b', 1))
        JobsQueue.instance.enqueue(session, test2, args=('b',), kwargs={'b': 2})
        JobsQueue.instance.enqueue(session, test2, args=('b',), kwargs={'b': 2})

        # syntactic sugar
        test1.delay(session, 'a', 1, priority=20)
        test1.delay(session, 'a', 1)
        test2.delay(session, 'a', 2, priority=2)
        test2.delay(session, 'b', 1)
        # direct, no job
        test2(session, 'b', 10)
        # work
        return True

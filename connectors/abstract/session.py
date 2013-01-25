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

import openerp.pooler

from contextlib import contextmanager


class Session(object):
    """ Container for the OpenERP transactional stuff:

    * `cr`: Cursor
    * `uid`: User id
    * `pool`: pool or registry of models
    * `context`: OpenERP context

    A session can hold a reference to a model. This is useful
    in the connectors' context because a session's live is usually
    focused on a model (export a product, import a sale order, ...)
    * `model_name`: name of the model
    * `model`: instance of the model

    A session can be used as a context manager. When using the context
    manager, the cursor will be committed or rollbacked (if an exception
    occurs), then closed.

    A session can open a new session with the same attributes, but a new
    cursor. Usage::

        with session.subsession() as subsession:
            do_work(subsession, ...)

    The subsession will be committed / rollbacked and closed as well.

    """

    def __init__(self, cr, uid, pool, model_name=None, context=None):
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.model_name = model_name
        self.model = None
        if model_name is not None:
            self.model = self.pool.get(model_name)
        if context is None:
            context = {}
        self.context = context

    @contextmanager
    def subsession(self):
        """ Open a new transaction and ensure that it is correctly
        closed.
        """
        db, new_pool = openerp.pooler.get_db_and_pool(self.cr.dbname)
        with Session(db.cursor(),
                     self.uid,
                     new_pool,
                     self.model_name,
                     context=self.context) as sub:
            yield sub

    @contextmanager
    def change_user(self, uid):
        """ Temporarily change the user's session and restablish the
        normal user at closing,
        """
        current_uid = self.uid
        self.uid = uid
        yield self
        self.uid = current_uid

    def commit(self):
        self.cr.commit()

    def rollback(self):
        self.cr.rollback()

    def close(self):
        self.cr.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        if tb is None:
            self.commit()
        else:
            self.rollback()
        self.close()

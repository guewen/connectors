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

    def __init__(self, cr, uid, pool, model_name=None, context=None):
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.model_name = model_name
        if model_name is not None:
            self.model = self.pool.get(model_name)
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
                             self.model_name,
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

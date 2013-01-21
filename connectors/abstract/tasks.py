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

from functools import wraps

import queue as que


# decorators
class task(object):

    def __init__(self, queue):
        assert isinstance(queue, que.AbstractQueue), "%s: invalid queue" % queue
        self.queue = queue

    def __call__(self, func):
        @wraps(func)
        def delay(session, *args, **kwargs):
            self.queue.enqueue_args(session, func, args=args, kwargs=kwargs)
        func.delay = delay
        return func

# TODO periodic_task?

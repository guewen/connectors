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

__all__ = [
    'on_record_write',
    'on_record_create',
    'on_record_unlink',
    'on_workflow_signal',
]

# rename to Event
class EventHook(object):
    """
    Simple event class used to provide hooks for events
    in the implementations of the connectors.

    Here's how to use the EventHook class::
    # TODO update the doc

        my_event = EventHook()
        def on_my_event(a, b):
            print "Event was fired with arguments: %s, %s" % (a, b)
        my_event.subscribe(on_my_event)
        my_event.fire("foo", "bar")
    """

    def __init__(self):
        self._handlers = {None: set()}

    def subscribe(self, handler, model_names=None, replacing=None):
        if replacing is not None:
            self.unsubscribe(replacing, model_names=model_names)
        if not isinstance(model_names, (list, tuple)):
            model_names = [model_names]
        for name in model_names:
            self._handlers.setdefault(name, set()).add(handler)

    def unsubscribe(self, handler, model_names=None):
        if not isinstance(model_names, (list, tuple)):
            model_names = [model_names]
        for name in model_names:
            if name in self._handlers:
                self._handlers[name].remove(handler)

    def fire(self, model_name, *args, **kwargs):
        for name in (None, model_name):
            for handler in self._handlers.get(name, ()):
                handler(*args, **kwargs)

    def __call__(self, func):
        # TODO : implement decorator
        return func


on_record_write = EventHook()
"""
`on_record_write` is fired when one record has been updated.

Listeners should take the following arguments:

 * session: `Session` object
 * model_name: model
 * record_id: id of the record
 * fields: fields which have been written

"""

on_record_create = EventHook()
"""
`on_record_create` is fired when one record has been created.

Listeners should take the following arguments:

 * session: `Session` object
 * model_name: model
 * record_id: id of the created record

"""

on_record_unlink = EventHook()
"""
`on_record_unlink` is fired when one record has been deleted.

Listeners should take the following arguments:

 * session: `Session` object
 * model_name: model
 * record_id: id of the record

"""

on_workflow_signal = EventHook()
"""
`on_workflow_signal` is fired whenever a workflow signal is triggered.

Listeners should take the following arguments:

 * session: `Session` object
 * model_name: model
 * record_id: id of the record
 * signal: name of the signal

"""

# Some usual events should be implemented here
# Events which may be specific for one connector
# could be implemented in their own connector.

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

from collections import Callable

__all__ = [
    'on_record_write',
    'on_record_create',
    'on_record_unlink',
    'on_workflow_signal',
]


class Event(object):
    """ An event handles actions called when the event is fired.

    The events are able to filter the actions by model name.

    The usage of an event is to instantiate an `Event` object::

        on_my_event = Event()

    Then to subscribe one or more actions, an action is a function::

        def do_something(a, b):
            print "Event was fired with arguments: %s, %s" % (a, b)

        # active on all models
        on_my_event.subscribe(do_something)

        def do_something_product(a, b):
            print ("Event was fired on a product "
                  "with arguments: %s, %s" % (a, b))

        # active only on product.product
        on_my_event.subscribe(do_something_product,
                              model_names='product.product')

    We can also replace an event::

        def do_something_product2(a, b):
            print "Action 2"
            print ("Event was fired on a product "
                  "with arguments: %s, %s" % (a, b))

        on_my_event.subscribe(do_something_product2,
                              replacing=do_something_product)

    Finally, we fire the event::

        on_my_event.fire('value_a', 'value_b')

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

    def __call__(self, *args, **kwargs):
        """ Event decorator

        For an event `on_event` declared like this::

            on_event = Event()

        A consumer can be subscribed using::

            @on_event
            def do_things(arg1, arg2):
                # work

        And for consumers specific to models::

            @on_event(model_names=['product.product', 'res.partner'])
            def do_things(arg1, arg2):
                # work

        """
        def with_subscribe(model_names=None):
            def wrapped_func(func):
                self.subscribe(func, model_names=model_names)
                return func
            return wrapped_func

        if len(args) == 1 and isinstance(args[0], Callable):
            return with_subscribe(**kwargs)(*args)
        return with_subscribe(**kwargs)


on_record_write = Event()
"""
`on_record_write` is fired when one record has been updated.

Listeners should take the following arguments:

 * session: `Session` object
 * record_id: id of the record
 * fields: fields which have been written

"""

on_record_create = Event()
"""
`on_record_create` is fired when one record has been created.

Listeners should take the following arguments:

 * session: `Session` object
 * record_id: id of the created record

"""

on_record_unlink = Event()
"""
`on_record_unlink` is fired when one record has been deleted.

Listeners should take the following arguments:

 * session: `Session` object
 * record_id: id of the record

"""

on_workflow_signal = Event()
"""
`on_workflow_signal` is fired whenever a workflow signal is triggered.

Listeners should take the following arguments:

 * session: `Session` object
 * record_id: id of the record
 * signal: name of the signal

"""

# Some usual events should be implemented here
# Events which may be specific for one connector
# could be implemented in their own connector.

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

class ReferenceRegistry(object):
    def __init__(self):
        self.references = set()

    def register_reference(self, reference):
        self.references.add(reference)

    def get_reference(self, service, version):
        for reference in self.references:
            if reference.match(service, version):
                return reference
        raise ValueError('No reference found for %s %s' %
                         service, version)

# it all starts here!
REFERENCES = ReferenceRegistry()

def get_reference(service, version):
    return REFERENCES.get_reference(service, version)

def register_reference(reference):
    REFERENCES.register_reference(reference)


class Reference(object):
    """ A reference represents an external system
    like Magento, Prestashop, Redmine, ...

    A reference can hold a version.

    The references contains all the classes they are able to use
    (processors, referrers, synchronizers) and return the appropriate
    class to use for a model.  When a reference is linked to a parent
    and no particular processor, synchronizer or referrer is defined, it
    will use the parent's one.

    Example::

        magento = Reference('magento')
        magento1700 = Reference('magento', '1.7', parent=magento)

    """
    def __init__(self, service, version=None, parent=None):
        self.service = service
        self.version = version
        self.parent = parent
        self._processors = set()
        self._record_referrer = None
        self._synchronizers = set()

    def match(self, service, version):
        return (self.service == service and
                self.version == version)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        if self.version:
            return 'Reference(\'%s\', \'%s\')' % (self.service, self.version)
        return 'Reference(\'%s\')' % self.service

    def get_synchronizer(self, synchro_type, model):
        synchronizer = None
        if self._synchronizers:
            for sync in self._synchronizers:
                if sync.match(synchro_type, model):
                    synchronizer = sync
                    break
        if synchronizer is None and self.parent:
            synchronizer = self.parent.get_synchronizer(synchro_type, model)
            if synchronizer is None:
                raise ValueError('No matching synchronizer found')
        return synchronizer

    def get_processor(self, model):
        processor = None
        if self._processors:
            for proc in self._processors:
                if proc.match(model):
                    processor = proc
                    break
        if processor is None and self.parent:
            processor = self.parent.get_processor(model)
            if processor is None:
                raise ValueError('No matching processor '
                                 'found for %s' % self)
        return processor

    def get_record_referrer(self, model):
        if self._record_referrer:
            record_referrer = self._record_referrer
        else:
            if self.parent:
                record_referrer = self.parent.get_record_referrer(model)
            if record_referrer is None:
                raise ValueError('No matching record_referrer found for %s' % self)
        return record_referrer

    def register_record_referrer(self, record_referrer):
        self._record_referrer = record_referrer

    def register_synchronizer(self, synchronizer):
        self._synchronizers.add(synchronizer)

    def register_processor(self, processor):
        self._processors.add(processor)

    def unregister_synchronizer(self, synchronizer):
        self._synchronizers.remove(synchronizer)

    def unregister_processor(self, processor):
        self._processors.remove(processor)

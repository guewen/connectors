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

class Reference(object):
    """ A reference represents an external system
    like Magento, Prestashop, Redmine, ...
    """
    def __init__(self, service, version):
        self.service = service
        self.version = version

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return vars(self) == vars(other)

    def __repr__(self):
        return 'Reference(\'%s\', \'%s\')' % (self.service, self.version)

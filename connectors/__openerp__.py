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

{
    'name': 'Connectors',
    'version': '0.0',
    'category': 'Generic Modules',
    'description': """
Experiments around the connectors, with chocolate.
    """,
    'author': 'Guewen Baconnier',
    'website': '',
    'depends': ['delivery'],
    'data': [
        'group_fields_view.xml',
        'security/base_external_referentials_security.xml',
        'implementation/queue_view.xml',
    ],
    'installable': True,
}

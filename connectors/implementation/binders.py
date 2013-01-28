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
from ..abstract.binders import Binder, ExternalIdentifier
from .references import Magento

_logger = logging.getLogger(__name__)


class MagentoBinder(Binder):
    """ Generic Binder for Magento """

    def _prefixed_id(self, external_identifier):
        """Return the prefixed_id for an id given
        :param str or int id: external id
        :rtype str
        :return the prefixed id
        """
        # The reason why we don't just use the external id and put the
        # model as the prefix is to avoid unique ir_model_data.name per
        # module constraint violation.
        return "%s/%s" % (self.model._name.replace('.', '_'),
                          str(external_identifier.id))

    def _extid_from_prefixed_id(self, prefixed_id):
        """Return the external id extracted from an prefixed_id

        :param str prefixed_id: prefixed_id to process
        :rtype int/str
        :return the id extracted
        """
        parsed = prefixed_id.split(self.model._name.replace('.', '_') + '/')[1]

        if parsed.isdigit():
            parsed = int(parsed)
        ext_id = ExternalIdentifier()  # TODO find a good way to manage
                                       # the ExternalIdentifier
        ext_id.id = parsed
        return ext_id

    def _get_openerp_id(self, referential, external_identifier):
        """Returns the id of the entry in ir.model.data and the expected
        id of the resource in the current model Warning the
        expected_oe_id may not exists in the model, that's the res_id
        registered in ir.model.data
        """
        model_data_obj = self.session.pool.get('ir.model.data')
        model_data_ids = model_data_obj.search(
                self.session.cr,
                self.session.uid,
                [('name', '=', self._prefixed_id(external_identifier)),
                 ('model', '=', self.model._name),
                 ('referential_id', '=', referential.id)],
                context=self.session.context)
        model_data_id = model_data_ids and model_data_ids[0] or False
        expected_oe_id = False
        if model_data_id:
            expected_oe_id = model_data_obj.read(
                    self.session.cr,
                    self.session.uid,
                    model_data_id,
                    ['res_id'])['res_id']
        return expected_oe_id

    def to_openerp(self, referential, external_identifier):
        """ Give the OpenERP ID for an external ID

        :param referential_id: id of the external.referential
        :param external_identifier: `ExternalIdentifier` for which
            we want the OpenERP ID
        :return: OpenERP ID of the record
        """
        if external_identifier:
            expected_oe_id = self._get_openerp_id(
                    external_identifier, referential)
            # OpenERP cleans up the references in ir.model.data to deleted
            # records only on server updates to avoid performance
            # penalty. Thus, we check if the record really still exists.
            if expected_oe_id:
                if self.model.exists(self.session.cr,
                                     self.session.uid,
                                     expected_oe_id,
                                     context=self.session.context):
                    return expected_oe_id
        return False

    def to_external(self, referential, openerp_id):
        """ Give the external ID for an OpenERP ID

        :param referential_id: id of the external.referential
        :param openerp_id: OpenERP ID for which we want the
            external id
        :return: `ExternalIdentifier` of the record
        """
        data_obj = self.session.pool.get('ir.model.data')
        model_data_ids = data_obj.search(
                self.session.cr,
                self.session.uid,
                [('model', '=', self.model._name),
                 ('res_id', '=', openerp_id),
                 ('referential_id', '=', referential.id)],
                context=self.session.context)
        if model_data_ids:
            prefixed_id = data_obj.read(self.session.cr,
                                        self.session.uid,
                                        model_data_ids[0],
                                        ['name'])['name']
            return self._extid_from_prefixed_id(prefixed_id)
        return False

    def bind(self, referential, external_identifier, openerp_id):
        """ Create the link between an external ID and an OpenERP ID

        :param referential_id: id of the external.referential
        :param external_identifier: `ExternalIdentifier` to bind
        :param openerp_id: OpenERP ID to bind
        """
        assert isinstance(external_identifier, ExternalIdentifier), (
                "external_identifier must be an ExternalIdentifier")

        _logger.debug('bind openerp_id %s with external_id %s',
                      openerp_id, external_identifier.id)

        bind_vals = self._prepare_bind_vals(referential,
                                            openerp_id,
                                            external_identifier)
        return self.session.pool.get('ir.model.data').create(
                self.session.cr, self.session.uid,
                bind_vals, context=self.session.context)

    def _prepare_bind_vals(self, referential, openerp_id, external_identifier):
        """ Create an external reference for a resource id in the
        ir.model.data table
        """
        ext_ref_obj = self.session.pool.get('external.referential')
        module = 'extref/%s' % ext_ref_obj.read(self.session.cr,
                                                self.session.uid,
                                                referential.id,
                                                ['name'])['name']

        bind_vals = {
            'name': self._prefixed_id(external_identifier),
            'model': self.model._name,
            'res_id': openerp_id,
            'referential_id': referential.id,
            'module': module
            }
        return bind_vals


@Magento
class SaleOrderBinder(MagentoBinder):
    model_name = 'sale.order'


@Magento
class ResPartnerBinder(MagentoBinder):
    model_name = 'res.partner'

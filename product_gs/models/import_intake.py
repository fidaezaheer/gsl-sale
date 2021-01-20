
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

import functools
import itertools

import psycopg2
import pytz

from odoo import api, fields, models, _
from odoo.tools import ustr

class IrFieldsConverter(models.AbstractModel):
    _inherit = 'ir.fields.converter'

    @api.model
    def db_id_for_create(self, model, field, subfield, value):
        flush = self._context.get('import_flush', lambda arg=None: None)

        id = None
        warnings = []
        error_msg = ''
        action = {
            'name': 'Possible Values',
            'type': 'ir.actions.act_window', 'target': 'new',
            'view_mode': 'tree,form',
            'views': [(False, 'list'), (False, 'form')],
            'context': {'create': False},
            'help': _(u"See all possible values")}
        if subfield is None:
            action['res_model'] = field.comodel_name
        elif subfield in ('id', '.id'):
            action['res_model'] = 'ir.model.data'
            action['domain'] = [('model', '=', field.comodel_name)]

        RelatedModel = self.env[field.comodel_name]
        field_type = _(u"name")
        if value == '':
            return False, field_type, warnings
        flush()
        try:
            id, _name = RelatedModel.name_create(name=value)
        except (Exception, psycopg2.IntegrityError):
            error_msg = _(u"Cannot create new '%s' records from their name alone. Please create those records manually and try importing again.") % RelatedModel._description

        if id is None:
            if error_msg:
                message = _("No matching record found for %(field_type)s '%(value)s' in field '%%(field)s' and the following error was encountered when we attempted to create one: %(error_message)s")
            else:
                message = _("No matching record found for %(field_type)s '%(value)s' in field '%%(field)s'")
            raise self._format_import_error(
                ValueError,
                message,
                {'field_type': field_type, 'value': value, 'error_message': error_msg},
                {'moreinfo': action})
        return id, field_type, warnings

    @api.model
    def _str_to_many2one(self, model, field, values):
        # Should only be one record, unpack
        [record] = values

        subfield, w1 = self._referencing_subfield(record)
        if model._name == 'stock.move' and field.name == 'product_id':
            id, _, w2 = self.db_id_for_create(model, field, subfield, record[subfield])
        else:
            id, _, w2 = self.db_id_for(model, field, subfield, record[subfield])
        return id, w1 + w2
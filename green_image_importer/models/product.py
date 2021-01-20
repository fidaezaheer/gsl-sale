
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

import re

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from itertools import groupby
from odoo.tools import float_is_zero

import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def import_images(self):
        return {
            'name': _('Import Images(Code)'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'green.image.import.tmpl',
            'context': {'default_line_ids': [(0,0,{'product_id': product_id}) for product_id in self.ids]
            ,'active_ids':self.id},
            'target': 'new'
        }

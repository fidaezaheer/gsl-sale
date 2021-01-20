
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductImage(models.TransientModel):
    _name = 'product.image.change'
    _description = 'Product Image Change Wizard'

    product_id = fields.Many2one(comodel_name='product.template', readonly=True)
    image_1920 = fields.Image("Image", related='product_id.image_1920', readonly=False)

    def save(self):
        return {'type': 'ir.actions.act_window_close'}
        
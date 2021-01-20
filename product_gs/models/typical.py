
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductTypical(models.Model):
    _name = 'product.typical'
    _description = 'Product Typical'

    _rec_name = 'name'
    _order = 'sequence ASC'

    name = fields.Char(string='Name', required=True, default=lambda self: _('New'), copy=False)
    sequence = fields.Char()

    parent_id = fields.Many2one(string='Parent Typical', comodel_name='product.typical', ondelete='restrict', index=True)
    product_qty = fields.Float(string='Quantity',)
    product_uom = fields.Many2one(string='Unit of Measurement', comodel_name='uom.uom', ondelete='restrict', 
        default=lambda self: self.env.ref('uom.product_uom_unit').id)
    currency_id = fields.Many2one('res.currency', 'Currency', compute='_compute_currency_id')
    fair_market_value = fields.Float('Fair market value', digits='Product Price')
    unit_weight = fields.Float("Unit Weight (in Short tonnes)",digits='Typicals value unit weight')
    aluminum = fields.Float("% Aluminum",digits='Typicals value')
    steel = fields.Float("% Steel",digits='Typicals value')
    copper = fields.Float("% Copper",digits='Typicals value')
    glass = fields.Float("% Glass",digits='Typicals value')
    plastics = fields.Float("% Plastics",digits='Typicals value')
    wood = fields.Float("% Wood",digits='Typicals value')
    mixed_metals = fields.Float("% Mixed Metals",digits='Typicals value')
    mixed_plastics = fields.Float("% Mixed Plastics",digits='Typicals value')
    carpet = fields.Float("% Carpet",digits='Typicals value')
    personal_computers = fields.Float("% Personal Computers",digits='Typicals value')
    concrete = fields.Float("% Concrete",digits='Typicals value')
    drywall = fields.Float("% Drywall",digits='Typicals value')
    fiberglass = fields.Float("% Fiberglass",digits='Typicals value')
    vinyl_flooring = fields.Float("% Vinyl Flooring",digits='Typicals value')
    wood_flooring = fields.Float("% Wood Flooring",digits='Typicals value')
    cubic_feet = fields.Float("Cubic Feet",digits='Typicals value')

    def _compute_currency_id(self):
        main_company = self.env['res.company']._get_main_company()
        for typical in self:
            typical.currency_id = main_company.currency_id.id
    

class FactorTable(models.Model):
    _name = 'factor.table'
    _description = 'Factor Table'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(string='Name',required=True,copy=False, readonly=True)
    code = fields.Char(required=True,copy=False,index=True, readonly=True )
    sr_factor = fields.Float(string="SR Factor", digits='Factors table')
    recycle_factor = fields.Float(digits='Factors table')    

    def get_sr_dict(self):
        return {l.code: l.sr_factor for l in self.search([])}
    
    def get_recycle_dict(self):
        return {l.code: l.recycle_factor for l in self.search([])}
    
    
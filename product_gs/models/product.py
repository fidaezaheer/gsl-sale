
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



class ProductProduct(models.Model):
    _inherit = 'product.product'

    intake_qty = fields.Float("Initial quantity", digits='Product Unit of Measure', default=0.0)
    sale_line_ids = fields.One2many(string='Sale Lines', comodel_name='sale.order.line', inverse_name='product_id',)
    donation_qty = fields.Float("Donation", digits='Product Unit of Measure', compute='_get_disposition_qty')
    resale_qty = fields.Float("Resale", digits='Product Unit of Measure', compute='_get_disposition_qty')
    relocate_qty = fields.Float("Relocate", digits='Product Unit of Measure', compute='_get_disposition_qty')
    recycle_qty = fields.Float("Recycle", digits='Product Unit of Measure', compute='_get_disposition_qty')
    landfill_qty = fields.Float("Landfill", digits='Product Unit of Measure', compute='_get_disposition_qty')
    request_qty = fields.Float("Requested", digits='Product Unit of Measure', compute='_get_disposition_qty')
    delivered_qty = fields.Float("Delivered", digits='Product Unit of Measure', compute='_get_disposition_qty')
    placed_qty = fields.Float("Placed", digits='Product Unit of Measure', compute='_get_disposition_qty')
    pending_request_qty = fields.Float("Pending requests", digits='Product Unit of Measure', compute='_get_disposition_qty')
    overflow_request_qty = fields.Float("Overflow", digits='Product Unit of Measure', compute='_get_disposition_qty')
    unrequest_qty = fields.Float("Unrequested", digits='Product Unit of Measure', compute='_get_disposition_qty')
    default_code = fields.Char('Internal Reference', index=True, compute='get_photo_id', store=True)

    @api.depends('typical_id.sequence','typical_id.parent_id.sequence','photo_id')
    def get_photo_id(self):
        for product in self:
            default_code = '#%s%s' % (product.typical_id.parent_id.sequence or '0', product.typical_id.sequence or '0')
            if product.photo_id:
                default_code = '%s-%s' % (default_code, product.photo_id_wo_ext)
            product.update({
                'default_code': default_code
            })

    @api.depends('sale_line_ids.product_uom_qty', 'sale_line_ids.state','sale_line_ids.requested_qty', 'sale_line_ids.qty_delivered')
    def _get_disposition_qty(self):
        for product in self:
            request_qty = sum(product.sale_line_ids.filtered(lambda line: line.state not in ('cancel', 'draft')).mapped('requested_qty'))
            sale_lines = product.sale_line_ids.filtered(lambda line: line.state in ('sale', 'done'))
            placed_qty = sum(sale_lines.mapped('product_uom_qty'))
            delivered_qty = sum(sale_lines.mapped('qty_delivered'))
            pending_request_qty = request_qty - placed_qty
            overflow_request_qty = request_qty - product.intake_qty if (request_qty > product.intake_qty) else 0.0
            unrequest_qty = product.intake_qty - request_qty if (request_qty < product.intake_qty) else 0.0
            qty_dict = {
                'donation_qty': 0.0,
                'resale_qty': 0.0,
                'relocate_qty': 0.0,
                'recycle_qty': 0.0,
                'landfill_qty': 0.0,
                'request_qty': request_qty,
                'placed_qty': placed_qty,
                'delivered_qty': delivered_qty,
                'pending_request_qty': pending_request_qty,
                'overflow_request_qty': overflow_request_qty,
                'unrequest_qty': unrequest_qty
            }
            for key, group in groupby(sale_lines.sorted(lambda line: line.disposition_type_id), lambda line: line.disposition_type_id.code):
                if key:
                    groupe_lines = list(group)
                    total_qty = 0.0
                    for line in groupe_lines:
                        total_qty += line.product_uom_qty
                    qty_dict.update({
                        '%s_qty'%key: total_qty
                    })
            product.update(qty_dict)

    def name_get(self):
        res = super(ProductProduct, self).name_get()
        if not self.env.context.get('show_stock', False):
            return res
        res_with_stock = []
        for product_id, name in res:
            stock = self.browse(product_id).virtual_available
            res_with_stock.append((product_id, '%s - %.0f'%(name, stock)))
        return res_with_stock

    def sort_by_photoid(self):
        def sortp(product):
            num, text = re.match('^(\d*)(.*)',product.photo_id_wo_ext).groups()
            return (int(num or '0'), text)
        return self.sorted(lambda p: sortp(p))

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    typical_id = fields.Many2one(string='Typical',comodel_name='product.typical',ondelete='restrict',index=True)
    phase_id = fields.Many2one(string='Phase',comodel_name='gs.project.phase',ondelete='restrict',index=True, readonly=True)
    project_id = fields.Many2one(string='Project',comodel_name='gs.project',related='phase_id.project_id')
    currency_id = fields.Many2one('res.currency', 'Currency', related='typical_id.currency_id')

    typical_fmv = fields.Float('Fair market value', digits='Product Price', related='typical_id.fair_market_value')
    override_fmv = fields.Float('Override FMV', digits='Product Price')
    typical_unit_weight = fields.Float("Unit Weight (in LBS)",digits='Typicals value', related='typical_id.unit_weight')
    override_uw = fields.Float("Override Unit Weight (in LBS)",digits='Typicals value')
    aluminum = fields.Float(related='typical_id.aluminum',digits='Typicals value')
    steel = fields.Float(related='typical_id.steel',digits='Typicals value')
    copper = fields.Float(related='typical_id.copper',digits='Typicals value')
    glass = fields.Float(related='typical_id.glass',digits='Typicals value')
    plastics = fields.Float(related='typical_id.plastics',digits='Typicals value')
    wood = fields.Float(related='typical_id.wood',digits='Typicals value')
    mixed_metals = fields.Float(related='typical_id.mixed_metals',digits='Typicals value')
    mixed_plastics = fields.Float(related='typical_id.mixed_plastics',digits='Typicals value')
    carpet = fields.Float(related='typical_id.carpet',digits='Typicals value')
    personal_computers = fields.Float(related='typical_id.personal_computers',digits='Typicals value')
    concrete = fields.Float(related='typical_id.concrete',digits='Typicals value')
    drywall = fields.Float(related='typical_id.drywall',digits='Typicals value')
    fiberglass = fields.Float(related='typical_id.fiberglass',digits='Typicals value')
    vinyl_flooring = fields.Float(related='typical_id.vinyl_flooring',digits='Typicals value')
    wood_flooring = fields.Float(related='typical_id.wood_flooring',digits='Typicals value')
    cubic_feet = fields.Float(related='typical_id.cubic_feet',digits='Typicals value',store=True)
    unit_weight = fields.Float(compute='_get_unit_weight',digits='Typicals value')
    fair_market_value = fields.Float(compute='_get_fmv',digits='Typicals value')

    
    make_id = fields.Many2one(string='Make',comodel_name='product.template.make',ondelete='set null',)
    model_id = fields.Many2one(string='Model',comodel_name='product.template.model',ondelete='set null',)
    condition = fields.Selection(selection=[('new', 'New'), ('good', 'Good'),('poor', 'Poor')])
    dimensions = fields.Char()
    building = fields.Char(string='Building location',)
    

    @api.depends('typical_id.unit_weight', 'override_uw')
    def _get_unit_weight(self):
        decimal_precision = self.env['decimal.precision'].precision_get('Typicals value')
        for Product in self:
            if float_is_zero(Product.override_uw,precision_digits=decimal_precision):
                Product.unit_weight = Product.typical_unit_weight
            else:
                Product.unit_weight = Product.override_uw
    

    @api.depends('typical_id.fair_market_value', 'override_fmv')
    def _get_fmv(self):
        decimal_precision = self.env['decimal.precision'].precision_get('Typicals value')
        for Product in self:
            if float_is_zero(Product.override_fmv,precision_digits=decimal_precision):
                Product.fair_market_value = Product.typical_fmv
            else:
                Product.fair_market_value = Product.override_fmv

    type = fields.Selection(default='product')
    default_code = fields.Char(readonly=True )
    photo_id = fields.Char(string='Photo ID',)
    photo_id_wo_ext = fields.Char(string='Photo ID wihtout extension', compute='_photo_id_remove_ext')

    @api.depends('photo_id')
    def _photo_id_remove_ext(self):
        for product in self:
            if product.photo_id:
                product.photo_id_wo_ext = re.split('\.[a-zA-Z]+$', product.photo_id)[0]
            else:
                product.photo_id_wo_ext = ''

    def action_image_change(self):
        return {
            'name': _('Change Product Image'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'product.image.change',
            'context': {
                'default_product_id': self.id
            },
            'target': 'new'
        }

    def generate_mailout(self):
        return {
            'name': _('Mailout'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mailout.list',
            'context': {'default_line_ids': [(0,0,{'product_id': product_id}) for product_id in self.ids]},
            'target': 'new'
        }
    
    # @api.model_create_multi
    # def create(self, vals_list):
    #     templates = super(ProductTemplate, self).create(vals_list)
    #     for template in templates:
    #         if template.typical_id:
    #             template.write({
    #                 'website_sequence': template.typical_id.sequence,
    #             })
    #     return templates

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if vals.get('typical_id', False) or vals.get('photo_id', False):
            self.env['product.product'].invalidate_cache(fnames=['default_code'])
        return res

class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    mailout = fields.Boolean('Mailout', default=False)
    request_type = fields.Selection(string='Request type', selection=[('resale', 'Employee Resale')])
    delivery_ids = fields.Many2many(string='Delivery', comodel_name='delivery.carrier', relation='mailout_category_rel',column1='delivery_id',column2='category_id',)

    def open_mailout(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/shop/category/%s' % self.id,
            'target': 'new',
            'target_type': 'public',
        }



class Make(models.Model):
    _name = 'product.template.make'
    _description = 'Product Make'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(string='Name',required=True,default=lambda self: _('New'),copy=False)

    
class Model(models.Model):
    _name = 'product.template.model'
    _description = 'Product model'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(string='Name',required=True,default=lambda self: _('New'),copy=False)

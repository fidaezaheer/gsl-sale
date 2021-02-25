
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    project_id = fields.Many2one(string='Project',comodel_name='gs.project',related='phase_id.project_id')
    phase_id = fields.Many2one(string='Phase',comodel_name='gs.project.phase')
    disposition_type_id = fields.Many2one(comodel_name='disposition.type', related='sale_id.disposition_type_id', store=True, index=True)

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for picking in self:
            if picking.picking_type_code == 'incoming' and picking.phase_id:
                Products = picking.mapped('move_lines').filtered(lambda m: m.state == 'done').mapped('product_id')
                Products.write({
                    'phase_id': picking.phase_id
                })
                picking.phase_id.message_post(body='Intake operation validated <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a>'%(picking.id, picking.name))
            else:
                phase = picking.mapped('move_lines').mapped('product_id').mapped('phase_id')
                if len(phase) != 1:
                    raise ValidationError('Products must be from same project/phase.')
                else:
                    phase.message_post(body='Placement validated <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a>'%(picking.id, picking.name))
        self.action_create_pricelist_items()
        return res

    def action_create_pricelist_items(self):
        self.mapped('move_lines').action_create_pricelist_items()

class StockMove(models.Model):
    _inherit = 'stock.move'

    disposition_type_id = fields.Many2one(comodel_name='disposition.type', related='picking_id.disposition_type_id', store=True, index=True)
    typical_id = fields.Many2one(string='Typical',comodel_name='product.typical',related='product_id.typical_id', readonly=False)
    project_id = fields.Many2one(string='Project',comodel_name='gs.project',related='picking_id.project_id')
    phase_id = fields.Many2one(string='Phase',comodel_name='gs.project.phase', related='picking_id.phase_id')
    requested_qty = fields.Float(string='Requested', digits='Product Unit of Measure', related='sale_line_id.requested_qty', store=True)
    image_1920 = fields.Image(related='product_id.product_tmpl_id.image_1920', readonly=False)
    photo_id = fields.Char(related='product_id.photo_id', readonly=False)    

    make_id = fields.Many2one(comodel_name='product.template.make', related='product_id.make_id', readonly=False)
    model_id = fields.Many2one(comodel_name='product.template.model', related='product_id.model_id', readonly=False)
    condition = fields.Selection(related='product_id.condition', readonly=False)
    dimensions = fields.Char(related='product_id.dimensions', readonly=False)
    building = fields.Char(related='product_id.building', readonly=False)
    description_sale = fields.Text(related='product_id.description_sale', readonly=False)
    list_price = fields.Float('Sales Price', digits='Product Price', related='product_id.list_price', readonly=False)
    pricelist_name = fields.Char(string='Pricelist',)
    pricelist_value = fields.Char(string='Value',)
    

    reserved_availability = fields.Float(
        'Reserved', compute='_compute_reserved_availability',
        digits='Product Unit of Measure',
        readonly=True, help='Quantity that has already been reserved for this move', store=True)
    quantity_done = fields.Float('Quantity Done', compute='_quantity_done_compute', digits='Product Unit of Measure', inverse='_quantity_done_set', store=True)
    actual_quantity_done = fields.Float('Done', compute='_actual_done_compute', digits='Product Unit of Measure', store=True)
    
    @api.depends('quantity_done', 'returned_move_ids.quantity_done')
    def _actual_done_compute(self):
        for move in self:
            move.actual_quantity_done = move.quantity_done - sum(move.returned_move_ids.mapped('quantity_done'))
    
    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder)
        for move in self:
            if move.picking_code == 'incoming' and move.picking_id.phase_id:
                move.product_id.intake_qty += move.product_uom_qty
        return res
    
    def action_create_pricelist_items(self):
        Pricelist = self.env['product.pricelist']
        Item = self.env['product.pricelist.item']
        for move in self:
            pt = move.product_id.product_tmpl_id.id
            for pricelist, value in zip(move.pricelist_name.split(','), move.pricelist_value.split(',')):
                try:
                    price_value = float(value)
                except:
                    price_value = 0
                if price_value <= 0:
                    continue
                pricelist = Pricelist.search([('name','=ilike',pricelist)], limit=1)
                if not pricelist:
                    continue
                item = Item.search([('product_tmpl_id','=',pt), ('pricelist_id','=',pricelist.id)], limit=1)
                if item:
                    item.write({
                        'applied_on': '1_product',
                        'compute_price': 'fixed',
                        'fixed_price': price_value,
                    })
                else:
                    item = Item.create({
                        'applied_on': '1_product',
                        'product_tmpl_id': pt,
                        'compute_price': 'fixed',
                        'fixed_price': price_value,
                        'pricelist_id': pricelist.id
                    })

    

# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.http_routing.models.ir_http import slug


class MailoutList(models.TransientModel):
    _name = 'mailout.list'
    _description = 'Mailout products list'

    _rec_name = 'name'
    _order = 'name ASC'


    name = fields.Char(string='Name', required=True, default=lambda self: _('New'), copy=False)
    line_ids = fields.One2many(string='Products', comodel_name='mailout.list.line', inverse_name='list_id',)            
    request_type = fields.Selection(string='Request type', selection=[('resale', 'Employee Resale')], default='resale')
    
    delivery_ids = fields.Many2many(string='Delivery', comodel_name='delivery.carrier', relation='mailout_delivery_rel',column1='delivery_id',column2='mailout_id',)     

    def action_mailout(self):
        mailout = self.env['product.public.category'].create({
            'name': self.name,
            'mailout': True,
            'request_type': self.request_type,
            'delivery_ids': [(6, 0, self.delivery_ids.ids)],
        })
        self.line_ids.mapped('product_id').write({
            'public_categ_ids': [(4, mailout.id, False)],
            'is_published': True,
            'sale_ok': True,
        })
        
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'product.public.category',
            'res_id': mailout.id
        }
        

class MailoutListLine(models.TransientModel):
    _name = 'mailout.list.line'
    _description = 'Mailout products list line'

    _rec_name = 'product_id'
    _order = 'sequence ASC'
    
    product_id = fields.Many2one(string='Product', comodel_name='product.template',ondelete='restrict',)
    list_id = fields.Many2one(comodel_name='mailout.list', ondelete='cascade',)
    sequence = fields.Integer(default=10)
    
    
    

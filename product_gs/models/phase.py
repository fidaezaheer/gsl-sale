
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

import datetime
from math import ceil
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
from operator import itemgetter
from odoo.tools import float_is_zero


class GSProjectPhase(models.Model):
    _name = 'gs.project.phase'
    _description = 'GS Project Phase'

    _inherit = ['mail.thread', 'mail.activity.mixin']


    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(string='Name', required=True, default=lambda self: _('New Phase'), copy=False)
    project_id = fields.Many2one(string='Project', comodel_name='gs.project',ondelete='restrict', required=True,)
    phase_company_id = fields.Many2one(string='Company', comodel_name='res.partner', ondelete='set null')
    active = fields.Boolean(default=True)

    pdp_printed = fields.Boolean(default=False)

    project_pm_lead_id = fields.Many2one(string='Project PM Lead', comodel_name='res.partner', ondelete='set null')
    pc_lead_id = fields.Many2one(string='PC Lead', comodel_name='res.partner', ondelete='set null')
    project_bdm = fields.Many2one(string='Project BDM ', comodel_name='res.partner', ondelete='set null')
    project_bdm2 = fields.Many2one(string='Project BDM 2', comodel_name='res.partner', ondelete='set null')
    # project_bdm = fields.Char(string='Project BDM',)
    # project_bdm2 = fields.Char(string='Project BDM 2',)
    portfolio = fields.Char(string='Portfolio',)
    address = fields.Char(string='Project Address',)
    decom_start = fields.Date(string='Decom start',default=fields.Date.context_today,)
    decom_end = fields.Date(string='Decom end',default=fields.Date.context_today,)
    
    number = fields.Char(string='Phase #', copy=False, store=True)
    product_ids = fields.One2many(string='Items', comodel_name='product.template', inverse_name='phase_id')
    product_variant_ids = fields.One2many(string='Item variants', comodel_name='product.product', inverse_name='phase_id')

    override_recycling_wood = fields.Float(string='Wood Recycling',)
    override_recycling_metal = fields.Float(string='Metal Recycling',)
    override_landfill = fields.Float(string='Landfill',)
    override_recycle = fields.Float(string='Recycling',compute='_get_total_recycle')

    dg_donation = fields.Integer(string='Donation %',)
    dg_resale = fields.Integer(string='Resale %',)
    dg_relocate = fields.Integer(string='Relocate %',)
    dg_recycle = fields.Integer(string='Recycle %',)
    dg_landfill = fields.Integer(string='Landfill %',)   
    
    total_cubic_feet = fields.Float(string='Total',compute='_get_total_cubic_feet')
    truck_count = fields.Integer(string='Truck count',compute='_get_total_cubic_feet')

    @api.depends('product_variant_ids.intake_qty', 'product_variant_ids.cubic_feet')
    def _get_total_cubic_feet(self):
        for phase in self:
            total = sum(phase.product_variant_ids.mapped(lambda p: p.intake_qty * p.cubic_feet))
            phase.total_cubic_feet = total
            phase.truck_count = ceil(total/700.0)
            

    @api.constrains('dg_donation','dg_resale','dg_relocate','dg_recycle','dg_landfill')
    def _check_dg_percentage(self):
        for record in self:
            total = sum([record.dg_donation, record.dg_resale,record.dg_relocate,record.dg_recycle,record.dg_landfill])
            if total > 100:
                raise ValidationError("Percentage must be in total 100%")
    

    @api.depends('override_recycling_wood','override_recycling_metal')
    def _get_total_recycle(self):
        for phase in self:
            phase.override_recycle = phase.override_recycling_wood + phase.override_recycling_metal

    def action_open_mailouts(self):
        mailouts = self.env['product.public.category'].search([('product_tmpl_ids','=',self.product_ids.ids),('mailout','=',True)])
        return {
            'name': _('Mailouts'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'product.public.category',
            'domain': [('id', 'in', mailouts.ids)],
        }
        
    def action_open_valuator(self):
        Tree = self.env.ref('product_gs.view_phase_valuator', False)
        return {
            'name': 'FMV/Wt Overide: %s'%self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,kanban,form',
            'res_model': 'product.template',
            'views': [[Tree.id, 'tree'],[False, 'kanban'],[False,'form']],
            'domain': [('id', 'in', self.product_ids.ids)],
        }

    def action_open_itemreport(self):
        Tree = self.env.ref('product_gs.item_report_list_view', False)
        return {
            'name': 'Item report: %s'%self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'product.product',
            'views': [[Tree.id, 'tree']],
            'domain': [('id', 'in', self.product_ids.product_variant_ids.ids)],
        }
        
    def action_open_requests(self):
        product_variant_ids = self.product_ids.product_variant_ids
        orders = self.env['sale.order.line'].search([('product_id','in',product_variant_ids.ids)]).mapped('order_id')
        return {
            'name': 'Requests: %s'%self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('id', 'in', orders.ids)],
            'context': {'search_default_requests_pending': True}
        }
    
    def action_open_requestlines(self):
        Tree = self.env.ref('product_gs.requests_tree_view')
        product_variant_ids = self.product_ids.product_variant_ids
        order_lines = self.env['sale.order.line'].search([('product_id','in',product_variant_ids.ids)])
        return {
            'name': 'Requests: %s'%self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'tree, pivot',
            'res_model': 'sale.order.line',
            'domain': [('id', 'in', order_lines.ids)],
            'views': [[Tree.id, 'tree'], [False, 'pivot']],
            'context': {'search_default_pending_requests': True}
        }

    def action_open_placements(self):
        product_variant_ids = self.product_ids.product_variant_ids
        moves = self.env['stock.move'].search([('product_id','in',product_variant_ids.ids),('picking_code','=','outgoing'),('state','!=','cancel')])
        return {
            'name': _('Placements'),
            'type': 'ir.actions.act_window',
            'view_mode': 'pivot,tree',
            'res_model': 'stock.move',
            'domain': [('id', 'in', moves.ids)],
        }
    def action_open_deliveries(self):
        product_variant_ids = self.product_ids.product_variant_ids
        moves = self.env['stock.move'].search([('product_id','in',product_variant_ids.ids),('picking_code','=','outgoing')])
        pickings = moves.mapped('picking_id')
        Action = self.env.ref('stock.action_picking_tree_all').read()[0]
        return dict(Action, domain=[('id','in',pickings.ids)])
        
    def _get_attachment_name(self):
        return '%s-%s'%(self.name, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def action_print_pdp(self):
        ReportAction = self.env.ref('product_gs.action_report_pdp')
        attachment, pdf = ReportAction._render_qweb_pdf(self.ids)
        self.pdp_printed = True
        print_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.message_post(body='PDP report printed on %s.'%print_time, attachments = [('%s-%s'%(self.name, print_time), attachment)])
        return ReportAction.report_action(self)

    def get_disposition_weights(self):
        self.ensure_one()
        sale_lines = self.env['sale.order.line'].search([('product_id','in',self.product_ids.product_variant_ids.ids),('state','in',('sale', 'done'))])
        disposition_types = self.env['disposition.type'].search([])
        data = {dt.code:{'quantity':0, 'weight': 0.0} for dt in disposition_types}
        total_fmv = 0.0
        fmv_donate = 0.0
        for dt in disposition_types:
            dsl = sale_lines.filtered(lambda l: l.disposition_type_id == dt)
            data[dt.code]['weight'] = sum(dsl.mapped(lambda l: l.qty_delivered*l.product_id.unit_weight))
            data[dt.code]['quantity'] = sum(dsl.mapped('qty_delivered'))
            dfmv = sum(dsl.mapped(lambda l: l.qty_delivered*l.product_id.fair_market_value))
            total_fmv += dfmv
            if dt.code == 'donation':
                fmv_donate += dfmv
                
        total_qty = sum([value['quantity'] for key,value in data.items()])
        total_weight = sum([value['weight'] for key,value in data.items()])
        if not float_is_zero(total_weight, precision_digits=4):
            for key in data.keys():
                data[key]['percentage'] = (data[key]['weight']/total_weight * 100)
        else:
            for key in data.keys():
                data[key]['percentage'] = 0
        data.update({
            'total': {
                'quantity': total_qty,
                'weight': total_weight,
                'percentage': 100
            },
            'fmv': total_fmv,
            'fmv_donate': fmv_donate
        })
        return data

    def get_disposition_sr(self):
        self.ensure_one()
        factor_table = self.env['factor.table'].get_sr_dict()
        disposition_types = self.env['disposition.type'].search([('code','in',('donation','resale','relocate'))])
        sale_lines = self.env['sale.order.line'].search([('product_id','in',self.product_ids.product_variant_ids.ids),('state','in',('sale', 'done')),('disposition_type_id','in',disposition_types.ids)])
        data = 0.0
        for l in sale_lines:
            for key in factor_table.keys():
                data += l.qty_delivered * l.product_id.unit_weight * factor_table[key] * itemgetter(key)(l.product_id)
        sr = data
        return sr

    def get_recycle_sr(self):
        self.ensure_one()
        factor_table = self.env['factor.table'].get_recycle_dict()
        disposition_types = self.env['disposition.type'].search([('code','in',('recycle',))])
        sale_lines = self.env['sale.order.line'].search([('product_id','in',self.product_ids.product_variant_ids.ids),('state','in',('sale', 'done')),('disposition_type_id','in',disposition_types.ids)])
        data = 0.0
        weight = 0.0
        for l in sale_lines:
            for key in factor_table.keys():
                data += l.qty_delivered * l.product_id.unit_weight * factor_table[key] * itemgetter(key)(l.product_id)
            weight += l.qty_delivered * l.product_id.unit_weight
        if not float_is_zero(weight, precision_digits=3):
            if not float_is_zero(self.override_recycle, precision_digits=3):
                override_factor = self.override_recycle/weight
            else:
                override_factor = 1
            return data * override_factor
        else:
            return 0

    def action_override(self):
        view = self.env.ref('product_gs.phase_override_wizard')
        return {
            'name': _('Overrides'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'view_id': view.id,
            'target': 'new'
        }
    
    def override_save(self):
        self.ensure_one()
        self.message_post(body="Override values added.")
        return {'type': 'ir.actions.act_window_close'}
        
    
    def _get_los_data(self):
        self.ensure_one()
        value_to_html = self.env['ir.qweb.field.float'].value_to_html
        items = self.product_ids.product_variant_ids
        sale_lines = self.env['sale.order.line'].search([('state','not in', ('draft', 'cancel', 'sent')),('product_id','in',items.ids)])
        dispositions = self.env['disposition.type'].search([])
        partners = sale_lines.sorted(lambda s: s.disposition_type_id.sequence).mapped('order_partner_id')
        items_data = []
        for item in items:
            item_qty = []
            item_sale_lines = sale_lines.filtered(lambda l: l.product_id == item)
            closed_qty = sum(item_sale_lines.mapped('product_uom_qty'))
            item_qty.append(value_to_html(item.intake_qty, {'decimal_precision': 'Product Unit of Measure'}))
            item_qty.append(value_to_html(closed_qty, {'decimal_precision': 'Product Unit of Measure'}))
            item_qty.append(value_to_html(item.virtual_available, {'decimal_precision': 'Product Unit of Measure'}))
            for disposition in dispositions:
                total_qty = sum(item_sale_lines.filtered(lambda l: l.disposition_type_id == disposition).mapped('product_uom_qty'))
                item_qty.append(value_to_html(total_qty, {'decimal_precision': 'Product Unit of Measure'}))
            for partner in partners:
                total_qty = sum(item_sale_lines.filtered(lambda l: l.order_partner_id == partner).mapped('product_uom_qty'))
                item_qty.append(value_to_html(total_qty, {'decimal_precision': 'Product Unit of Measure'}))
            items_data.append({'item': item, 'data': item_qty})
        return {
            'lines': items_data,
            'dispositions': dispositions,
            'partners': partners
        }
    def _get_placement_data(self):
        self.ensure_one()
        value_to_html = lambda val: self.env['ir.qweb.field.float'].value_to_html(val, {'decimal_precision': 'Product Unit of Measure'})
        items = self.product_ids.product_variant_ids
        if self.env.context.get('selected', False):
            sale_lines = self.env['sale.order.line'].search([('state','not in', ('draft', 'cancel')),('product_id','in',items.ids),('tag_ids','ilike','selected')])
        else:
            sale_lines = self.env['sale.order.line'].search([('state','not in', ('draft', 'cancel')),('product_id','in',items.ids)])
        partners = sale_lines.sorted(lambda s: s.disposition_type_id.sequence).mapped('order_partner_id')
        get_code = lambda p: sale_lines.filtered(lambda l: l.order_partner_id == p)[0].disposition_type_id.name
        items_data = []
        for item in items:
            item_qty = []
            item_sale_lines = sale_lines.filtered(lambda l: l.product_id == item)
            approved_qty = sum(item_sale_lines.mapped('product_uom_qty'))
            # requested_qty = sum(item_sale_lines.mapped('requested_qty'))
            # delivered_qty = sum(item_sale_lines.mapped('qty_delivered'))
            # item_qty.append(value_to_html(item.intake_qty))
            item_qty.append(value_to_html(item.virtual_available))
            item_qty.append(value_to_html(approved_qty))
            # item_qty.append(value_to_html(approved_qty-delivered_qty))
            # item_qty.append(value_to_html(delivered_qty))
            for partner in partners:
                partner_lines = item_sale_lines.filtered(lambda l: l.order_partner_id == partner)
                approved_qty = sum(partner_lines.mapped('product_uom_qty'))
                requested_qty = sum(partner_lines.mapped('requested_qty'))
                # delivered_qty = sum(partner_lines.mapped('qty_delivered'))
                item_qty.append(value_to_html(requested_qty))
                # item_qty.append(value_to_html(approved_qty-delivered_qty))
                item_qty.append(value_to_html(approved_qty))
            items_data.append({'item': item, 'data': item_qty})
        return {
            'lines': items_data,
            'partners': [(partner, get_code(partner)) for partner in partners]
        }

    def action_archive(self):
        self.mapped('product_ids').action_archive()
        return super(GSProjectPhase, self).action_archive()
    
    def action_unarchive(self):
        self.with_context(active_test=False).mapped('product_ids').action_unarchive()
        return super(GSProjectPhase, self).action_unarchive()

    def get_unrequested_items(self):
        return self.product_variant_ids.filtered(lambda p: p.unrequest_qty > 0)
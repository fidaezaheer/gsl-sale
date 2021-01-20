
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from operator import itemgetter
from odoo.tools import float_is_zero

class SummaryReport(models.TransientModel):
    _name = 'summary.report'
    _description = 'Summary Report'

    @api.model
    def get_html(self, given_context=None):
        res = self.search([('create_uid', '=', self.env.uid)], limit=1)
        if not res:
            return self.create({}).with_context(given_context)._get_html()
        return res.with_context(given_context)._get_html()
    
    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        value_convert = lambda value: self.env['ir.qweb.field.float'].value_to_html(value, {'decimal_precision': 'Summary report value'})
        qty_convert = lambda qty: self.env['ir.qweb.field.float'].value_to_html(qty, {'decimal_precision': 'Product Unit of Measure'})
        price_convert = lambda qty: self.env['ir.qweb.field.float'].value_to_html(qty, {'decimal_precision': 'Product Price'})
        phase = self.env['gs.project.phase'].browse(context.get('active_id'))
        closed = phase.get_disposition_weights()
        dispositions = self.env['disposition.type'].search([])
        products = phase.product_ids.mapped('product_variant_ids')
        open_qty = sum(products.mapped('qty_available'))
        open_weight = sum(products.mapped(lambda p: p.qty_available * p.unit_weight))
        intake_qty = sum(products.mapped('intake_qty'))
        intake_weight = sum(products.mapped(lambda p: p.intake_qty * p.unit_weight))
        intake_fmv = sum(products.mapped(lambda p: p.intake_qty * p.fair_market_value))
        
        weight_summary = [
            [
                "Total",
                qty_convert(intake_qty),
                value_convert(intake_weight),
                100,
                qty_convert(open_qty),
                value_convert(open_weight),
                100,
                qty_convert(closed['total']['quantity']),
                value_convert(closed['total']['weight']),
                closed['total']['percentage'],
                value_convert(intake_weight - closed['total']['weight']),
            ]
        ]

        for d in dispositions:
            goal = itemgetter("dg_%s"%d.code)(phase)
            goal_p = goal/100.0
            weight_data = [
                d.name,
                qty_convert(intake_qty*goal_p),
                value_convert(intake_weight*goal_p),
                goal,
                qty_convert(open_qty*goal_p),
                value_convert(open_weight*goal_p),
                goal,
                qty_convert(closed[d.code]['quantity']),
                value_convert(closed[d.code]['weight']),
                price_convert(closed[d.code]['percentage']),
                value_convert((intake_weight*goal_p) - closed[d.code]['weight']),
            ]
            weight_summary.append(weight_data)
        closed_estimate = {
            'sr': value_convert(closed['donation']['weight'] + closed['resale']['weight'] + closed['relocate']['weight']),
            'recycle': value_convert(closed['recycle']['weight']),
            'landfill': value_convert(closed['landfill']['weight']),
        }
        intake_estimate = {
            'sr': value_convert((phase.dg_donation + phase.dg_relocate + phase.dg_resale)/100 * intake_weight),
            'recycle': value_convert(phase.dg_recycle/100 * intake_weight),
            'landfill': value_convert(phase.dg_landfill/100 * intake_weight)
        }
        rcontext.update({
            'weight_summary': {
                'lines': weight_summary,
                'fmv': {
                    'intake_fmv': price_convert(intake_fmv),
                    'intake_donate_fmv': price_convert(intake_fmv*phase.dg_donation/100),
                    'closed_fmv': price_convert(closed['fmv']),
                    'closed_donate_fmv': price_convert(closed['fmv_donate']),
                }
            },
            'closed_estimate': closed_estimate,
            'intake_estimate': intake_estimate,
            'report': {
                'sr': value_convert(phase.get_disposition_sr()),
                'recycle_sr': value_convert(phase.get_recycle_sr()),
                'donation': value_convert(closed['donation']['weight']),
                'relocate': value_convert(closed['relocate']['weight']),
                'resale': value_convert(closed['resale']['weight']),
                'recycle': value_convert(phase.override_recycle if not float_is_zero(phase.override_recycle, precision_digits=3) else closed['recycle']['weight']),
                'landfill': value_convert(phase.override_landfill if not float_is_zero(phase.override_landfill, precision_digits=3) else closed['landfill']['weight']),
                'donate_fmv': price_convert(closed['fmv_donate']),
            } 
        })
        result['html'] = self.env.ref('product_gs.summary_report_base')._render(rcontext)
        return result
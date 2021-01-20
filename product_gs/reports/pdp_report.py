
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class PdpReport(models.AbstractModel):
    _name = 'report.product_gs.pdp_report_main'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('product_gs.pdp_report_main')
        docs = self.env[report.model].browse(docids)
        Products = docs.mapped('product_ids').mapped('product_variant_ids')
        orders = self.env['sale.order.line'].search([('product_id','in',Products.ids),('state','not in',('draft','sent','cancel')),('product_uom_qty','>',0.0)]).\
                mapped('order_id').sorted(lambda o: o.disposition_type_id.sequence)
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
            'orders': orders,
            'products': Products
        }
        return docargs

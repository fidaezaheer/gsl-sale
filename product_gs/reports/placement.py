
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PlacementReport(models.TransientModel):
    _name = 'placement.report'
    _description = 'Placement Report'

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
        phase = self.env['gs.project.phase'].browse(context.get('active_id'))
        rcontext.update(phase._get_placement_data())
        result['html'] = self.env.ref('product_gs.placement_report_base')._render(rcontext)
        return result

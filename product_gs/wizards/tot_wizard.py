
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class TotWizard(models.TransientModel):
    _name = 'tot.wizard'
    _description = 'Tot Wizard'

    order_id = fields.Many2one(comodel_name='sale.order',ondelete='cascade', required=True)
    tot_type = fields.Selection(string='Type',selection=[('Canada', 'Canada'), ('USA', 'USA'), ('TDSB', 'TDSB'), ('wf','WF')], default='Canada', required=True)

    def action_print(self):
        return self.order_id.action_print_tot(tot_type=self.tot_type)
    
    def action_close(self): 
        return {'type': 'ir.actions.act_window_close'}
            
    
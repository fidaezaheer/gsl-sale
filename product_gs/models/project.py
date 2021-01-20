
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class GSProject(models.Model):
    _name = 'gs.project'
    _description = 'GS Project'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(string='Name', required=True, default=lambda self: _('New Project'), copy=False)
    phase_ids = fields.One2many(string='Phases', comodel_name='gs.project.phase',inverse_name='project_id',)
    number = fields.Char(string='Project #', required=True, copy=False)


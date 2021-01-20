# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

# from ..quickbase.quickbase import QuickBase
from odoo.exceptions import UserError, ValidationError
import logging
import pyqb

class ResPartner(models.Model):
    """ Inherits partner and adds Quick Base integration information """
    # _name = 'res.partner'
    _inherit = 'res.partner'

    linkedin_url = fields.Char(string="LinkedIn Profile")
    # Common
    qb_image_url = fields.Char(string="Image URL")
    qb_google_address = fields.Char()
    qb_lat = fields.Char()
    qb_lng = fields.Char()
    qb_created_date = fields.Datetime()
    thumbnail_image = fields.Binary("Thumbnail Image", attachment=True)

    qb_account_id = fields.Integer(string="QB Account ID")
    qb_account_legacy_id = fields.Char(string="Account Legacy ID")
    qb_account_number = fields.Char(string="Account Number")
    qb_account_is_metric = fields.Boolean(string="Is Metric")
    qb_account_report_title = fields.Char(string="Report Title")
    qb_account_report_header = fields.Text(string="Report Header")
    qb_account_report_description = fields.Text(string="Report Description")
    qb_account_report_visibility = fields.Selection(
        [('Public', 'Public'), ('Internal only', 'Internal only'), ('With password', 'With password')],
        string="Visibility")

    # qb_account_phase_ids = fields.One2many('gsop.phase_reports', 'account_id', string="Phases")
    # Beneficiary Columns Start
    qb_beneficiary_id = fields.Integer(string="QB Beneficiary ID")
    qb_beneficiary_legacy_id = fields.Char(string="Beneficiary Legacy ID")
    # qb_beneficiary_posts_ids = fields.One2many('gsop.posts', 'beneficiary_id', string="Posts")
    # qb_beneficiary_phases_ids = fields.Many2many(relation='beneficiary_phase_rel', comodel_name='gsop.phase_reports',
    #                                              string="Beneficiary Phases")

    # Partners Columns Start
    qb_partner_id = fields.Integer(string="QB Partner ID")
    qb_partner_legacy_id = fields.Char(string="Partner Legacy ID")
    # qb_partner_phases_ids = fields.Many2many(relation='partner_phase_rel', comodel_name='gsop.phase_reports',
    #                                          string="Partners Phases")

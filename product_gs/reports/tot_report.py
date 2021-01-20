
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

VAT = {
    'wf': '501(c) 3 or Other Tax Registration #:',
    'Canada': 'CRA-issued or other Tax Registration #:',
    'USA': '501(c) 3 or Other Tax Registration #:',
    'TDSB': 'CRA-issued or other Tax Registration #:'
}


class TotReport(models.AbstractModel):
    _name = 'report.product_gs.tot_report_main'

    @api.model
    def _get_report_values(self, docids, data={}):
        tot_type = data.get('tot_type', 'Canada')
        tot_title = 'GreenStandards Transfer of Title'
        if tot_type != 'wf':
            tot_title = "%s - %s" % (tot_title, tot_type)
        docids = docids or data.get('docids')
        docargs = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': self.env['sale.order'].browse(docids),
            'tot_args': {
                'tot_type': tot_type,
                'title': tot_title,
                'vat_label': VAT[tot_type]
            }
        }
        return docargs

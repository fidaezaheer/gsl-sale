
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
import pyqb

_logger = logging.getLogger(__name__)

class GSProjectPhaseInherit(models.Model):
    _inherit = 'gs.project.phase'

    qb_id = fields.Integer(string='Quickbase Id')
    quote_date = fields.Date(string='Quote Date')
    qb_account_name = fields.Char(string='Account Name', copy=False)
    qb_report_id = fields.Integer(string='QB Report Id')
    # number = fields.Char(string='Phase #', copy=False, store=True)
    stream_id = fields.Integer(string='QB Stream Id', copy=False)
    proposals_only = fields.Boolean(string='Proposal-Only Inventory', default=False)

    def get_sale_orders(self):
        domain = [('order_line.product_id.product_tmpl_id.phase_id','=',self.id),
                  ('disposition_type_id.code','=','donation'),
                  ('state','=','sale')]
        return self.env['sale.order'].sudo().search(domain)

    
    def action_publish_report(self,phase):
        config = self.env['ir.config_parameter'].sudo()
        domain_url = config.search([('key', '=', 'quickbase_gs.quickbase_domainurl')]).value
        user_token = config.search([('key', '=', 'quickbase_gs.quickbase_usertoken')]).value
        phase_table_id = config.search([('key', '=', 'quickbase_gs.quickbase_phases_tableid')]).value
        beneficiary_table_id = config.search([('key', '=', 'quickbase_gs.quickbase_beneficiaries_tableid')]).value
        streams_table_id = config.search([('key', '=', 'quickbase_gs.quickbase_streams_tableid')]).value
        pha_ben_tableid = config.search([('key', '=', 'quickbase_gs.quickbase_phase_beneficiary_tableid')]).value
        _qbc = pyqb.Client(url=domain_url, user_token=user_token)
        sale_orders = self.get_sale_orders()
        ben_ids =[]
        description = ''
        response = {}
        phase_no = phase.number
        if not phase_no:
            return {"error":True,"description":"Error: No Phase # provided"}
        phase_qb = _qbc.doquery(query='{"phase_number".EX."%s"}' %phase_no, database=phase_table_id)  #Phase report      
        if 'record' not in phase_qb:
            return {"error":True,"description":"Error: No Phase report found on QuickBase for this phase"}
        for order in sale_orders:
            if order.partner_id:
                if order.partner_id.qb_beneficiary_id != False:
                    if 'record' in phase_qb:
                        phase_report_id = phase_qb['record']['record_id_']
                        pha_rep_ben = _qbc.doquery(query='{"phase_name".EX."%s"}' %phase_no, database=pha_ben_tableid)  #Phase report      
                        if 'record' in pha_rep_ben:
                            ben_list =[]
                            try:
                                ben_lists =  list(pha_rep_ben['record'])
                                for ben in ben_lists:
                                    ben_list.append(ben['related_beneficiary'])
                            except Exception as e:
                                ben_list.append(pha_rep_ben['record']['related_beneficiary'])
                            if str(order.partner_id.qb_beneficiary_id) not in ben_list:
                                data ={}
                                data['related_beneficiary']  = order.partner_id.qb_beneficiary_id
                                data['related_phase_report']  = phase_report_id
                                _qbc.addrecord(database=pha_ben_tableid, fields=data)
                if order.partner_id.qb_beneficiary_id == False or order.partner_id.qb_beneficiary_id == 0:
                    ben = self.gen_QBben_data(order.partner_id)
                    res = _qbc.addrecord(database=beneficiary_table_id, fields=ben)
                    if res['errcode'] == '0':
                        order.partner_id.write({'qb_beneficiary_id': res['rid']})
                        ben_ids.append(res['rid'])
                        if 'record' in phase_qb:
                            phase_report_id = phase_qb['record']['record_id_']
                            data ={}
                            data['related_beneficiary']  = res['rid']
                            data['related_phase_report']  = phase_report_id
                            _qbc.addrecord(database=pha_ben_tableid, fields=data)

        description += 'Created QB Beneficiary IDS:' +str(ben_ids) if len(ben_ids) > 0 else ''
        if not 'record' in phase_qb and phase_qb['errcode'] == '0':
            return {"error":True,"description":'Error: No phase found in Quickbase'}
        else:
            data = phase.get_disposition_weights()
            source_reduced_co2e__tonnes_ = phase.get_disposition_sr()
            recycled_reduced_co2e__tonnes_ = phase.get_recycle_sr()
            stream ={}
            stream['phase'] = phase_qb['record']['record_id_']
            stream['type'] = 'Furniture Assets'
            stream['donated'] = str(data['donation']['weight'])
            stream['recycled'] = str(phase.override_recycle) if phase.override_recycle != 0 or phase.override_recycle == False else data['resale']['weight']
            stream['resold'] = str(data['resale']['weight'])
            stream['relocated'] = str(data['relocate']['weight'])
            stream['landfilled'] = str(phase.override_landfill) if phase.override_landfill != 0 or phase.override_landfill == False else data['resale']['weight']
            stream['donation_fmv_'] = str(data['fmv_donate'])
            stream['source_reduced_co2e__tonnes_'] = source_reduced_co2e__tonnes_
            stream['recycled_reduced_co2e__tonnes_'] = recycled_reduced_co2e__tonnes_
            stream = self.gen_stream_data(stream, phase_qb['record']['record_id_'])
            # Create Stream
            if phase.stream_id == False:
                stream_qb = _qbc.addrecord(database=streams_table_id, fields=stream)
                if 'rid' in stream_qb:
                    description += " Stream Created in QB"
                    self.write({'stream_id': int(stream_qb['rid'])})
                return {"error":False,"description":description}
            else:
                try:
                    stream_rec = _qbc.editrecord(rid=phase.stream_id, database=streams_table_id, fields=stream)
                    description += " Stream modified in QB"
                except Exception as e:
                    stream_rec = _qbc.addrecord(database=streams_table_id, fields=stream)
                    description += " Stream Created in QB"
                    if 'rid' in stream_rec:
                        self.write({'stream_id': int(stream_rec['rid'])})
                return {"error":False,"description":description}


    def gen_QBben_data(self,partner_id):
        ben ={}
        ben['name'] = partner_id.name or ''
        ben['company_url'] = partner_id.website or ''
        ben['address__city'] = partner_id.city or ''
        ben['address__country'] = partner_id.country_id.name or ''
        ben['address__postal_code'] = partner_id.zip or ''
        ben['address__state_region'] = partner_id.state_id.name or ''
        ben['address__street_1'] = partner_id.street or ''
        ben['address__street_2'] = partner_id.street2 or ''
        ben['legacy_id'] = partner_id.qb_partner_legacy_id or ''
        return ben

    def gen_stream_data(self,streams, phase):
        stream ={}
        stream['phase'] = phase#Required
        stream['type'] = streams['type']#Required
        stream['donated'] = streams['donated']#Required
        stream['recycled'] = streams['recycled']#Required
        stream['resold'] = streams['resold']#Required
        stream['relocated'] = streams['relocated']#Required
        stream['landfilled'] = streams['landfilled']#Required
        stream['donation_fmv_'] = streams['donation_fmv_']#Required
        stream['source_reduced_co2e__tonnes_'] = streams['source_reduced_co2e__tonnes_']#Required
        stream['recycled_reduced_co2e__tonnes_'] = streams['recycled_reduced_co2e__tonnes_']#Required
        return stream
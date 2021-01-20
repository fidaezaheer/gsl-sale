from odoo import http
from odoo.http import request
import json
from datetime import datetime
import logging
import pyqb
import base64
import collections
import requests
import xmltodict

_logger = logging.getLogger(__name__)


def is_authenticated(params):
    config = http.request.env["ir.config_parameter"].sudo()
    qb_web_hook_token = config.search([("key", "=", "gsop.qb_web_hook_token")]).value
    if params["token"] == qb_web_hook_token:
        return True
    else:
        return False

def convertdate(datevalue):
    # oldformat = '01-20-2020'%'%m-%d-%Y'
    datetimeobject = datetime.strptime(datevalue,'%m-%d-%Y')
    newformat2 = datetimeobject.strftime('%Y-%m-%d')
    return newformat2

class WebhooksQb(http.Controller):
    @http.route("/odoo_phase_upsert", type="json", auth="public", cors="*", method="POST", website=True)
    def odoo_phase_upsert(self, **kwargs):
        values = dict(kwargs)
        _logger.info("\n" + str(values))
        # Config
        self.config = request.env['ir.config_parameter'].sudo()
        self.domain_url = self.config.search([('key', '=', 'quickbase_gs.quickbase_domainurl')]).value
        user_token = self.config.search([('key', '=', 'quickbase_gs.quickbase_usertoken')]).value
        main_token = self.config.search([('key', '=', 'quickbase_gs.quickbase_main_usertoken')]).value
        self.phase_table_id = self.config.search([('key', '=', 'quickbase_gs.quickbase_phases_tableid')]).value
        self.main_phase_table_id = self.config.search([('key', '=', 'quickbase_gs.quickbase_phase_tableid')]).value
        if self.main_phase_table_id == False:
            self.main_phase_table_id = 'bm9ieqsy3'
        if main_token == False:
            main_token = 'b5muyc_kj4t_d5u9qjvdsm754mqa7qbe7ryfg8'
        self._qbc = pyqb.Client(url=self.domain_url, user_token=user_token)
        
        try:
            # Search a project
            if kwargs.get("phase_number"):
                # Get Phase Informations
                qbc = pyqb.Client(url=self.domain_url, user_token=main_token)
                phase_main = qbc.doquery(query='{"Phase #".EX."%s"}' %kwargs.get("phase_number"), database=self.main_phase_table_id) 
            
            project = request.env["gs.project"].sudo().search([('number','=',kwargs["project_number"])],limit=1)
            if not project:
                project = request.env["gs.project"].sudo().create({
                    "name":kwargs["project_name"],
                    "number":kwargs["project_number"],
                })
            # Create a phase
            if project:
                phase =  request.env["gs.project.phase"].sudo().search([('number','=',kwargs["phase_number"])],limit=1)
                phase_qb = self._qbc.doquery(query='{"phase_number".EX."%s"}' %kwargs["phase_number"], database=self.phase_table_id)  #Phase report      
                account_name = ''
                if phase_qb['errtext'] == 'No error':
                    if 'record' in phase_qb:
                        account_name = phase_qb['record']['account']
                        if kwargs["qb_report_id"] == 'unknown' or kwargs["qb_report_id"] == '' :
                            qb_report_id = phase_qb['record']['record_id_']
                            kwargs["qb_report_id"] = qb_report_id
                
                if not phase:
                    # Convert dates
                    dt_quote=False
                    if kwargs["quote_date"] != '' or kwargs["quote_date"] != False:
                        dt_quote = convertdate(kwargs["quote_date"])
                    phase_data = {
                        "qb_id": kwargs["qb_id"],
                        "number":kwargs["phase_number"],
                        "name": kwargs["phase_name"],
                        "decom_start": convertdate(kwargs["decom_start"]) if kwargs["decom_start"] != '' else False,
                        "decom_end": convertdate(kwargs["decom_end"]) if kwargs["decom_end"] != '' else False,
                        "quote_date": dt_quote,
                        "qb_report_id": kwargs["qb_report_id"] if kwargs["qb_report_id"] != 'unknown' else False,
                        "project_id":project.id,
                        "qb_account_name": account_name
                    }
                    if "company_name" in kwargs:
                        phase_data['name'] = kwargs['company_name'] if phase_data['name'] == '' else phase_data['name']
                        partner = request.env["res.partner"].sudo().search([("name","=",kwargs["company_name"])],limit=1)
                        if not partner:
                            partner = request.env["res.partner"].sudo().create({
                                "name" : kwargs["company_name"],
                            })
                        if partner:
                            phase_data["phase_company_id"] = partner.id

                    if phase_main.get('errtext') == 'No error':
                        if isinstance(phase_main.get('record'), collections.OrderedDict):
                            users_query = ['project___pm_lead', 'pc', 'project___bdm', 'project___bdm_2']
                            kwargs_query = ['project_pm_lead','project_pc_lead','project_bdm','project_bdm_2']
                            field_names = ['project_pm_lead_id','pc_lead_id','project_bdm','project_bdm2']
                            
                            for i in range(0,len(users_query)):
                                user_id = False
                                email = phase_main.get('record',{}).get(users_query[i])
                                user_id = self.qb_get_userinfo(email,kwargs.get(kwargs_query[i],False)) if email else False
                                if user_id:
                                    user_id.partner_id.write({'email':email})
                                    phase_data[field_names[i]] = user_id.partner_id.id

                    phase =  request.env["gs.project.phase"].sudo().create(phase_data)
                    if phase:
                        return json.dumps({'error':False,'message':'Phase successfully created in Odoo'})
                    else:
                        return json.dumps({'error':True,'message':'Phase creation unsuccessful'})
                else:
                    return json.dumps({'error':False,'message':'Phase already exists on Odoo'})
        except Exception as e:
            return json.dumps({'error':True,'message':str(e.args)})

    def qb_get_userinfo(self, email, name):
        """Quickbase Get User Info from Main App"""
        
        ResUser = request.env['res.users'].sudo()
        if name == False:
            
            Config = request.env['ir.config_parameter'].sudo()
            quickbase_domain = Config.search([('key', '=', 'gsop.quickbase_domainurl')]).value
            if quickbase_domain == False:
                quickbase_domain = "https://greenstards.quickbase.com"
            qbc2 = pyqb.Client(url=quickbase_domain)
            qbc2.authenticate(username='fida@syncoria.com', password='Rpg5!g@&G8!c')
            URL = quickbase_domain + '/db/main?a=API_GetUserInfo&email='+ email + '&ticket=' + qbc2.__dict__.get('ticket')

            bdm_user = False
            response = requests.get(URL)
            if response.status_code == 200:
                res_dict = xmltodict.parse(response.text)
                if isinstance(res_dict, collections.OrderedDict):
                    if res_dict.get('qdbapi',{}).get('user',{}):
                        firstName = res_dict.get('qdbapi',{}).get('user',{}).get('firstName','') if res_dict.get('qdbapi',{}).get('user',{}).get('firstName','') != None else ''
                        name =  res_dict.get('qdbapi',{}).get('user',{}).get('firstName','') + ' ' + res_dict.get('qdbapi',{}).get('user',{}).get('lastName','')
        bdm_user = ResUser.search(['|',('email','=',email),('name','=',name)],limit=1)
        if bdm_user and bdm_user.name == bdm_user.email:
            bdm_user.write({'name':name,'email':email}) 
        if not bdm_user:
            bdm_user = request.env["res.users"].sudo().create({
                                'name': name,
                                'login': email,
                                'email': email,
                                'sel_groups_1_8_9': '9',
                                'notification_type': 'inbox',
                            })
        return bdm_user

    @http.route("/proposal_phase_upsert", type="json", auth="public", cors="*", method="POST", website=True)
    def proposal_phase_upsert(self, **kwargs):
        values = dict(kwargs)
        _logger.info(values)
        try:
            project = request.env["gs.project"].sudo().search([('number','=',kwargs["project_number"])],limit=1)
            if not project:
                project = request.env["gs.project"].sudo().create({
                    "name":kwargs["project_name"],
                    "number":kwargs["project_number"],
                })
            if project:
                phase =  request.env["gs.project.phase"].sudo().search([('name','=',kwargs["company_name"]+' (Proposal)')],limit=1)
                self.config = request.env['ir.config_parameter'].sudo()
                self.domain_url = self.config.search([('key', '=', 'quickbase_gs.quickbase_domainurl')]).value
                user_token = self.config.search([('key', '=', 'quickbase_gs.quickbase_usertoken')]).value
                self.phase_table_id = self.config.search([('key', '=', 'quickbase_gs.quickbase_phases_tableid')]).value
                # self._qbc = pyqb.Client(url=self.domain_url, user_token=user_token)
                if not phase:
                    phase_data = {
                        "name": kwargs["company_name"]+' (Proposal)',
                        "project_id": project.id,
                        "proposals_only":True,
                        # "qb_account_name": account_name
                    }
                    if "company_name" in kwargs:
                        partner = request.env["res.partner"].sudo().search([("name","=",kwargs["company_name"])],limit=1)
                        if not partner:
                            partner = request.env["res.partner"].sudo().create({
                                "name" : kwargs["company_name"],
                            })
                        if partner:
                            phase_data["phase_company_id"] = partner.id
                    if "project_pm_lead" in kwargs:
                        if kwargs["project_pm_lead"] != None and kwargs["project_pm_lead"] != "":
                            project_pm_lead_id = request.env["res.users"].sudo().search([("name","=",kwargs["project_pm_lead"])],limit=1)
                            if not project_pm_lead_id:
                                login=''
                                project_pm_lead_id = http.request.env["res.users"].sudo().create({
                                    'name': kwargs["project_pm_lead"],
                                    'login': login if login != '' else kwargs["project_pm_lead"],
                                    'sel_groups_1_8_9': '9',
                                    'notification_type': 'inbox',
                                })
                            if project_pm_lead_id:
                                phase_data["project_pm_lead_id"] = project_pm_lead_id.id
                    phase =  request.env["gs.project.phase"].sudo().create(phase_data)
                    if phase:
                        return json.dumps({'error':False,'message':'Phase successfully created in Odoo.'})
                    else:
                        return json.dumps({'error':True,'message':'Phase creation unsuccessful.'})
                else:
                    return json.dumps({'error':False,'message':'Phase already exists on Odoo.'})
        except Exception as e:
            return json.dumps({'error':True,'message':str(e.args)})

    @http.route("/phase_report_view", type="http", auth="public", cors="*", method="GET", website=True)
    def phase_report_view(self, **kwargs):
        phase = request.env['gs.project.phase'].sudo().search([('number','=',kwargs['phase_number'])])
        if phase:
            url = '/web#id='+str(phase.id)+'&model=gs.project.phase'
            return request.redirect(url)

    @http.route("/phase_record_id", type="json", auth="public", cors="*", method="POST", website=True)
    def phase_record_id(self, **kwargs):
        phase = request.env['gs.project.phase'].sudo().search([('number','=',kwargs['phase_number'])])
        if phase:
            url = '/web#id='+str(phase.id)+'&model=gs.project.phase'
            return json.dumps({'error':False,'url':url})
        else:
            return json.dumps({'error':True,'url':'url'})


    @http.route("/phase_publish_report", type="json", auth="public", cors="*", method="POST", website=True)
    def phase_publish_report(self, **kwargs):
        values = dict(kwargs)
        _logger.info(values)
        try:
            phase = request.env['gs.project.phase'].sudo().search([('id','=',int(kwargs['activeId']))])
            response = phase.action_publish_report(phase)
            return json.dumps(response)
        except Exception as e:
            return json.dumps({'error':True,'message':str(e.args)})

    @http.route("/get_phase_rec", type="json", auth="public", cors="*", method="POST", csrf=False)
    def get_phase_rec(self, **kwargs):
        values = dict(kwargs)
        _logger.info(values)
        try:
            phase = request.env['gs.project.phase'].sudo().search([('id','=',int(kwargs['activeId']))])
            return json.dumps({'error':False,'proposals_only':phase.proposals_only})
        except Exception as e:
            return json.dumps({'error':True,'message':str(e.args)})
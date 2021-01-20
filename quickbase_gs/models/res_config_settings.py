# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
# from ..quickbase.quickbase_sync import *
import logging
import pandas as pd
from ..quickbase.utils import *
from odoo.exceptions import UserError, ValidationError
import logging
import pyqb
_logger = logging.getLogger(__name__)


def round_to_nearest(x, base=5):
    return x - x % base


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    quickbase_usertoken = fields.Char('Quick Base User Token', help="xxxxxxxxxxxx")
    quickbase_domainurl = fields.Char('Quick Base Domain URL', help="xxxxxxxxxxxx")

    quickbase_accounts_tableid = fields.Char('Quick Base Account Table ID', help="xxxxxxxxxxxx")
    quickbase_phases_tableid = fields.Char('Quick Base Phases Table ID', help="xxxxxxxxxxxx")
    quickbase_beneficiaries_tableid = fields.Char('Quick Base Beneficiaries Table ID', help="xxxxxxxxxxxx")
    quickbase_posts_tableid = fields.Char('Quick Base Posts Table ID', help="xxxxxxxxxxxx")
    quickbase_partners_tableid = fields.Char('Quick Base Partners Table ID', help="xxxxxxxxxxxx")
    quickbase_phase_beneficiary_tableid = fields.Char('Quick Base Phase Beneficiary Table ID', help="xxxxxxxxxxxx")
    quickbase_phase_partner_tableid = fields.Char('Quick Base Phase Partners Table ID', help="xxxxxxxxxxxx")
    quickbase_streams_tableid = fields.Char('Quick Base Streams Table ID', help="xxxxxxxxxxxx")

    quickbase_account_query_fid = fields.Integer('Quick Base Account Query FID', help="xxxxxxxxxxxx")
    quickbase_account_query_rec_id = fields.Integer('Quick Base Account Query Record ID', help="xxxxxxxxxxxx")
    quickbase_account_avatar_fid = fields.Integer('Quick Base Account Avatar FID', help="xxxxxxxxxxxx")
    quickbase_phase_data_query_fid = fields.Integer('Quick Base Phase Data Query FID', help="xxxxxxxxxxxx")
    quickbase_beneficiaries_query_fid = fields.Integer('Quick Base Beneficiaries Query FID', help="xxxxxxxxxxxx")
    quickbase_beneficiaries_avatar_fid = fields.Integer('Quick Base Beneficiaries Avatar FID', help="xxxxxxxxxxxx")
    quickbase_posts_query_phases_fid = fields.Integer('Quick Base Posts Phases Query FID', help="xxxxxxxxxxxx")
    quickbase_posts_picture_fid = fields.Integer('Quick Base Posts Picture FID', help="xxxxxxxxxxxx")
    quickbase_partners_query_fid = fields.Integer('Quick Base Partners Query FID', help="xxxxxxxxxxxx")
    quickbase_partners_logo_fid = fields.Integer('Quick Base Partners Logo FID', help="xxxxxxxxxxxx")
    quickbase_phase_beneficiary_query_fid = fields.Integer('Quick Base Phase Beneficiary Query FID', help="xxxxxxxxxxxx")
    quickbase_phase_partner_query_fid = fields.Integer('Quick Base Phase Partners Query FID', help="xxxxxxxxxxxx")
    quickbase_streams_query_fid = fields.Integer('Quick Base Streams Query FID', help="xxxxxxxxxxxx")
    gsop_total_donation = fields.Integer('Gsop Total Donation Value', help="xxxxxxxxxxxx")
    gsop_total_tons = fields.Integer('Gsop Total Tons', help="xxxxxxxxxxxx")
    qb_web_hook_token = fields.Char('Quick Base Webhook Token', help="xxxxxxxxxxxx")
    quickbase_cache = fields.Boolean('Quickbase Cache')
    google_maps_api_key = fields.Char('Google Maps API Key', help="xxxxxxxxxxxx")
    #Main App
    quickbase_user_name = fields.Char('Quick Base User Email', help="quickbase@gmail.com")
    quickbase_user_password = fields.Char('Quick Base User Password', help="********")
    quickbase_users_tableid = fields.Char('Quick Base Users Table ID', help="xxxxxxxxxxxx")
    quickbase_main_usertoken = fields.Char('Quick Base Main User Token', help="xxxxxxxxxxxx")
    quickbase_contacts_tableid = fields.Char('Quick Base Contacts Table ID', help="xxxxxxxxxxxx")
    quickbase_companies_tableid = fields.Char('Quick Base Companies Table ID', help="xxxxxxxxxxxx")
    quickbase_phase_tableid = fields.Char('Quick Base Main Phase Table ID', help="xxxxxxxxxxxx")



    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update(
            quickbase_usertoken=ICPSudo.get_param('quickbase_gs.quickbase_usertoken'),
            quickbase_domainurl=ICPSudo.get_param('quickbase_gs.quickbase_domainurl'),
            quickbase_accounts_tableid=ICPSudo.get_param('quickbase_gs.quickbase_accounts_tableid'),
            quickbase_phases_tableid=ICPSudo.get_param('quickbase_gs.quickbase_phases_tableid'),
            quickbase_beneficiaries_tableid=ICPSudo.get_param('quickbase_gs.quickbase_beneficiaries_tableid'),
            quickbase_posts_tableid=ICPSudo.get_param('quickbase_gs.quickbase_posts_tableid'),
            quickbase_partners_tableid=ICPSudo.get_param('quickbase_gs.quickbase_partners_tableid'),
            quickbase_phase_beneficiary_tableid=ICPSudo.get_param('quickbase_gs.quickbase_phase_beneficiary_tableid'),
            quickbase_phase_partner_tableid=ICPSudo.get_param('quickbase_gs.quickbase_phase_partner_tableid'),
            quickbase_streams_tableid=ICPSudo.get_param('quickbase_gs.quickbase_streams_tableid'),
            quickbase_account_query_fid=int(ICPSudo.get_param('quickbase_gs.quickbase_account_query_fid')),
            quickbase_account_query_rec_id=int(ICPSudo.get_param('quickbase_gs.quickbase_account_query_rec_id')),
            quickbase_account_avatar_fid=int(ICPSudo.get_param('quickbase_gs.quickbase_account_avatar_fid')),
            quickbase_phase_data_query_fid=int(ICPSudo.get_param('quickbase_gs.quickbase_phase_data_query_fid')),
            quickbase_beneficiaries_query_fid=int(ICPSudo.get_param('quickbase_gs.quickbase_beneficiaries_query_fid')),
            quickbase_beneficiaries_avatar_fid=int(ICPSudo.get_param('quickbase_gs.quickbase_beneficiaries_avatar_fid')),
            quickbase_posts_query_phases_fid=int(ICPSudo.get_param('quickbase_gs.quickbase_posts_query_phases_fid')),
            quickbase_posts_picture_fid=int(ICPSudo.get_param('quickbase_gs.quickbase_posts_picture_fid')),
            quickbase_partners_query_fid=int(ICPSudo.get_param('quickbase_gs.quickbase_partners_query_fid')),
            quickbase_partners_logo_fid=int(ICPSudo.get_param('quickbase_gs.quickbase_partners_logo_fid')),
            quickbase_phase_beneficiary_query_fid=int(ICPSudo.get_param('quickbase_gs.quickbase_phase_beneficiary_query_fid')),
            quickbase_phase_partner_query_fid=int(ICPSudo.get_param('quickbase_gs.quickbase_phase_partner_query_fid')),
            quickbase_streams_query_fid=int(ICPSudo.get_param('quickbase_gs.quickbase_streams_query_fid')),
            qb_web_hook_token=ICPSudo.get_param('quickbase_gs.qb_web_hook_token'),
            quickbase_cache=ICPSudo.get_param('quickbase_gs.quickbase_cache'),
            google_maps_api_key=ICPSudo.get_param('quickbase_gs.google_maps_api_key'),
            quickbase_user_name=ICPSudo.get_param('quickbase_gs.quickbase_user_name'),
            quickbase_user_password=ICPSudo.get_param('quickbase_gs.quickbase_user_password'),
            quickbase_main_usertoken=ICPSudo.get_param('gsop.quickbase_main_usertoken'),
            quickbase_users_tableid=ICPSudo.get_param('gsop.quickbase_users_tableid'),    
            quickbase_contacts_tableid=ICPSudo.get_param('gsop.quickbase_contacts_tableid'),
            quickbase_companies_tableid=ICPSudo.get_param('gsop.quickbase_companies_tableid'),
            quickbase_phase_tableid=ICPSudo.get_param('gsop.quickbase_phase_tableid'),
        )
        return res

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('quickbase_gs.quickbase_usertoken', self.quickbase_usertoken)
        ICPSudo.set_param('quickbase_gs.quickbase_domainurl', self.quickbase_domainurl)
        ICPSudo.set_param('quickbase_gs.quickbase_accounts_tableid', self.quickbase_accounts_tableid)
        ICPSudo.set_param('quickbase_gs.quickbase_phases_tableid', self.quickbase_phases_tableid)
        ICPSudo.set_param('quickbase_gs.quickbase_beneficiaries_tableid', self.quickbase_beneficiaries_tableid)
        ICPSudo.set_param('quickbase_gs.quickbase_posts_tableid', self.quickbase_posts_tableid)
        ICPSudo.set_param('quickbase_gs.quickbase_partners_tableid', self.quickbase_partners_tableid)
        ICPSudo.set_param('quickbase_gs.quickbase_phase_beneficiary_tableid', self.quickbase_phase_beneficiary_tableid)
        ICPSudo.set_param('quickbase_gs.quickbase_phase_partner_tableid', self.quickbase_phase_partner_tableid)
        ICPSudo.set_param('quickbase_gs.quickbase_streams_tableid', self.quickbase_streams_tableid)
        ICPSudo.set_param('quickbase_gs.quickbase_account_query_fid', self.quickbase_account_query_fid)
        ICPSudo.set_param('quickbase_gs.quickbase_account_query_rec_id', self.quickbase_account_query_rec_id)
        ICPSudo.set_param('quickbase_gs.quickbase_account_avatar_fid', self.quickbase_account_avatar_fid)
        ICPSudo.set_param('quickbase_gs.quickbase_phase_data_query_fid', self.quickbase_phase_data_query_fid)
        ICPSudo.set_param('quickbase_gs.quickbase_beneficiaries_query_fid', self.quickbase_beneficiaries_query_fid)
        ICPSudo.set_param('quickbase_gs.quickbase_beneficiaries_avatar_fid', self.quickbase_beneficiaries_avatar_fid)
        ICPSudo.set_param('quickbase_gs.quickbase_posts_query_phases_fid', self.quickbase_posts_query_phases_fid)
        ICPSudo.set_param('quickbase_gs.quickbase_posts_picture_fid', self.quickbase_posts_picture_fid)
        ICPSudo.set_param('quickbase_gs.quickbase_partners_query_fid', self.quickbase_partners_query_fid)
        ICPSudo.set_param('quickbase_gs.quickbase_partners_logo_fid', self.quickbase_partners_logo_fid)
        ICPSudo.set_param('quickbase_gs.quickbase_phase_beneficiary_query_fid', self.quickbase_phase_beneficiary_query_fid)
        ICPSudo.set_param('quickbase_gs.quickbase_phase_partner_query_fid', self.quickbase_phase_partner_query_fid)
        ICPSudo.set_param('quickbase_gs.quickbase_streams_query_fid', self.quickbase_streams_query_fid)
        ICPSudo.set_param('quickbase_gs.qb_web_hook_token', self.qb_web_hook_token)
        ICPSudo.set_param('quickbase_gs.quickbase_cache', self.quickbase_cache)
        ICPSudo.set_param('quickbase_gs.google_maps_api_key', self.google_maps_api_key)
        ICPSudo.set_param('quickbase_gs.quickbase_user_name', self.quickbase_user_name)
        ICPSudo.set_param('quickbase_gs.quickbase_user_password', self.quickbase_user_password)
        ICPSudo.set_param('gsop.quickbase_users_tableid', self.quickbase_users_tableid)
        ICPSudo.set_param('gsop.quickbase_contacts_tableid', self.quickbase_contacts_tableid)
        ICPSudo.set_param('gsop.quickbase_main_usertoken', self.quickbase_main_usertoken)
        ICPSudo.set_param('gsop.quickbase_companies_tableid', self.quickbase_companies_tableid)
        ICPSudo.set_param('gsop.quickbase_phase_tableid', self.quickbase_phase_tableid)

    def sync_beneficiaries_data(self):
        self.Partner = self.env['res.partner'].sudo()
        self.Users = self.env['res.users'].sudo()
        self.Groups = self.env['res.groups'].sudo()
        # self.PhaseReport = self.env['quickbase_gs.phase_reports'].sudo()
        # self.Streams = self.env['quickbase_gs.streams'].sudo()
        # self.Post = self.env['quickbase_gs.posts'].sudo()
        self.Country = self.env['res.country'].sudo()
        self.Country_State = self.env['res.country.state'].sudo()
        self.Config = self.env['ir.config_parameter'].sudo()
        self.domain_url = self.Config.search([('key', '=', 'quickbase_gs.quickbase_domainurl')]).value
        self.user_token = self.Config.search([('key', '=', 'quickbase_gs.quickbase_usertoken')]).value

        beneficiary_table_id = self.Config.search([('key', '=', 'quickbase_gs.quickbase_beneficiaries_tableid')]).value
        beneficiary_url = self.domain_url + "/db/" + beneficiary_table_id + "?a=API_GenResultsTable&clist=a&options=csv&usertoken=" + self.user_token
        #-----------------------------------------------------------
        try:
            beneficiary_csv =  pd.read_csv(beneficiary_url)
        except Exception as e:
            beneficiary_csv = pd.read_csv(beneficiary_url, encoding = 'iso-8859-1') 
        #--------------------------------------------------------------
        beneficiary_dic = {}
        avatar_fid = int(self.Config.search([('key', '=', 'gsop.quickbase_beneficiaries_avatar_fid')]).value)
        _logger.info('Starting Beneficiary Sync')
        for index, row in beneficiary_csv.iterrows():
            _logger.info('Start beneficiary with QB id = ' + str(row['Record ID#']))
            img_url = 'https://staging-greenstandards.odoo.com/base/static/img/company_image.png'

            beneficiary_record = self.Partner.search([('qb_beneficiary_id', '=', row['Record ID#'])], limit=1)

            if not pd.isna(row['Logo']) and avatar_fid:
                img_url = "%s/up/%s/a/r%s/e%d/v0/%s" % (
                    self.domain_url, beneficiary_table_id, row['Record ID#'], avatar_fid, row['Logo'])

            country_id = None
            state_id = None
            if not pd.isna(row['Address: Country']):
                country_id = get_country_id(self, row['Address: Country'])
            if not pd.isna(row['Address: State/Region']) and country_id:
                state_id = get_state_id(self, country_id, row['Address: State/Region'])

            from datetime import datetime
            if 'Date Created' in row:
                try:
                    row['Date Created'] = datetime.strptime(row['Date Created'],"%m-%d-%Y")
                    row['Date Created'] = row['Date Created'].strftime('%Y-%m-%d')
                except Exception as e:
                    row['Date Created'] = datetime.strptime(row['Date Created'],"%Y-%m-%d")

            beneficiary_model = {
                'qb_beneficiary_id': row['Record ID#'],
                'name': row['Name'],
                'qb_beneficiary_legacy_id': row['Legacy ID'] if not pd.isna(row['Legacy ID']) else None,
                'qb_image_url': img_url,
                'street': row['Address: Street 1'] if not pd.isna(row['Address: Street 1']) else None,
                'street2': row['Address: Street 2'] if not pd.isna(row['Address: Street 2']) else None,
                'zip': row['Address: Postal Code'] if not pd.isna(row['Address: Postal Code']) else None,
                'city': row['Address: City'] if not pd.isna(row['Address: City']) else None,
                'state_id': state_id,
                'country_id': country_id,
                'qb_created_date': row['Date Created'],
                'is_company': True
            }

            # Check if the record exsits or not and the address are the same or not to call google api to get lat and lng for thr address
            if not beneficiary_record.id and not pd.isna(row['Address']) and row[
                'Address'] != beneficiary_record.contact_address:
                lat, lng, google_address = get_google_address_gs(self, row['Address'])
                beneficiary_model['qb_lat'] = lat
                beneficiary_model['qb_lng'] = lng
                beneficiary_model['qb_google_address'] = google_address

            if not beneficiary_record.id:
                beneficiary_record = self.Partner.search([('name', '=', row['Name'])], limit=1)
                if beneficiary_record.id:
                    beneficiary_record.write(beneficiary_model)
                    _logger.info('Update beneficiary with name ' + row['Name'] + ' and QB id = ' + str(row['Record ID#']))
                else:
                    beneficiary_record = self.Partner.create(beneficiary_model)
                    _logger.info('Create new beneficiary with QB id = ' + str(row['Record ID#']))
            else:
                beneficiary_record.write(beneficiary_model)
                _logger.info('Update beneficiary with QB id = ' + str(row['Record ID#']))

            beneficiary_dic[row['Record ID#']] = beneficiary_record.id
        _logger.info('Completed Beneficiary Sync')
        return beneficiary_dic


    @api.model
    def set_quickbase_parameters(self):
        _logger.info("\n set_quickbase_parameters")
        settings = self.env['res.config.settings'].create({
            "quickbase_usertoken": "b4h753_kj4t_hdfhhycmtbqpcjxe3mqy95ktj",
            "quickbase_domainurl": "https://greenstards.quickbase.com",
            "quickbase_accounts_tableid": "bpignhuhm",
            "quickbase_phases_tableid": "bpign7p8q",
            "quickbase_beneficiaries_tableid": "bpigpyw2t",
            "quickbase_posts_tableid": "bpigp7jg3",
            "quickbase_partners_tableid": "bpigqdmkp",
            "quickbase_phase_beneficiary_tableid": "bpj9isccv",
            "quickbase_phase_partner_tableid": "bpj9izmc3",
            "quickbase_streams_tableid": "bpsfkhtt9",
            "qb_web_hook_token": "b4h753_kj4t_b85sjzccgubenjdjf4fmac9mz2yp",
            "quickbase_account_query_fid": "9",
            "quickbase_account_query_rec_id": "3",
            "quickbase_beneficiaries_avatar_fid": "3",
            "quickbase_phase_data_query_fid": "66",
            "quickbase_phase_beneficiary_query_fid": "3",
            "quickbase_account_avatar_fid": "7",
            "quickbase_posts_query_phases_fid": "11",
            "quickbase_posts_picture_fid": "10",
            "quickbase_partners_query_fid": "3",
            "quickbase_partners_logo_fid": "15",
            "quickbase_phase_beneficiary_query_fid": "8",
            "quickbase_phase_partner_query_fid": "8",
            "quickbase_streams_query_fid": "8",
            # "google_maps_api_key": "AIzaSyA0BDPMVFcHQ2cb6hIi5BriQpr8Szr1xPE",
            # "quickbase_user_name": "",
            # "quickbase_user_password": "",
            "quickbase_users_tableid": "bm78yxvsa",
            "quickbase_contacts_tableid": "bm78yxvtr",
            "quickbase_main_usertoken": "b5muyc_kj4t_d5u9qjvdsm754mqa7qbe7ryfg8",
            "quickbase_companies_tableid": "bm78yxvsz",
            "quickbase_phase_tableid": "bm9ieqsy3",
        })
        settings.execute()


# -*- coding: utf-8 -*-
import requests
import logging

from PIL import Image
from resizeimage import resizeimage
from io import BytesIO
import base64

_logger = logging.getLogger(__name__)

country_dic = {}
state_dic = {}
SHORT_TON_TO_METRIC = 0.90718474


def slugify(account_name):
    return account_name.replace(' ', '_')


def un_slugify(slug):
    return slug.replace('_', ' ')


def escape_html(text):
    return text.replace('&', "&amp;").replace('<', "&lt;").replace('>', "&gt;").replace('"', '&quot;').replace("'",
                                                                                                               "&#039;")


def unescape_html(text):
    return text.replace("&amp;", '&').replace("&lt;", '<').replace("&gt;", '>').replace('&quot;', '"').replace("&#039;",
                                                                                                               "'")


def get_image_content(url):
    if requests.get(url).status_code == 200:
        return requests.get(url).content
    else:
        return None


def get_google_address(self, quickbase_address):
    _logger.info('Start load address for QB address ' + str(quickbase_address))
    lat, lng, formatted_address = None, None, None
    if quickbase_address:
        google_map_url = 'https://maps.googleapis.com/maps/api/geocode/json?&address='
        google_map_key = self.Config.search([('key', '=', 'gsop.google_maps_api_key')]).value
        _logger.info('Start load address with url ' + google_map_url + quickbase_address + '&key=' + google_map_key)
        google_response = requests.get(google_map_url + quickbase_address + '&key=' + google_map_key)
        json_response = google_response.json()
        if json_response.get('results') and json_response.get('results')[0]:
            result = json_response.get('results')[0]
            lat = result.get('geometry').get('location').get('lat')
            lng = result.get('geometry').get('location').get('lng')
            formatted_address = result.get('formatted_address')
    return lat, lng, formatted_address

def get_google_address_gs(self, quickbase_address):
    _logger.info('Start load address for QB address ' + str(quickbase_address))
    
    lat, lng, formatted_address = None, None, None
    if quickbase_address:
        google_map_url = 'https://maps.googleapis.com/maps/api/geocode/json?&address='
        google_map_key = self.Config.search([('key', '=', 'quickbase_gs.google_maps_api_key')]).value
        _logger.info('Start load address with url ' + google_map_url + quickbase_address + '&key=' + google_map_key)
        google_response = requests.get(google_map_url + quickbase_address + '&key=' + google_map_key)
        json_response = google_response.json()
        if json_response.get('results') and json_response.get('results')[0]:
            result = json_response.get('results')[0]
            lat = result.get('geometry').get('location').get('lat')
            lng = result.get('geometry').get('location').get('lng')
            formatted_address = result.get('formatted_address')
    return lat, lng, formatted_address

def calculate_phase_streams(phase_record):
    resold, donated, recycled, relocated, landfilled, donation_fmv, source_reduced_co2e, recycled_reduced_co2e = 0, 0, 0, 0, 0, 0, 0, 0
    for stream in phase_record.streams_ids:
        resold = resold + stream.resold
        donated = donated + stream.donated
        recycled = recycled + stream.recycled
        relocated = relocated + stream.relocated
        landfilled = landfilled + stream.landfilled
        donation_fmv = donation_fmv + stream.donation_fmv
        source_reduced_co2e = source_reduced_co2e + stream.source_reduced_co2e
        recycled_reduced_co2e = recycled_reduced_co2e + stream.recycled_reduced_co2e
    phase_record.resold = resold
    phase_record.donated = donated
    phase_record.recycled = recycled
    phase_record.relocated = relocated
    phase_record.landfilled = landfilled
    phase_record.donation_fmv = donation_fmv
    phase_record.source_reduced_co2e = source_reduced_co2e
    phase_record.recycled_reduced_co2e = recycled_reduced_co2e


def get_state_id(self, country_id, state_name):
    if not bool(state_dic):
        states = self.Country_State.search([])
        for state in states:
            state_dic[str(state.country_id.id) + state.name] = state.id

    return state_dic.get(str(country_id) + state_name) if country_id and state_name else None


def get_country_id(self, country_name):
    if not bool(country_dic):
        countries = self.Country.search([])
        for country in countries:
            country_dic[country.name] = country.id

    return country_dic.get(country_name)


def convert_to_tonnes(phases):
    for phase in phases:
        resold, donated, recycled, relocated, landfilled, donation_fmv, source_reduced_co2e, recycled_reduced_co2e = 0, 0, 0, 0, 0, 0, 0, 0
        for stream in phase.streams:
            stream.resold = stream.resold * SHORT_TON_TO_METRIC
            resold = resold + stream.resold

            stream.donated = stream.donated * SHORT_TON_TO_METRIC
            donated = donated + stream.donated

            stream.recycled = stream.recycled * SHORT_TON_TO_METRIC
            recycled = recycled + stream.recycled

            stream.relocated = stream.relocated * SHORT_TON_TO_METRIC
            relocated = relocated + (stream.relocated * SHORT_TON_TO_METRIC)

            stream.landfilled = stream.landfilled * SHORT_TON_TO_METRIC
            landfilled = landfilled + stream.landfilled
            donation_fmv = donation_fmv + stream.donation_fmv
            source_reduced_co2e = source_reduced_co2e + stream.source_reduced_co2e
            recycled_reduced_co2e = recycled_reduced_co2e + stream.recycled_reduced_co2e
        phase.resold = resold
        phase.donated = donated
        phase.recycled = recycled
        phase.relocated = relocated
        phase.landfilled = landfilled
        phase.donation_fmv = donation_fmv
        phase.source_reduced_co2e = source_reduced_co2e
        phase.recycled_reduced_co2e = recycled_reduced_co2e
        phase.diverted_from_landfill = phase.donated + phase.recycled + phase.resold + phase.relocated
        phase.handled = phase.diverted_from_landfill + phase.landfilled


def set_show_materials_report(account):
        for phase in account.phases:
            for stream in phase.streams:
                if stream.stream_type != 'Furniture Assets':
                    account.show_materials_report = True
                    return


def set_report_streams(account):
        account.has_report_only_streams = False
        account.has_non_report_only_streams = False
        for phase in account.phases:
            phase.report_only_streams = [stream for stream in phase.streams if stream.report_only]
            if phase.report_only_streams:
                account.has_report_only_streams = True
            phase.non_report_only_streams = [stream for stream in phase.streams if not stream.report_only]
            if phase.non_report_only_streams:
                account.has_non_report_only_streams = True


def generate_beneficiary_thumbnail(img_url):
    encoded_file, encoded_thumbnail_file = None, None
    picture = get_image_content(img_url)
    if picture:
        encoded_file = base64.b64encode(picture)
        try:
            img = Image.open(BytesIO(picture))
            thumbnail_img = resizeimage.resize_contain(img, [110, 110])
            output = BytesIO()
            thumbnail_img.save(output, format='png')
            im_data = output.getvalue()
            encoded_thumbnail_file = base64.b64encode(im_data)
            #img.close()
        except Exception as e:
            _logger.error(e)
            encoded_thumbnail_file = base64.b64encode(picture)
    return encoded_file, encoded_thumbnail_file


def generate_post_thumbnail(img_url):
    encoded_file, encoded_thumbnail_file = None, None
    picture = get_image_content(img_url)
    if picture:
        encoded_file = base64.b64encode(picture)
        try:
            img = Image.open(BytesIO(picture))
            thumbnail_img = resizeimage.resize_cover(img, [492, 314])
            output = BytesIO()
            thumbnail_img.save(output, format='png')
            im_data = output.getvalue()
            encoded_thumbnail_file = base64.b64encode(im_data)
            #img.Close()
        except Exception as e:
            _logger.error(e)
            encoded_thumbnail_file = base64.b64encode(picture)
    return encoded_file, encoded_thumbnail_file
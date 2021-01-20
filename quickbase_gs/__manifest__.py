# -*- coding: utf-8 -*-
{
    'name': "GSOP Quickbase Connector",
    'summary': """Odoo Quickbase Connector for GSOP""",
    'description': """Odoo Quickbase Connector for GSOP""",
    'author': "Syncoria Inc.",
    'website': "https://www.syncoria.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','product_gs'],
    'external_dependencies': {'python': ['pandas','requests','xmltodict','six','pyqb']},
    'data': [
        # 'security/ir.model.access.csv',
        'data/quickbase_setting.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_view.xml',
        'data/ir_cron_data.xml',
        'views/phase_view.xml',
    ],
    'qweb': [
        # 'static/src/xml/inventory_report.xml',
    ],
 
}

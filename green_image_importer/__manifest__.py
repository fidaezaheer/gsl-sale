# -*- coding: utf-8 -*-
{
    'name': "green Image Import",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','product_gs'],

    # always loaded
    'data': [
        #"security/green_import_product_img_security.xml",
        "security/ir.model.access.csv",
        "wizard/product_tmpl_multi_action.xml",
        "wizard/green_message_wizard.xml",
        "views/import_images.xml",
        "views/image.xml"
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

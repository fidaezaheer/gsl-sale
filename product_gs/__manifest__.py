{
    'name': 'Product Customizations',
    'summary': '',
    'version': '1.0',

    'description': """
    """,

    'author': 'TM_FULLNAME',
    'maintainer': 'TM_FULLNAME',
    'contributors': ['TM_FULLNAME <TM_FULLNAME@gmail.com>'],

    'website': 'http://www.gitlab.com/TM_FULLNAME',

    'license': 'AGPL-3',
    'category': 'Uncategorized',

    'depends': [
        'stock',
        'website_sale',
        'website_form',
        'website_sale_delivery',
    ],
    'external_dependencies': {
        'python': [
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'wizards/product_image.xml',
        'views/mailout.xml',
        'views/stock.xml',
        'views/project.xml',
        'views/product.xml',
        'views/typicals_view.xml',
        'views/phase.xml',
        'data/data.xml',
        'views/website.xml',
        'views/sale.xml',
        'reports/gsop_reports.xml',
        'reports/pdp_report.xml',
        'reports/los_report.xml',
        'reports/summary_report.xml',
        'reports/placement_report.xml',
        'views/disposition_type.xml',
        'data/factor.table.csv',
        'wizards/tot_wizard.xml',
        'data/mail_data.xml',
        # 'data/cron.xml'
    ],
    'demo': [
    ],
    'js': [
    ],
    'css': [
    ],
    'qweb': [
        'static/src/xml/los_report_button.xml',
        'static/src/xml/publish_report_button.xml'
    ],
    'images': [
    ],
    'test': [
    ],

    'installable': True
}

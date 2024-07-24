# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN Traffic Contract',
    'category': 'REACH SUCDEN',
    'version' : '16.0.1.0',
    'author': 'Thai Sucden',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'sd_pur_sales', 'sd_inventory', 'sd_mrp'],
    'description': """
    Module Traffic Contract VN
    """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/traffic_contract_view.xml',
        'views/p_contract_view.xml',
        'views/s_p_allocation_view.xml',
        'views/traffic_contract_filter_view.xml',
        'views/sucden_origin_view.xml',
        'views/certificate_license_traffic_view.xml',
        'views/unallocated_pcontract_view.xml',
        'views/instore_traffic_view.xml',
        'views/bonded_movement_view.xml',
        'views/gdn_bonded_view.xml',
        'views/shipping_split_view.xml',
        'views/s_import_file_view.xml',
        'views/sale_contract_view.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            ''
            'sd_traffic/static/css/view.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}

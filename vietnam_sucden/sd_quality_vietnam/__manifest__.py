# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN VIETNAM QUALITY',
    'category': 'SUCDEN VIETNAM QUALITY',
    'version' : '16.0.1.0',
    'author': 'SUCDEN VIETNAM',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'sd_quality', 'sd_security_gate', 'sd_master_vietnam'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/stock_contract_allocation_view.xml',
        'views/pss_management_view.xml',
        'views/kcs_sample_view.xml',
        'views/lot_kcs.xml',
        'views/lot_allocation.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sd_quality_vietnam/static/src/css/lot_kcs_badge.css',
            'sd_quality_vietnam/static/src/js/lot_kcs_badge.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}

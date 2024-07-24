# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN ACCOUNT CONTRACT',
    'category': 'REACH contract',
    'version' : '16.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://www.reach.com.vn',
    'depends': ['account','sd_master','sd_mrp','sd_inventory'],
    'description': """
    """,
    'data': [
        
        'security/ir.model.access.csv',
        
        'views/res_partner.xml',
        'views/account_payment.xml',
        'views/account_period_view.xml',
        'views/mrp_production_costing_view.xml',
        'views/account_journal_view.xml',
        'views/account_move.xml',
        'views/menu.xml',
        'views/res_currency_view.xml',
        'report/report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

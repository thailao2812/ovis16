# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN SALES PURCHASE',
    'category': 'REACH SALES PURCHASE',
    'version' : '15.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://www.reach.com.vn',
    'depends': ['base','sd_master','sd_purchase_contract','sd_sale_contract'],
    'description': """
    """,
    'data': [
        
        #'data/example_users_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        
        'views/ned_certificate_license_views.xml',
        'views/sd_sale_contract.xml',
        'views/shipping_intruction.xml',
        'views/daily_confirmation.xml',
        'views/sd_purchase_contract.xml',
        'views/menu.xml',
        
        'report/report_view.xml',
        'data/ir_cron.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

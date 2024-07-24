# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN MRP QUALITY',
    'category': 'REACH MRP QUALITY',
    'version' : '15.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://www.reach.com.vn',
    'depends': ['sd_master','mrp','sd_mrp','sd_quality','sd_inventory','sd_traffic'],
    'description': """
    """,
    'data': [
        
        'views/production.xml',
        'views/menu.xml',
        'views/stock_lot.xml',
        'views/mrp_operation_result.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

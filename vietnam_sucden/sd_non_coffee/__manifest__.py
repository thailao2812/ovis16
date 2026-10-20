# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN Non-Coffee Processes',
    'category': 'Sucden Non-Coffee',
    'version' : '15.0.1.0',
    'author': 'Sucden Coffee Vietnam',
    'website': 'https://sucdencoffee.vn',
    'depends': ['account','base','product','purchase','delivery'],
    'description': """
        SUCDEN Non-Coffee Processes
    """,
    'data': [
        'security/ir.model.access.csv',     
        'views/pricelist_views.xml'
        #'data/example_users_data.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

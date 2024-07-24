# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN VIETNAM MASTER DATA',
    'category': 'REACH MASTER DATA',
    'version' : '15.0.1.0',
    'author': 'SCUDEN VIETNAM',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'sd_master', 'contacts_area'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'security/group.xml',
        'views/res_partner_area_view.xml',
        'views/import_polygon_view.xml',
        'views/import_deforestation_view.xml',
        'views/farmer_view.xml',
        'views/res_user_view.xml',
        'views/product_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'sd_master_vietnam/static/src/js/*',
        ]
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}

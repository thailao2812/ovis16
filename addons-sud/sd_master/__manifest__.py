# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN MASTER DATA',
    'category': 'REACH MASTER DATA',
    'version' : '15.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://www.reach.com.vn',
    'depends': ['base','product','account','stock','uom'],
    'description': """
    """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        
        #'data/example_users_data.xml',
        
        'views/master_data.xml',
        'views/res_district.xml',
        'views/res_partner.xml',
        'views/product_category.xml',
        'views/res_users_view.xml',
        'views/product_product.xml',
        'views/res_currency.xml',
        'views/mapping_data.xml',
        #'views/ned_certificate_license_views.xml',
        'views/res_company.xml',
        'views/menu.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN LICENSE CERTIFICATE',
    'category': 'SUCDEN LICENSE CERTIFICATE',
    'version' : '16.0.1.0',
    'author': 'SCUDEN VIETNAM',
    'website': 'https://www.sucden.com',
    'depends': ['base','sd_pur_sales', 'sd_purchase_contract', 'sd_sale_contract', 'sd_contract_vietnam'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'data/group.xml',
        'views/ned_certificate_view.xml',
        'views/ned_certificate_license_view.xml',
        'views/sd_certificate_license_detail.xml',
        'views/purchase_contract_view.xml',
        'views/s_contract_view.xml',
        'views/shipping_instruction_view.xml',
        'views/sale_contract_view.xml',
        'views/delivery_order_view.xml',
        'views/lot_stack_allocation_license.xml',
        'views/menu.xml',
    ],
    'assets': {
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}

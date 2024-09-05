# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN CONTRACT VIETNAM',
    'category': 'SUCDEN CONTRACT VIETNAM',
    'version' : '16.0.1.0',
    'author': 'SCUDEN VIETNAM',
    'website': 'https://www.sucden.com',
    'depends': ['base','sd_pur_sales', 'sd_master_vietnam'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'data/group.xml',
        'views/purchase_contract_view.xml',
        'views/shipping_instruction_view.xml',
        'views/certificate_license_view.xml',
        'views/sd_certificate_license_detail.xml',
        'views/diff_configuration_view.xml',
        'views/stock_allocation_view.xml',
        'views/average_price_contract_view.xml',
        'views/sale_contract_view.xml',
        'views/menu.xml',
        'wizard/import_farmer_view.xml',
        'wizard/wizard_report_average_price.xml',
        'wizard/wizard_purchase_contract.xml',
        'report/report_view.xml'
    ],
    'assets': {
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}

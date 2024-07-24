# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN INDIA MASTER DATA',
    'category': 'Sucden India',
    'version' : '16.0.1.0',
    'author': 'Sucden Viet Nam',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'sd_master'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'security/data.xml',
        'views/res_partner_view.xml',
        'views/res_partner_bank_view.xml',
        'views/condition_contract_view.xml',
        'views/financial_year_view.xml',
        'views/res_district_view.xml',
        'views/ned_certificate_view.xml',
        'views/interest_configuration_view.xml',
        'views/analysis_batch_report_view.xml',
        'data/data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

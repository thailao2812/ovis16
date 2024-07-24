# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN VIETNAM SECURITY GATE',
    'category': 'SUCDEN VIETNAM SECURITY GATE',
    'version' : '16.0.1.0',
    'author': 'SUCDEN VIETNAM',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'sd_contract_vietnam', 'sd_security_gate'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_contract_view.xml',
        'views/request_payment_view.xml',
        'views/delivery_registration_contract.xml',
        'views/data.xml',
        'report/report_view.xml',
        'wizard/wizard_reason_refuse_view.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'sd_security_gate_vietnam/static/src/css/customize.css',
    #     ],
    # },
    'installable': True,
    'auto_install': False,
    'application': False,
}

# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN INDIA SECURITY GATE',
    'category': 'Sucden India',
    'version' : '16.0.1.0',
    'author': 'Sucden Viet Nam',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'sd_india_quality_control', 'sd_india_inventory'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'security/data.xml',
        'wizard/wizard_reject_security_view.xml',
        'views/security_gate_view.xml',
        'views/quality_control_view.xml',
        'views/request_kcs_line_view.xml',
        'views/stock_picking_view.xml',
        'report/report.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN INDIA QUALITY CONTROL',
    'category': 'Sucden India',
    'version' : '16.0.1.0',
    'author': 'Sucden Viet Nam',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'sd_security_gate', 'sd_india_inventory', 'sd_india_master'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_reject_qc_view.xml',
        'views/data.xml',
        'views/request_kcs_line_view.xml',
        'views/kcs_criterions_view.xml',
        'views/lot_kcs_view.xml',
        'views/lot_stack_allocation_view.xml',
        'views/stock_movement_view.xml',
        'views/stock_picking_view_kcs.xml',
        'views/pss_management_view.xml',
        'views/tolerance_quality_view.xml',
        'views/moisture_configuration_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

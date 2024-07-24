# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN VIETNAM INVENTORY',
    'category': 'SUCDEN VIETNAM INVENTORY',
    'version' : '16.0.1.0',
    'author': 'SUCDEN VIETNAM',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'sd_inventory', 'sd_master_vietnam'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'security/group.xml',
        'views/stack_merge_view.xml',
        'views/stock_picking_view.xml',
        'report/report.xml',
        'wizard/wizard_report_stack_merge_view.xml',
    ],
    'assets': {

    },
    'installable': True,
    'auto_install': False,
    'application': False,
}

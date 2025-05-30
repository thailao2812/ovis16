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
        'views/request_material_view.xml',
        'report/report.xml',
        'wizard/wizard_report_stack_merge_view.xml',
        'wizard/in_out_stack_quantity.xml',
        'views/device_profile_menu.xml',
        # 'views/device_telemetry_wizard.xml',
        'views/device_telemetry.xml',
        'views/stock_trucking_cost_view.xml',
        'views/menu.xml',
    ],
    'assets': {

    },
    'installable': True,
    'auto_install': False,
    'application': False,
}

# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN INDIA MRP',
    'category': 'Sucden India',
    'version' : '16.0.1.0',
    'author': 'Sucden Viet Nam',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'sd_india_master', 'sd_mrp', 'sd_india_inventory'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_bom_premium_view.xml',
        'views/mrp_operation_result_view.xml',
        'views/outturn_percent_view.xml',
        'views/processing_loss_approval_view.xml',
        'views/truck_quality_production_view.xml',
        'views/mrp_production_view.xml',
        'views/stock_picking_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

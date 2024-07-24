# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'SUCDEN Restful API',
    'version': '16.0',
    'category': 'SUCDEN 16',
    'depends': ['sd_inventory','sd_mrp'],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/sud_packing_branch.xml',
        'views/stock_view.xml',
        'views/mrp_operation_result.xml',
        'views/menu.xml',
        ],
    'installable': True,
    'auto_install': False,
}

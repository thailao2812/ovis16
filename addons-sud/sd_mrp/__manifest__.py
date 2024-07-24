# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN MRP',
    'category': 'REACH MRP',
    'version' : '16.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://www.reach.com.vn',
    'depends': ['sd_master','sd_quality','sd_purchase_contract','sd_inventory','mrp'],
    'description': """
    """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/group.xml',
        'wizard/wizard_request_materials.xml',
        
        #'data/example_users_data.xml',
        'views/mrp_production.xml',
        
        'views/master_code.xml',
        'views/mrp_bom.xml',
        'views/mrp_operation_result.xml',
        'views/result_produced_product_line.xml',
        'views/processing_loss_aproval.xml',
        'views/import_production_result.xml',
        'views/mrp_oee.xml',
        'views/mrp_bom_premium.xml',
        'views/stock_picking.xml',
        
        'wizard/import_material_request.xml',
        'views/menu.xml'

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

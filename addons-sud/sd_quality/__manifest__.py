# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN QUANLITY',
    'category': 'REACH contract',
    'version' : '15.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://www.reach.com.vn',
    'depends': ['base','sd_inventory', 'mrp','sd_master','sd_pur_sales'],
    'description': """
    """,
    'data': [
        'security/security.xml',
        
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        
        'security/ir.model.access.csv',
        'views/kcs_view.xml',
        'views/kcs_criterions.xml',
        'views/stock_picking.xml',
        'views/stock_picking.xml',
        'views/kcs_sample.xml',
        'views/request_kcs_line.xml',
        'views/restack_management.xml',
        'views/lot_kcs.xml',
        'views/lot_stack_allocate.xml',
        'views/pss_management.xml',
        'views/fob_management.xml',
        'views/fob_pss_management.xml',
        'views/glyphosate.xml',
        'views/vessel_registration.xml',
        'views/stock_movement.xml',
        'views/shipping_instruction.xml',
        'views/post_shipment.xml',
        'views/purchase_allocation.xml',
        'views/pss_management_nestle_view.xml',
        'views/stock_contract_allocation.xml',
        
        'views/stock_intake_quality.xml',
        'views/request_material.xml',
        
        'wizards/import_qc_view.xml',
        'wizards/wizard_glyphosat.xml',
        'wizards/wizard_cancel_confirmation.xml',
        
        'views/menu.xml',
        
        #Report
        'report/report_view.xml',
        
        #Data
        #'data/ir_sequence.xml'

    ],
# 'assets': {
#         'web.assets_backend': [
#             ''
#             'sd_quality/static/src/css/custom_quality_css.css',
#         ],
#     },
    'installable': True,
    'auto_install': False,
    'application': False,
}

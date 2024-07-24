# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN INVENTORY CONTRACT',
    'category': 'REACH contract',
    'version' : '16.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://www.reach.com.vn',
    'depends': ['base','stock','sd_master','sd_sale_contract','mrp', 'sd_purchase_contract'],
    'description': """
    """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        #'data/example_users_data.xml',
        
        'wizard/stock_stack_view.xml',
        'wizard/request_material.xml',
        'wizard/wizard_print_report.xml',
        'wizard/wizard_grn_import.xml',
        'wizard/in_out_stack_quanlity.xml',
        
        #'views/ned_certificate_license_views.xml',
        'views/stock_picking_type.xml',
        'views/stock_warehouse.xml',
        'views/stock_zone.xml',
        # 'views/stock_stack.xml',
        'views/stock_picking.xml',
        'views/stock_move_line.xml',
        'views/stock_storage_condition_views.xml',
        'views/production_lot.xml',
        'views/request_material.xml',
        'views/res_users_view.xml',
        'views/report_stock_balance_sheet.xml',
        'views/stock_material.xml',
        'views/stock_stack_transfer.xml',
        'views/stock_trucking_cost_view.xml',
        'views/request_stock_material_view.xml',
        'views/external_warehouse.xml',
        'views/by_product_derivable_view.xml',
        'views/stock_allocation_view.xml',

        # 'views/contract/nvp_contract.xml',
        # 'views/contract/nvp_quota.xml',
        # 'views/contract/nvp_quota_temp.xml',
        # 'views/contract/ptbf_contract.xml',
        # 'views/contract/allocation.xml',
        # 'views/contract/stock_allocation.xml',
        # 'views/contract/npe_nvp_relation.xml',
        'views/menu.xml',
        
        #Report
        'report/report_view.xml',
        
        #Data
        'data/ir_sequence.xml'

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

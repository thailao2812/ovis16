# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN PURCHASE CONTRACT',
    'category': 'REACH  contract',
    'version' : '15.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://www.reach.com.vn',
    'depends': ['base','stock', 'account','sd_master','sd_sale_contract','report_aeroo'],
    'description': """
    """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        
        'data/ir_sequence.xml',
        
        #Wizard
        'wizards/wizard_purchase_contract_view.xml',
        'wizards/wizard_ptbf_contract_view.xml',
        'wizards/import_p_contract_view.xml',
        
        #'views/ned_certificate_license_views.xml',
        'views/masterdata/fx_trade_root.xml',
        'views/masterdata/grades_premium_view.xml',
        'views/masterdata/condition_cost_fob_view.xml',
        'views/masterdata/cert_pre_view.xml',
        'views/masterdata/stoploss_config_view.xml',
        
        'views/contract/npe_contract.xml',
        'views/contract/nvp_contract.xml',
        'views/contract/nvp_quota.xml',
        'views/contract/nvp_quota_temp.xml',
        'views/contract/ptbf_contract.xml',
        'views/contract/allocation.xml',
        'views/contract/stock_allocation.xml',
        'views/contract/npe_nvp_relation.xml',
        'views/contract/request_payment.xml',
        'views/contract/owh_view.xml',
        #'views/contract/stock_picking.xml',
        'views/contract/purchase_contract_line_view.xml',

        
       
        'views/menu.xml',
        
        
        #Report
        'report/report_view.xml',
        
        #Data
        #'data/ir_sequence.xml'

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

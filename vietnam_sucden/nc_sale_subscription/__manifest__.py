# -*- coding: utf-8 -*-
{
    'name': 'SMN Sales Proposals',
    'version': '1.1',
    'category': 'Smartnet Own Modules',
    'author': 'SUCDEN',
    'website': 'https://sucdencoffee.vn/',
    'license': 'AGPL-3',
    'summary': 'Generate recurring and manage proposals',
    'description': """
This module allows you to manage proposals.

Features:
    - Create & edit proposals
    - Modify proposals with sales orders
""",
    'depends': [
        'sale_subscription', 'mail', 'rating', 'hr', 'product'
    ],
    'data': [
        #data
        'data/res_groups.xml',
        'data/sale_subscription_data.xml',
        'data/ir_config_paramter.xml',
        'data/mail_template.xml',
        
        'data/ir_module_category.xml',
        
        #security
        'security/ir.model.access.csv',

        #views
        'views/sale_subscription_views.xml',
        'views/sale_subscription_template_views.xml',
        'views/mail_template_views.xml',
        'views/sale_subscription_stage_views.xml',
        'views/hr_employee.xml',

        #wizad
        'wizards/sale_subscription_assign_view.xml',
        'wizards/sale_subscription_revert_view.xml',
        'wizards/sale_subscription_result_approval_view.xml',
        'wizards/sale_subscription_result_reject_view.xml',
        'wizards/sale_subscription_result_submit_view.xml',
    ],
    'application': True,
}

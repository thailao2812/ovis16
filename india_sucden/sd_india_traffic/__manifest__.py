# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN INDIA TRAFFIC',
    'category': 'Sucden India',
    'version' : '16.0.1.0',
    'author': 'Sucden Viet Nam',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'sd_india_contract', 'sd_india_account'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/fob_management_india_view.xml',
        'views/data.xml',
        'views/exchange_view.xml',
        'views/exchange_product_view.xml',
        'views/fixed_cost_view.xml',
        'views/ned_crop_view.xml',
        'wizard/wizard_search_purchase_contract_view.xml',
        'wizard/wizard_search_sale_contract.xml',
        'wizard/wizard_report_fob_statement_view.xml',
        'wizard/wizard_psc_to_sc_link_view.xml',
        'wizard/wizard_report_psc_to_sc_link_view.xml',
        'views/report_psc_to_sc_link_view.xml',
        'views/purchase_contract_view.xml',
        'views/market_india_view.xml',
        'views/item_group_view.xml',
        'views/contract_price_purchase_view.xml',
        'views/product_view.xml',
        'views/s_contract_view.xml',
        'views/sale_contract_view.xml',
        'views/shipping_instruction_view.xml',
        'views/report_fob_statement_view.xml',
        'views/sale_contract_india_view.xml',
        'views/ned_certificate_view.xml',
        'views/menu.xml'

    ],
'assets': {
        'web.assets_backend': [
            'sd_india_traffic/static/src/css/custom.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}

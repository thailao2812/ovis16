# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN INDIA CONTRACT',
    'category': 'Sucden India',
    'version' : '16.0.1.0',
    'author': 'Sucden Viet Nam',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'sd_pur_sales', 'sd_india_quality_control'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_reject_view.xml',
        'wizard/wizard_ptbf_contract_view.xml',
        'wizard/wizard_invoice_form_view.xml',
        'views/purchase_contract_view.xml',
        'views/s_contract_view.xml',
        'views/request_payment_view.xml',
        'views/transfer_order_view.xml',
        'views/delivery_order_view.xml',
        'views/sale_contract_view.xml',
        'views/ned_certificate_license_view.xml',
        'views/account_payment_view.xml',
        'views/post_shipment_view.xml',
        'views/stock_allocation_view.xml',
        'views/nvp_npe_relation_view.xml',
        'report/report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

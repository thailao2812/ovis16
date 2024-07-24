# -*- coding: utf-8 -*-
{
    'name': 'Sucden VN Report',
    'version': '16.0',
    'category': 'SUCDEN Report Manager',
    'depends': ['sd_quality','sd_purchase_contract','sd_pur_sales', 'sd_mrp','sd_inventory','sd_traffic'],
    'data': [
            'security/security.xml',
            'security/ir.model.access.csv',


            # 'shipment.xml',
            # 'report_view.xml',
            # 'tracking_qc_picking.xml',
            # 'production_report_view.xml',
            # 'report_grn_unallocated.xml',
            # 'fob_weight_franchise_view.xml',
            'views/production_report_view.xml',
            'views/sucden_syn_config_view.xml',
            'views/batch_report.xml',
            'views/production_analysis_view.xml',
            'views/batch_pnl_upgrade_view.xml',
            'views/input_value.xml',
            'views/output_value.xml',
            'views/faq_prod_loss_tracking.xml',
            'wizard/npe_unfixed_wizard.xml',
            'views/npe_master.xml',
            'views/stock_intake_week.xml',
            'views/stock_intake_supplier.xml',
            'views/faq_stack_tracking.xml',
            'views/production_plan_view.xml',
            'views/shipment_quality.xml',
            'views/internal_transfer_tracking.xml',
            'views/shipment.xml',
            'views/grn_matching_report.xml',
            'views/fob_deviation.xml',
            'views/fob_weight_franchise.xml',
            'views/report_grn_unallocated.xml',
            'views/long_short_fob_view.xml',
            'views/long_short_fob_v2_view.xml',
            'views/long_short_factory_view.xml',
            'views/cash_book_view.xml',
            'views/menu.xml',


            'report/report_view.xml',

            # 'supplier_contract.xml',
            # 'wizard/wizard_shippment.xml'
            ],
    'installable': True,
    'auto_install': False,
    'author': 'Sucden Vietnam Ltd',
}
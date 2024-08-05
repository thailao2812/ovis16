# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class WizardReportFobStatement(models.TransientModel):
    _name = "wizard.report.fob.statement"

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    product_ids = fields.Many2many('product.product', string='Item Group')
    item_group_ids = fields.Many2many('product.group', string='Item Group')
    sale_contract_ids = fields.Many2many('sale.contract.india')

    def button_render(self):
        self.env.cr.execute("""Delete from report_fob_statement""")
        if (not self.date_from or not self.date_to) and not self.sale_contract_ids:
            raise UserError(_("You have to input date from or date to, or input Contract to Generate Report"))
        if self.sale_contract_ids:
            for sale in self.sale_contract_ids:
                for line in sale.line_purchase_ids:
                    fob_value = forex = farm_gate = market_price = 0
                    market_month = False
                    if line.outturn / 100 == 0:
                        green_coffee = 0
                    else:
                        green_coffee = line.quantity * (line.outturn / 100)
                    if line.purchase_contract_id.fob_management_id:
                        fob_value = line.purchase_contract_id.fob_management_id.fob_usd
                        forex = line.purchase_contract_id.fob_management_id.forex_rate_inr
                        farm_gate = line.purchase_contract_id.fob_management_id.price
                        market_price = line.purchase_contract_id.fob_management_id.market_price
                        market_month = line.purchase_contract_id.fob_management_id.market_month and line.purchase_contract_id.fob_management_id.market_month.id or False
                    value_usd = (fob_value * green_coffee) / 1000
                    sale_value = fob_value * (green_coffee/1000) * forex
                    value_raw_coffee = (farm_gate/50) * green_coffee
                    margin_value = sale_value - value_raw_coffee
                    if green_coffee > 0:
                        margin_per_mt = (margin_value/green_coffee) * 1000
                    else:
                        margin_per_mt = 0
                    value = {
                        'item_id': sale.item_group_id.id,
                        'p_number': sale.id,
                        'p_date': sale.p_date,
                        'sn_no': sale.name,
                        'sn_date': sale.sn_date,
                        'purchase_contract': line.purchase_contract_id.id,
                        'pc_date': line.date_contract,
                        'no_of_bag': line.quantity / sale.line_ids[0].packing_id.capacity or 0,
                        'pc_qty': line.quantity,
                        'outturn': line.outturn,
                        'green_coffee': green_coffee,
                        'fob_value': fob_value,
                        'currency_uom': 'USD/MT',
                        'value_usd': value_usd,
                        'forex': forex,
                        'farm_gate': farm_gate,
                        'sale_value': sale_value,
                        'value_raw_coffee': value_raw_coffee,
                        'margin_value': margin_value,
                        'margin_per_mt': margin_per_mt,
                        'market_price': market_price,
                        'currency_uom_fob': 'USD / MT',
                        'contract_price': 0,
                        'currency_uom_2nd': False,
                        'market_month': market_month,
                        'differential': line.purchase_contract_id.differential_india
                    }
                    self.env['report.fob.statement'].create(value)

        if not self.sale_contract_ids:
            if not self.date_from or not self.date_to:
                raise UserError(_("You have to input Date From and Date To or else select Sale Contract you want!"))
            sale_contract = self.env['sale.contract.india'].search([
                ('p_date', '>=', self.date_from),
                ('p_date', '<=', self.date_to)
            ])
            if self.item_group_ids:
                sale_contract = sale_contract.search([
                    ('item_group_id', 'in', self.item_group_ids.ids)
                ])
            else:
                sale_contract = sale_contract.search([
                    ('item_group_id', '!=', False)
                ])
            for sale in sale_contract:
                for line in sale.line_purchase_ids:
                    fob_value = forex = farm_gate = market_price = 0
                    market_month = False
                    if line.outturn / 100 == 0:
                        green_coffee = 0
                    else:
                        green_coffee = line.quantity * (line.outturn / 100)
                    if line.purchase_contract_id.fob_management_id:
                        fob_value = line.purchase_contract_id.fob_management_id.fob_usd
                        forex = line.purchase_contract_id.fob_management_id.forex_rate_inr
                        farm_gate = line.purchase_contract_id.fob_management_id.price
                        market_price = line.purchase_contract_id.fob_management_id.market_price
                        market_month = line.purchase_contract_id.fob_management_id.market_month and line.purchase_contract_id.fob_management_id.market_month.id or False
                    value_usd = (fob_value * green_coffee) / 1000
                    sale_value = fob_value * (green_coffee / 1000) * forex
                    value_raw_coffee = (farm_gate / 50) * green_coffee
                    margin_value = sale_value - value_raw_coffee
                    if green_coffee > 0:
                        margin_per_mt = (margin_value / green_coffee) * 1000
                    else:
                        margin_per_mt = 0
                    value = {
                        'item_id': sale.item_group_id.id,
                        'p_number': sale.id,
                        'p_date': sale.p_date,
                        'sn_no': sale.name,
                        'sn_date': sale.sn_date,
                        'purchase_contract': line.purchase_contract_id.id,
                        'pc_date': line.date_contract,
                        'no_of_bag': line.quantity / sale.line_ids[0].packing_id.capacity or 0,
                        'pc_qty': line.quantity,
                        'outturn': line.outturn,
                        'green_coffee': green_coffee,
                        'fob_value': fob_value,
                        'currency_uom': 'USD/MT',
                        'value_usd': value_usd,
                        'forex': forex,
                        'farm_gate': farm_gate,
                        'sale_value': sale_value,
                        'value_raw_coffee': value_raw_coffee,
                        'margin_value': margin_value,
                        'margin_per_mt': margin_per_mt,
                        'market_price': market_price,
                        'currency_uom_fob': 'USD / MT',
                        'contract_price': 0,
                        'currency_uom_2nd': False,
                        'market_month': market_month,
                        'differential': line.purchase_contract_id.differential_india
                    }
                    self.env['report.fob.statement'].create(value)
        return {
            'name': _('Report FOB Statement'),
            'view_type': 'tree',
            'view_mode': 'tree',
            'view': [(self.env.ref('sd_india_traffic.report_fob_statement_tree_view').id, 'tree')],
            'res_model': 'report.fob.statement',
            'context': {'search_default_group_product_id': True, 'search_default_group_p_number': True},
            'domain': [],
            'type': 'ir.actions.act_window'
        }
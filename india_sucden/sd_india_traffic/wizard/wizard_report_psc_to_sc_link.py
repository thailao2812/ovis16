# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class WizardReportPSCtoSC(models.TransientModel):
    _name = "wizard.report.psc.to.sc"

    season_id = fields.Many2one('ned.crop', string='Season')
    item_group_ids = fields.Many2many('product.group', string='Item Group')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    sale_contract_ids = fields.Many2many('sale.contract.india')

    def button_render(self):
        self.env.cr.execute("""Delete from report_psc_sc_link""")
        if (not self.date_from and self.date_to) or (self.date_from and not self.date_to):
            raise UserError(_("You have to input date from and date to OR leave it blank to Generate Report!!"))
        p_contract = False
        if self.date_from and self.date_to:
            p_contract = self.env['sale.contract.india'].search([
                ('p_date', '>=', self.date_from),
                ('p_date', '<=', self.date_to)
            ])
        if self.season_id:
            p_contract = p_contract.filtered(lambda x: x.crop_id.id == self.season_id.id)
        if self.item_group_ids:
            p_contract = p_contract.filtered(lambda x: x.item_group_id.id in self.item_group_ids.ids)
        if self.sale_contract_ids:
            p_contract = self.sale_contract_ids
        if not p_contract:
            p_contract = self.env['sale.contract.india'].search([
                ('p_number', '!=', False)
            ])
        number = 1
        for p in p_contract:
            if p.sale_contract_factory_ids:
                for line in p.sale_contract_factory_ids:
                    if line.s_contract.type == 'export':
                        number = 1000
                    si = self.env['shipping.instruction'].search([
                        ('contract_id', '=', line.s_contract.id)
                    ])
                    if not si:
                        value = {
                            'p_number': p.id,
                            'p_qty': p.total_quantity,
                            'p_price': p.price_unit,
                            'p_amount': (p.total_quantity * p.price_unit) / number,
                            's_contract_id': line.s_contract.id,
                            'product_id': line.s_contract.product_id.id,
                            's_qty': line.s_contract.total_qty,
                            'allocated_qty': line.s_contract.total_allocated_sc,
                            'differential': line.s_contract.differential,
                            'packing_cost': line.s_contract.packing_cost,
                            'certificate_premium': line.s_contract.premium_cert,
                            's_total_price': p.price_unit + line.s_contract.differential + line.s_contract.packing_cost + line.s_contract.premium_cert,
                            's_contract_amount': ((p.price_unit + line.s_contract.differential + line.s_contract.packing_cost + line.s_contract.premium_cert) * line.s_contract.total_allocated_sc) / number,
                            'open_position': p.balance_quantity_sc,
                            'open_position_value': (p.balance_quantity_sc * p.price_unit) / number
                        }
                        self.env['report.psc.sc.link'].create(value)
                    if si:
                        for s in si:
                            value = {
                                'p_number': p.id,
                                'p_qty': p.total_quantity,
                                'p_price': p.price_unit,
                                'p_amount': (p.total_quantity * p.price_unit) / number,
                                's_contract_id': line.s_contract.id,
                                'shipping_instruction_id': s.id,
                                'product_id': line.s_contract.product_id.id,
                                's_qty': line.s_contract.total_qty,
                                'allocated_qty': line.s_contract.total_allocated_sc,
                                'differential': line.s_contract.differential,
                                'packing_cost': line.s_contract.packing_cost,
                                'certificate_premium': line.s_contract.premium_cert,
                                's_total_price': p.price_unit + line.s_contract.differential + line.s_contract.packing_cost + line.s_contract.premium_cert,
                                's_contract_amount': ((p.price_unit + line.s_contract.differential + line.s_contract.packing_cost + line.s_contract.premium_cert) * line.s_contract.total_allocated_sc) / number,
                                'open_position': p.balance_quantity_sc,
                                'open_position_value': (p.balance_quantity_sc * p.price_unit) / number
                            }
                            self.env['report.psc.sc.link'].create(value)
            else:
                value = {
                    'p_number': p.id,
                    'p_qty': p.total_quantity,
                    'p_price': p.price_unit,
                    'p_amount': p.total_quantity * p.price_unit,
                    's_contract_id': False,
                    'product_id': False,
                    's_qty': 0,
                    'allocated_qty': 0,
                    'differential': 0,
                    'packing_cost': 0,
                    'certificate_premium': 0,
                    's_total_price': p.price_unit,
                    's_contract_amount': 0,
                    'open_position': p.balance_quantity_sc,
                    'open_position_value': p.balance_quantity_sc * p.price_unit
                }
                self.env['report.psc.sc.link'].create(value)
        action = self.env.ref('sd_india_traffic.report_psc_to_sc_act_window')
        result = action.sudo().read()[0]
        res = self.env.ref('sd_india_traffic.report_psc_to_sc_link_tree_view', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['context'] = {'search_default_group_p_number': True, 'search_default_group_s_contract_id': True}
        return result
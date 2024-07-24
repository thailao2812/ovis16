# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class WizardPtbfContract(models.TransientModel):
    _inherit = "wizard.ptbf.contract"

    def button_convert(self):
        npe_nvp_relation = self.env['npe.nvp.relation']
        history_rate = self.env['history.rate']

        origin = ''
        contract_id = False
        for line in self.env['ptbf.fixprice'].browse(self._context.get('active_ids')):
            origin += line.contract_id.name
            origin += ';'
            contract_id = line.contract_id

        for line in self.contract_line_ids:
            vals = {
                'date_receive': self.date_order,
                'product_id': line.product_id.id,
                'rate': self.rate,
                'history_id': self._context.get('active_id'),
                'ptbf_id': line.purchase_contract_id.id,
                'qty_price': line.product_qty or 0.0,
                'final_price_en': line.price_fix,
                'final_price_vn': line.price_amount_vn or round((line.price_fix * line.contract_id.rate) / 1000, 0),
                # 'final_price':line.price_amount_vn,
                'total_amount_en': line.total_amount,
                'total_amount_vn': line.total_amount
            }
            history_rate.create(vals)
        return True


class wizard_ptbf_contract_line(models.TransientModel):
    _inherit = "wizard.ptbf.contract.line"

    @api.depends('product_qty', 'price_fix', 'contract_id.rate', 'contract_id')
    def _compute_amount(self):
        for line in self:
            line.total_amount = line.product_qty * line.price_fix
            #             line.total_amount_vn = line.product_qty/1000 * line.price_fix * line.contract_id.rate
            line.price_amount_vn = round((line.price_fix * line.contract_id.rate) / 1000, 0)
            line.total_amount_vn = line.price_amount_vn * line.product_qty
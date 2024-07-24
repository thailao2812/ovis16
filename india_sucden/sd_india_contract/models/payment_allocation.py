# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class PaymentAllocationLine(models.Model):
    _inherit = "payment.allocation.line"

    interest_pay = fields.Float(compute='_compute_interest_pay', string='Interest Pay/Year', readonly=True, store=True,digits=(12, 0))
    rate = fields.Float(string='Rate %', readonly=False, digits=(12, 2))

    @api.depends('pay_allocation_id.allocation_amount', 'pay_allocation_id', 'rate', 'from_date', 'to_date')
    def _compute_interest_pay(self):
        for line in self:
            total_date = date = (line.to_date - line.from_date).days
            contract = line.pay_allocation_id.contract_id
            interest_configuration = self.env['interest.configuration'].search([
                ('name', '=', contract.crop_id.id),
                ('state', '=', 'approve')
            ], limit=1)
            if interest_configuration:
                interest_pay = line.pay_allocation_id.allocation_amount * (line.rate / 100)
                if total_date > interest_configuration.number_of_day:
                    if total_date == 0:
                        date = 1
                        total_date = 1
                        interest_pay_one = (interest_pay / 365) * int(date)
                    else:
                        interest_pay_one = (interest_pay / 365) * int(date)
                else:
                    interest_pay_one = 0
            else:
                interest_pay_one = 0
                interest_pay = 0
            line.update({
                'total_date': total_date,
                'interest_pay': interest_pay,
                'actual_interest_pay': interest_pay_one
            })

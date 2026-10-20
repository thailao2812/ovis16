# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
from datetime import datetime
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class Parser(models.AbstractModel):
    _name = 'report.report_final_payment_purchase_contract'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_final_payment_purchase_contract'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()

        localcontext.update({
            'get_date': self.get_date,
            'get_address': self.get_address,
            'get_according_partner': self.get_according_partner,
            'get_total_invoice': self.get_total_invoice,
            'get_current_date': self.get_current_date
        })
        return localcontext

    def get_current_date(self):
        return self.get_date(date=None)

    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))

        date = date_user_tz.strftime('%d/%m/%Y')
        return date

    def get_address(self, partner_id):
        street = ''
        if partner_id:
            street = ', '.join([x for x in (partner_id.street, partner_id.street2) if x])
            if partner_id.district_id:
                street += ' ' + partner_id.district_id.name + ' '
            if partner_id.city:
                street += partner_id.city + ' '
            if partner_id.state_id:
                street += partner_id.state_id.name
        return street

    def get_according_partner(self, partner_id):
        if partner_id:
            child_id = partner_id.child_ids[0] if partner_id.child_ids else False
            if child_id:
                return child_id.name, child_id.function
            else:
                return None, None

    def get_total_invoice(self, purchase):
        if purchase:
            if purchase.invoice_lines_ids:
                return ('{:,}'.format(int(sum(purchase.invoice_lines_ids.mapped('quantity')))),
                        '{:,}'.format(int(sum(purchase.invoice_lines_ids.mapped('total_amount')))),
                        '{:,}'.format(int(sum(purchase.invoice_lines_ids.mapped('total_amount_tax')))))
            else:
                return 0, 0, 0

    def get_request_payment_from_payment_allocation(self, payment_allocation):
        if payment_allocation:
            payment = payment_allocation.pay_id
            request_payment = payment.request_payment_id
            return '{:,}'.format(int(request_payment.payment_quantity)), '{:,}'.format(int(request_payment.fix_price)), '{:,}'.format(int(request_payment.request_amount))
        else:
            return 0, 0, 0

    def get_other_data_request_payment_allocation(self, payment_allocation):
        if payment_allocation:
            payment = payment_allocation.pay_id
            request_payment = payment.request_payment_id
            return self.get_date(request_payment.date)
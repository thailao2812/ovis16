from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
from num2words import num2words
from currency2text import supported_language, currency_to_text
import datetime
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

bank_name = False
partner = False
account_holder = False
acc_number = False

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class Parser(models.AbstractModel):
    _name = 'report.report_stack_merge'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_stack_merge'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_stack_merge': self.get_stack_merge,
            'get_init_qty_history_stack': self.get_init_qty_history_stack,
            'get_si': self.get_si
        })
        return localcontext

    def get_stack_merge(self, date_from, date_to):
        stack_merge = self.env['stock.lot'].search([
            ('date', '>=', date_from),
            ('date', '<=', date_to)
        ])
        return stack_merge

    def get_init_qty_history_stack(self, stack):
        if stack:
            qty = sum(stack.move_line_ids.filtered(lambda x: x.picking_id.merge).mapped('init_qty'))
            return '{:,}'.format(int(qty))
        else:
            return 0

    def get_si(self, stack):
        if stack:
            lot_stack_allocation = self.env['lot.stack.allocation'].search([
                ('stack_id', '=', stack.id)
            ], limit=1)
            if lot_stack_allocation:
                return lot_stack_allocation.shipping_id.name
            else:
                return ''

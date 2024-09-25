# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class SContract(models.Model):
    _inherit = "s.contract"

    state = fields.Selection(
        [('draft', 'New'), ('submit', 'Submit'), ('approved', 'Approved'), ('done', 'Done'), ('cancel', 'Cancelled')],
        string='Status', readonly=True, copy=False, index=True, default='draft')

    status = fields.Selection(selection='_get_new_status_type', string='Shipped From')

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=False, readonly=True,
                                   states={'draft': [('readonly', False)]}, default=False)

    contract_line = fields.One2many('s.contract.line', 'contract_id', string='Contract Lines', readonly=False,
                                    states={}, copy=True)
    price_unit = fields.Float(string='Price Unit', related='contract_line.price_unit', store=True)

    @api.model
    def _default_document_contract(self):
        document_contract = self.env['document.contract'].search([
            ('name', 'not in', ['GSP Certificate', 'Certificate of Origin'])
        ])
        return document_contract

    document_contract = fields.Many2many('document.contract', string='Document', default=_default_document_contract)

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    @api.model
    def _get_new_status_type(self):
        return [('kushalnagar', 'Kushalnagar'), ('mangalore', 'Mangalore')]

    @api.constrains('date_from', 'date_to')
    def check_date_from_to(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_from > record.date_to:
                    raise UserError(_("Date from need < date to, please check again!"))

    def button_submit(self):
        for record in self:
            record.state = 'submit'

    def set_to_draft(self):
        for record in self:
            record.state = 'draft'

    @api.constrains('name')
    def _check_constraint_name(self):
        for record in self:
            s_contract = self.search([('name', '=', record.name),
                                      ('id', '!=', record.id)], limit=1)
            if s_contract:
                raise UserError(_("S Contract (%s) was exist.") % (record.name))

    def button_print_s_contract(self):
        return self.env.ref(
            'sd_india_contract.report_s_contract').report_action(self)

class SContractLine(models.Model):
    _inherit = 's.contract.line'

    number_of_bags = fields.Float(string="Number of bags", digits=(16, 0))
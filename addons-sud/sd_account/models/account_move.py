
# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class AccountMove(models.Model):
    _inherit = "account.move"
    
    product_id = fields.Many2one('product.product', 'Product', related='invoice_line_ids.product_id', readonly=True, store = True)
    commercial_name = fields.Char(string="Commercial", related='sale_contract_id.shipping_id.reference', store= True)
    
    
    @api.depends('account_analytic_id')
    def _get_company_analytic_account_id(self):
        company_analytic_account = False
        company_analytic_account = self.env['account.analytic.account'].search([('id', 'parent_of', self.account_analytic_id.ids), 
                                                                                    ('analytic_type','=','2')])
            
        self.company_analytic_account_id = company_analytic_account
        
        
    company_analytic_account_id = fields.Many2one('account.analytic.account', 'Company Analytic Account', 
                                                  compute='_get_company_analytic_account_id',
                                                  readonly=True, index=True, store=True)
    
    
    
    payment_reference = fields.Char(
        string='Invoice Number',
        index='trigram',
        copy=False,
        help="The payment reference to set on journal items.",
        tracking=True,
    )
    
    @api.depends('invoice_line_ids','invoice_line_ids.quantity')
    def _total_qty(self):
        for order in self:
            total_qty = 0
            for line in order.invoice_line_ids:
                total_qty += line.quantity
            order.total_qty = total_qty
            
    total_qty = fields.Float(compute='_total_qty', digits=(16, 3) , string='Total Qty',store =True)
    

    account_analytic_id =fields.Many2one('account.analytic.account',string= 'Analytic Account')
    
    trans_type = fields.Selection([('local', 'Local'), ('export', 'Fxport')], string='Trans Type', default='export', readonly=True) 
    
    currency_rate =fields.Float(string="Currency Rate")
    warehouse_id = fields.Many2one('stock.warehouse',string= 'Warehouse')
    
    
    # THANH 080123 - inherit fields
    # THANH 080123 - chuyển field name thành field thường và mặc định dấu '/' để sinh số sequence khi bấm button POST
    name = fields.Char(string='Number', compute=False,
                       copy=False, readonly=False, store=True, index='trigram',
                       tracking=True, default='/')
    
    # THANH 090123 - inherit odoo
    def _post(self, soft=True):
        # THANH - kiểm tra kỳ kế toán đã mở / đóng chưa
        # self._check_entry_date()
        for move in self:
            # THANH - generate sequence by company analytic account
            if move.name == '/' or move.name =='Draft':
                # Get the journal's sequence.
                if not move.journal_id.sequence_id:
                    raise UserError(_("Please define a sequence to journal '%s'.") % (move.journal_id.name))

                # Consume a new number.
                seq_date = move.date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                move.name = move.journal_id.sequence_id.with_context(company_id=move.company_id.id,
                                                    ir_sequence_date=seq_date).next_by_id()
                if move.move_type in ('out_refund','in_refund'):
                    move.name += 'R'

            # THANH - missing analytic account on income/expenses move line due to creating at menu Journal Entries
            # then need to reupdate on move line which missing aaa
            move.line_ids.filtered(lambda x: not x.analytic_account_id) \
                    .write({'analytic_account_id': move.account_analytic_id.id})
        res = super(AccountMove, self)._post(soft=soft)
        # THANH - compute counterpart account
        # for move in self:
        #     move._compute_counterpart_account()
        return res
    
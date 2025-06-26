# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _
import base64
import xlrd
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class WizardPurchaseContractLine(models.TransientModel):
    _inherit = 'wizard.purchase.contract.line'

    open_qty = fields.Float(string='Open Qty')
    request_payment_id = fields.Many2one('request.payment', string='Request Payment')
    remain_request_payment = fields.Float(string='Remain Request Payment', related='request_payment_id.remain_fix_qty',
                                          store=True)

    # @api.depends('purchase_contract_id')
    # def compute_open_qty(self):
    #     for rec in self:
    #         rec.open_qty = 0
    #         if rec.purchase_contract_id:
    #             rec.open_qty = rec.purchase_contract_id.open_qty


class WizardPurchaseContract(models.TransientModel):
    _inherit = 'wizard.purchase.contract'

    invoice_ids = fields.Many2many('account.move', string='Invoice')
    invoice_purchase_line_ids = fields.One2many('invoice.purchase.line', 'wizard_id', string='Invoice Purchase Line')
    amount_allocated_untaxed = fields.Float(string='Amount Allocated (Untaxed)', compute='_compute_amount_allocated',
                                            store=True)
    amount_allocated_tax = fields.Float(string='Amount Allocated (Tax)', compute='_compute_amount_allocated',
                                        store=True)
    amount_allocated_total = fields.Float(string='Amount Allocated (Total)', compute='_compute_amount_allocated',
                                          store=True)

    @api.depends('invoice_purchase_line_ids', 'invoice_purchase_line_ids.quantity',
                 'invoice_purchase_line_ids.invoice_id')
    def _compute_amount_allocated(self):
        for rec in self:
            untaxed = tax = total = 0.0
            for line in rec.invoice_purchase_line_ids:
                invoice = line.invoice_id
                if invoice and invoice.amount_total and invoice.amount_untaxed and invoice.invoice_line_ids:
                    total_qty = sum(invoice.invoice_line_ids.mapped('quantity'))
                    if total_qty > 0:
                        ratio = line.quantity / total_qty
                        untaxed += ratio * invoice.amount_untaxed
                        total += ratio * invoice.amount_total
            tax = total - untaxed
            rec.amount_allocated_untaxed = untaxed
            rec.amount_allocated_tax = tax
            rec.amount_allocated_total = total

    @api.model
    def default_get(self, fields):
        res = super(WizardPurchaseContract, self).default_get(fields)
        purchase_contract_id = self.env['purchase.contract'].browse(self._context.get('active_ids'))
        res['invoice_ids'] = [(6, 0, purchase_contract_id.invoice_ids.ids)]
        return res

    def button_convert(self):
        npe_nvp_relation = self.env['npe.nvp.relation']
        convert_line = self.env['open.qty.npe']
        if not self.invoice_purchase_line_ids:
            raise UserError(_("You need input invoice line and allocate it with quantity"))
        if self.contract_line_ids and self.invoice_purchase_line_ids:
            errors = []
            for contract in self.contract_line_ids:
                related_invoices = self.invoice_purchase_line_ids.filtered(
                    lambda l: l.invoice_id.purchase_contract_id.id == contract.purchase_contract_id.id
                )
                total_allocated = sum(related_invoices.mapped('quantity'))
                expected_quantity = contract.product_qty + contract.open_qty
                if total_allocated != expected_quantity:
                    contract_name = (
                        contract.contract_id.display_name
                        if hasattr(contract.contract_id, 'display_name')
                        else contract.contract_id.name
                    )
                    errors.append(
                        _("For contract '%s', allocated quantity in invoices (%s) does not match contract quantity (%s + %s = %s).") % (
                            contract_name, total_allocated, contract.product_qty, contract.open_qty, expected_quantity
                        )
                    )
            if errors:
                raise UserError('\n'.join(errors))

        for line in self.contract_line_ids:
            if line.qty_received < line.product_qty + line.open_qty + line.total_qty_fixed:
                raise UserError('Cannot create a NVP if Qty Received < Fixed + Qty Fix + Open Qty')
            if line.product_qty + line.open_qty == 0:
                raise UserError(_("Cannot create NVP with quantity = 0"))
            # if line.open_qty > 0:
            #     if line.purchase_contract_id.open_qty - line.open_qty < 0:
            #         raise UserError(_("You cannot input Qty No Advance more than you setting in NPE"))
            #     line.purchase_contract_id.open_qty -= line.open_qty

        origin = ''
        for line in self._context.get('active_ids'):
            origin += self.env['purchase.contract'].browse(line).name
            origin += ';'

        # Ràng buộc diều kiện lãi
        for line in self._context.get('active_ids'):
            for npe in self.env['purchase.contract'].browse(line):
                # if not npe.request_payment_ids:
                #     raise UserError('Please input request payment for NPE before Convert to NVP')
                # else:
                for pay in npe.request_payment_ids:
                    if not pay.rate_ids:
                        raise UserError('You need to input interest before convert to NVP')
                    for rate in pay.rate_ids:
                        if not rate.date or not rate.date_end:
                            raise UserError('You need to input interest and date from - date to before convert to NVP')

        active_id = self._context.get('active_id')
        company = self.env.user.company_id.id
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        npe = self.env['purchase.contract'].browse(active_id)
        npe_line = npe.contract_line[0]
        new_id = npe.copy({'warehouse_id': warehouse_id.id, 'name': 'New', 'nvp_ids': [], 'cert_type': 'normal',
                           'contract_line': [], 'type': 'purchase', 'npe_contract_id': active_id, 'origin': origin})
        # ràng buộc dữ liệu
        # Kiet + 7 date cập nhật deadline date
        new_id.license_id = npe.license_id.id if npe.license_id else False
        new_id.onchange_date_order()
        open_qty = 0
        for line in self.contract_line_ids:
            vals = {
                'npe_contract_id': line.purchase_contract_id.id,
                'contract_id': new_id.id,
                'product_qty': line.product_qty + line.open_qty or 0.0,
                'type': 'fixed',
                'open_qty': line.open_qty or 0.0,
                'request_payment_id': line.request_payment_id.id or False,
            }
            if line.open_qty > 0:
                value = {
                    'purchase_contract_id': new_id.id,
                    'contract_id': line.purchase_contract_id.id,
                    'qty': line.open_qty
                }

                convert_line.create(value)
            npe_nvp_relation.create(vals)
            open_qty = line.open_qty

        sql = '''
            select product_id,sum(product_qty) product_qty 
            FROM wizard_purchase_contract_line 
            WHERE contract_id = %s
            Group By product_id
        ''' % (self.id)
        self.env.cr.execute(sql)
        for r in self.env.cr.dictfetchall():
            npe_line.copy({'product_qty': r['product_qty'], 'price_unit': self.price_unit, 'contract_id': new_id.id})
            new_id.qty_received += r['product_qty']
        for line in new_id.contract_line:
            line.product_qty = line.product_qty + open_qty

        result = False
        if new_id:
            action = self.env.ref('sd_purchase_contract.action_purchase_contract')
            result = action.read()[0]
            res = self.env.ref('sd_purchase_contract.view_purchase_contract_form', False)
            result['context'] = {}
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = new_id.ids[0] or False
        for inv in self.invoice_purchase_line_ids:
            value = {
                'move_id': inv.invoice_id.id,
                'purchase_contract_id': new_id.id,
                'date': datetime.now().date(),
                'quantity': inv.quantity,
                'amount_allocated_untaxed': inv.amount_allocated_untaxed,
                'amount_allocated_tax': inv.amount_allocated_tax,
                'amount_allocated_total': inv.amount_allocated_total,
            }
            self.env['purchase.contract.invoice'].create(value)
        return result

class InvoicePurchaseLine(models.TransientModel):
    _name = 'invoice.purchase.line'

    wizard_id = fields.Many2one('wizard.purchase.contract', string='Wizard')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    quantity_invoice = fields.Float(string='Quantity Invoice', compute='_compute_quantity_invoice', store=True)
    quantity = fields.Float(string='Quantity')
    amount_allocated_untaxed = fields.Float(string='Amount Allocated (Untaxed)', compute='_compute_amount_allocated',
                                            store=True)
    amount_allocated_tax = fields.Float(string='Amount Allocated (Tax)', compute='_compute_amount_allocated',
                                        store=True)
    amount_allocated_total = fields.Float(string='Amount Allocated (Total)', compute='_compute_amount_allocated',
                                          store=True)

    @api.depends('invoice_id', 'quantity')
    def _compute_quantity_invoice(self):
        for rec in self:
            rec.quantity_invoice = 0
            if rec.invoice_id:
                rec.quantity_invoice = sum(rec.invoice_id.invoice_line_ids.mapped('quantity'))

    @api.depends('invoice_id', 'quantity')
    def _compute_amount_allocated(self):
        for rec in self:
            untaxed = tax = total = 0.0
            invoice = rec.invoice_id
            if invoice and invoice.amount_total and invoice.amount_untaxed and invoice.invoice_line_ids:
                total_qty = sum(invoice.invoice_line_ids.mapped('quantity'))
                if total_qty > 0:
                    ratio = rec.quantity / total_qty
                    untaxed += ratio * invoice.amount_untaxed
                    total += ratio * invoice.amount_total
            tax = total - untaxed
            rec.amount_allocated_untaxed = untaxed
            rec.amount_allocated_tax = tax
            rec.amount_allocated_total = total
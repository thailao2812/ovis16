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

    # @api.depends('purchase_contract_id')
    # def compute_open_qty(self):
    #     for rec in self:
    #         rec.open_qty = 0
    #         if rec.purchase_contract_id:
    #             rec.open_qty = rec.purchase_contract_id.open_qty


class WizardPurchaseContract(models.TransientModel):
    _inherit = 'wizard.purchase.contract'

    def button_convert(self):
        npe_nvp_relation = self.env['npe.nvp.relation']
        convert_line = self.env['open.qty.npe']

        for line in self.contract_line_ids:
            if line.qty_received < line.product_qty + line.open_qty + line.total_qty_fixed:
                raise UserError('Cannot create a NVP if Qty Received < Fixed + Qty Fix + Open Qty')
            if line.product_qty == 0:
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
                'open_qty': line.open_qty or 0.0
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
        return result
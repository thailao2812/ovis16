# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class WizardPurchaseContract(models.TransientModel):
    _inherit = "wizard.purchase.contract"

    def button_convert(self):
        npe_nvp_relation = self.env['npe.nvp.relation']

        for line in self.contract_line_ids:
            if line.product_qty == 0:
                raise UserError(_("Please input Quantity before Convert"))
            if line.qty_received < line.product_qty + line.total_qty_fixed:
                raise UserError('Cannot create a CR if Qty Received > Fixed + Qty Fix')
        origin = ''
        for line in self._context.get('active_ids'):
            origin += self.env['purchase.contract'].browse(line).name
            origin += ';'

        # Ràng buộc diều kiện lãi
        # India khong can rang buoc
        # for line in self._context.get('active_ids'):
        #     for npe in self.env['purchase.contract'].browse(line):
        #         # if not npe.request_payment_ids:
        #         #     raise UserError('Please input request payment for NPE before Convert to NVP')
        #         # else:
        #         for pay in npe.request_payment_ids:
        #             if not pay.rate_ids:
        #                 raise UserError('You need to input interest before convert to NVP')
        #             for rate in pay.rate_ids:
        #                 if not rate.date or not rate.date_end:
        #                     raise UserError('You need to input interest and date from - date to before convert to NVP')

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

        for line in self.contract_line_ids:
            vals = {
                'npe_contract_id': line.purchase_contract_id.id,
                'contract_id': new_id.id,
                'product_qty': line.product_qty or 0.0,
                'type': 'fixed',
            }
            npe_nvp_relation.create(vals)

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

        result = False
        if new_id:
            action = self.env.ref('sd_purchase_contract.action_purchase_contract')
            result = action.read()[0]
            res = self.env.ref('sd_purchase_contract.view_purchase_contract_form', False)
            result['context'] = {}
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = new_id.ids[0] or False
        return result

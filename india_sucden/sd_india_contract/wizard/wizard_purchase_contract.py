# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class WizardPurchaseContract(models.TransientModel):
    _inherit = "wizard.purchase.contract"

    price_per_bag = fields.Float(string="Price of Bag", compute="_compute_price_per_bag", store=True)

    @api.depends('price_unit', 'purchase_contract_id', 'purchase_contract_id.type')
    def _compute_price_per_bag(self):
        for rec in self:
            if rec.price_unit and rec.price_unit > 0:
                rec.price_per_bag = rec.price_per_bag = rec.price_unit * 50
            else:
                rec.price_per_bag = 0

    def button_convert(self):
        npe_nvp_relation = self.env['npe.nvp.relation']

        for line in self.contract_line_ids:
            if line.product_qty == 0:
                raise UserError(_("Please input Quantity before Convert"))
            if line.qty_received < line.product_qty + line.total_qty_fixed:
                raise UserError('Cannot create a CR if Qty Received > Fixed + Qty Fix')
            if line.product_qty > line.qty_unreceived:
                raise UserError(_("Please input Quantity < Qty Unfixed"))
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

    @api.model
    def default_get(self, fields):
        res = {}
        val = []
        sql = '''
                SELECT count(distinct partner_id) count_partner,
                        count(distinct delivery_place_id) count_place
                FROM purchase_contract
                WHERE id in (%s)
            ''' % (','.join(map(str, self._context.get('active_ids'))))
        self.env.cr.execute(sql)
        for r in self.env.cr.dictfetchall():
            if r['count_partner'] > 1:
                raise UserError('You must select NPE with the same Vendor.')
            if r['count_place'] > 1:
                raise UserError('You must select NPE with the same Delivery Place.')

        res['purchase_contract_id'] = self.env['purchase.contract'].browse(self._context.get('active_id')).id
        for active_id in self._context.get('active_ids'):
            if self._context.get('active_model', False) == 'ptbf.fixprice':
                contract_obj = self.env['purchase.contract'].browse(self._context.get('default_purchase_contract_id'))
            else:
                contract_obj = self.env['purchase.contract'].browse(active_id)

            for line in contract_obj.contract_line:
                product_remain_qty = 0.0
                for relation in self.env['npe.nvp.relation'].search([('npe_contract_id', '=', line.contract_id.id)]):
                    product_remain_qty += relation.product_qty or 0.0

                val.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom.id,
                    'product_qty': line.contract_id.qty_unfixed,
                    'purchase_contract_id': line.contract_id.id,
                    'qty_received': line.contract_id.qty_received or 0.0,
                    'total_qty_fixed': line.contract_id.total_qty_fixed or 0.0,
                    'qty_unreceived': line.contract_id.qty_received - product_remain_qty - line.contract_id.return_qty or 0.0,
                    'product_remain_qty': line.product_qty - product_remain_qty,
                    'return_qty': line.contract_id.return_qty or 0.0,
                }))
            res.update({'contract_line_ids': val})
        return res

class wizard_purchase_contract_line(models.TransientModel):
    _inherit = "wizard.purchase.contract.line"

    return_qty = fields.Float(string ='Return Quantity',digits=(12, 0))

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class NVPNPERelation(models.Model):
    _inherit = 'npe.nvp.relation'

    request_payment_ids = fields.One2many('request.payment', 'convert_id')
    remain_qty = fields.Float(compute='_compute_qty', string='Remaining Quantity', store=True)

    @api.depends('request_payment_ids', 'request_payment_ids.payment_quantity', 'request_payment_ids.state', 'product_qty')
    def _compute_qty(self):
        for rec in self:
            rec.remain_qty = rec.product_qty - sum(rec.request_payment_ids.mapped('payment_quantity'))

    @api.depends('npe_contract_id', 'contract_id', 'product_qty')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.npe_contract_id.name + ' convert to ' + rec.contract_id.name + ' with remain quantity ' + str(rec.remain_qty)


    def name_get(self):
        result = []
        for rec in self:
            name = rec.npe_contract_id.name + ' convert to ' + rec.contract_id.name + ' with remain quantity ' + str(int(rec.remain_qty))
            result.append((rec.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self._context.get('convert_npe'):
            purchase_contract_id = self.env['purchase.contract'].browse(self._context.get('purchase_contract_id'))
            if purchase_contract_id:
                relation_ids = purchase_contract_id.nvp_ids
                args += [('id', 'in', relation_ids.ids)]
            relation = self.search(args, limit=limit)
            return relation.name_get()
        return super(NVPNPERelation, self).name_search(name, args, operator, limit)
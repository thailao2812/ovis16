# -*- coding: utf-8 -*-
from odoo.addons import decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleSubscriptionTemplateLine(models.Model):
    _name = 'sale.subscription.template.line'

    @api.depends('price_unit', 'quantity', 'discount')
    def _compute_price_subtotal(self):
        for line in self:
            line_sudo = line.sudo()
            price = line.env['account.tax']._fix_tax_included_price(line.price_unit, \
                    line_sudo.product_id.taxes_id, [])
            line.price_subtotal = line.quantity * price * (100.0 - line.discount) / 100.0

    def _get_default_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.get_product_multiline_description_sale()
            self.price_unit = self.product_id.list_price

    name = fields.Text(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', default=_get_default_uom_id, \
                             string='Unit of Measure', required=True)
    price_unit = fields.Float(string='Unit Price', required=True, \
                              digits=dp.get_precision('Product Price'))
    product_id = fields.Many2one('product.product', string='Product', required=True)
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'))
    price_subtotal = fields.Float(compute='_compute_price_subtotal', string='Sub Total', \
                                  digits=dp.get_precision('Account'), store=True)
    template_id = fields.Many2one('sale.subscription.template', string='Template')
    code = fields.Char('Code')

class SaleSubscriptionTemplate(models.Model):
    _inherit = 'sale.subscription.template'

    role_ids = fields.Many2many('sale.subscription.stage.role', 'template_role_rel',\
                                'template_id', 'role_id', string='Rules')
    # product_ids = fields.One2many('sale.subscription.template.line', 'template_id', \
    #                               string='Products')
    # def write(self, vals):
    #     # if vals.get('sequence'):
    #     #     if self.env.uid != 2:
    #     #         raise UserError(_('You do not have permission to modify this document. Please contact your administrator.'))
    #     if (len(vals) > 1 or (not vals.get('payment_mode') and not vals.get('recurring_rule_boundary', False))) and self.env.uid !=2:
    #         raise UserError(_('You do not have permission to modify this document.'))
    #     result = super(SaleSubscriptionTemplate, self).write(vals)
    #     return result
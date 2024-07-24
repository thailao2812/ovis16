# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class NedCertificate(models.Model):
    _inherit = 'ned.certificate'

    sale_premium_line = fields.One2many('sale.premium.line', 'certificate_id')
    purchase_premium_line = fields.One2many('purchase.premium.line', 'certificate_id')


class SalePremiumLine(models.Model):
    _name = 'sale.premium.line'

    certificate_id = fields.Many2one('ned.certificate')
    item_group_id = fields.Many2one('product.group', string='Item Group')
    sale_premium = fields.Float(string='Sale Premium')


class PurchasePremiumLine(models.Model):
    _name = 'purchase.premium.line'

    certificate_id = fields.Many2one('ned.certificate')
    item_group_id = fields.Many2one('product.group', string='Item Group')
    purchase_premium = fields.Float(string='Purchase Premium')
# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class SPIC(models.Model):
    _name = "s.pic"

    name = fields.Char('PIC', size=128)
    code = fields.Char('Code', size=56)

class SPERIOD(models.Model):
    _name = "s.period"

    name = fields.Char(string='Ship Month', size=128)
    code = fields.Char('Code', size=56)
    date_from = fields.Date('From')
    date_to = fields.Date('To')

    @api.constrains('name')
    def check_name_duplicate(self):
        for record in self:
            check_data = self.search([
                ('name', '=', record.name),
                ('id', '!=', record.id)
            ], limit=1)
            if check_data:
                raise UserError(_("You cannot create Shipt Month that already have in the system!!!"))

class SShipBy(models.Model):
    _name = "s.ship.by"

    name = fields.Char(string='Ship By', size=128)
    code = fields.Char('Code', size=56)

class PssSent(models.Model):
    _name = "pss.sent"

    awb= fields.Char(string="AWB")
    kgs = fields.Float(string="KGS")
    ref_no = fields.Char(string="PSS ref. No.")
    date_sent = fields.Date(string="Date Sent")
    signed_by = fields.Char(string="Signed by")
    aproved_date = fields.Date(string="Approved date")
    x_type = fields.Selection( [('PSS', 'PSS'), 
                                ('OTA', 'OTA'), 
                                ('Pesticide', 'Pesticide'),
                                ('Offer sample', 'Offer sample'), 
                                ('Chemical residue analysis', 'Chemical residue analysis'), 
                                ('Cupping', 'Cupping'), 
                                ('Others', 'Others')], string='Type')
    rejected_date = fields.Date(string="Rejected date")
    delivered_date = fields.Date(string="Delivered date")
    courier = fields.Char(string="Courier", default='DHL')
    quality = fields.Many2one('product.product',string="Quality")
    s_contract_id = fields.Many2one('s.contract', string='Pss Sent.')
    x_remark = fields.Char(string='Remark', size=256)
#

    
class DeliveryPlace(models.Model):
    _inherit = "delivery.place"
    
    #
    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     if not self.partner_id:
    #         self.update({'province_id': False})
    #         return
    #     values = {
    #         'currency_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.currency_id.id or False,
    #         'province_id': self.partner_id.state_id and self.partner_id.state_id.id or False 
    #         }
    #     self.update(values)
    

class DeliveryAccount(models.Model):
    _inherit = "delivery.account"
    
    
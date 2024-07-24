# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class DeliveryAccount(models.Model):
    _name = "delivery.account"
    
    debit_acc_id = fields.Many2one('account.account', string='Debit Acc', )
    credit_acc_id = fields.Many2one('account.account', string='Credit Acc')
    values = fields.Float(string='Values',required=True)
    description = fields.Char(string='Description',size=256)
    place_id = fields.Many2one('delivery.place', string='Account', required=False,)
    
    
class DeliveryPlace(models.Model):
    _name = "delivery.place"
    
    @api.model
    def _default_currency_id(self):
        currency_ids = self.env['res.currency'].search([], limit=1)
        return currency_ids
    
    province_id = fields.Many2one("res.country.state", 'Province')
    name = fields.Char(string='Place Name', required=True, default="New")
    code = fields.Char(string="Code")
    description = fields.Text(string='Description', required=False)
    type = fields.Selection([('sale', 'Sale'),('transport', 'Transport'), ('purchase', 'Purchase'),
                             ('port', 'Port'),('Loading Place', 'Loading Place')], string='Type', default='transport')
    partner_id = fields.Many2one('res.partner', string='Customer', required=False, domain=[('transfer', '=', True)])
    transit_cost = fields.Float(string='Transit Cost', default=0.0) 
    currency_id = fields.Many2one("res.currency", string="Currency", default=_default_currency_id)
    account_ids = fields.One2many('delivery.account','place_id',string="Account")
    active = fields.Boolean(string='Active', default=True)
    phone = fields.Char(string="Phone",size=128)
    fax = fields.Char(string="Fax",size=128)
    address = fields.Char(string="Address",size=128)
    recipient = fields.Char(string="Recipient",size=128)
    
    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     context = self._context or {}
    #     if context.get('picking_type_code', False):
    #         if context['picking_type_code'] == 'incoming':
    #             args += [('type', '=', 'purchase')]
    #         if context['picking_type_code'] == 'outgoing':
    #             args += [('type', '=', 'transport')]
    #     return super(DeliveryPlace, self).search(args, offset, limit, order, count=count)

    @api.constrains('code', 'name')
    def _check_code_name(self):
        for rec in self:
            checking = self.search([
                '|',
                ('code', '=', rec.code),
                ('name', '=', rec.name),
                ('id', '!=', rec.id)
            ], limit=1)
            if checking:
                raise UserError(_("You cannot create duplicated data here!!!! Please check again!"))
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.update({'province_id': False})
            return
        values = {
            'currency_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.currency_id.id or False,
            'province_id': self.partner_id.state_id and self.partner_id.state_id.id or False 
            }
        self.update(values)
        


class NedCrop(models.Model):
    _name = 'ned.crop' 
    _order = 'create_date desc, id desc'
    
    name = fields.Char(string='Crop', required=True, copy=False, index=True, default='New')
    short_name = fields.Char(string='Short Name', required=False)
    start_date = fields.Date('Start Date', required=True ,  copy=False)
    to_date = fields.Date('End Date', required=True ,  copy=False)
    description = fields.Text('Description', copy=False)
    state = fields.Selection([('current', 'Current'), ('previous', 'Previous')], string='Status', copy=False , required=True, default='current')
    
    create_date = fields.Date(string='Creation Date', readonly=True, index=True, default=fields.Datetime.now)
    create_uid = fields.Many2one('res.users', 'Responsible', readonly=True , default=lambda self: self._uid)
        

class ShippingLine(models.Model):
    _name = 'shipping.line' 
    _order = 'create_date desc, id desc'
    
    name = fields.Char(string='Shipping Line', required=True, copy=False, index=True)
    active = fields.Boolean(string="Active", default=True)


class PackingTerms(models.Model):
    _name ="packing.terms"
    _order = 'id desc'
    
    name = fields.Char(string="Name")
    vietnamese = fields.Char(string="Vietnamese")
    english = fields.Char(string="English")
    
class MarketPrice(models.Model):
    _name ="market.price"
    _order = 'mdate desc'
    
    
    mdate =  fields.Date(string="MDate")
    interbankrate = fields.Float(string="Interbank Rate")
    price = fields.Float(string="Price")
    bankceiling =fields.Float(string="Bank Ceiling")
    note = fields.Char(string="Note")
    bank_floor = fields.Float(string="Bank Floor")
    eximbank = fields.Float(string="Eximbank")
    techcombank = fields.Float(string="Techcombank")
    acb_or_vietinbank = fields.Float(string="ACB or Vietinbank")
    commercialrate = fields.Float(string="Commercial Rate")
    exporter_faq_price = fields.Float(string="BMT exported FAQ")
    liffe_month = fields.Char(string="LIFFE Month")
    liffe = fields.Char(string="LIFFE")
    g2difflocal = fields.Float(string="Collector Diff")
    g2difffob = fields.Float(string="FOB Diff")
    
    g2_replacement = fields.Float(string='G2 Replacement')
    faq_price = fields.Float(string='FAQ Price')
    fob_price = fields.Float(string='FOB Price')
    grade_price = fields.Float(string='Grade Price')
    
    
    privatedealer_faq_price = fields.Float(string="BMT Collector FAQ")
    dn_faq_ask = fields.Float(string="DN FAQ Ask")
    dn_g2_ask = fields.Float(string="DN G2 Ask")
    bmt_faq_ask = fields.Float(string="BMT FAQ Ask")
    bmt_g2_ask = fields.Float(string="BMT G2 Ask")
    dn_exporter_faq = fields.Float(string="DN Exporter FAQ")
    dn_exporter_g2 = fields.Float(string="DN Exporter G2")
    bmt_exporter_g2 = fields.Float(string="BMT Exporter G2")
    bmt_collector_g2 = fields.Float(string="BMT Collector G2")
    
    
    

class NedPacking(models.Model):
    _name = 'ned.packing'
    _order = 'id desc'

    name = fields.Char(string="Packing",size=256,required=True)
    vn_description = fields.Char(string="VN Description",size=256)
    en_description = fields.Char(string="EN Description",size=256)
    capacity = fields.Float(string="Capacity",digits=(16,0))
    tare_weight = fields.Float(string="Tare weight",digits=(16,2))
    price = fields.Float(string="Price",digits=(16,0))
    Premium = fields.Float(string="Premium", digits=(16,2))
    active = fields.Boolean(string="Active",default=True)
    
class NedFumigation(models.Model):
    _name = 'ned.fumigation'
    _order = 'id desc'
    
    name = fields.Char(string="Fumigation",size=256,required=True)

class NedCertificate(models.Model):
    _name = 'ned.certificate'
    _order = 'active desc, id desc'
    
    @api.model
    def _default_currency_id(self):
        currency_ids = self.env['res.currency'].search([], limit=1)
        return currency_ids

    def name_get(self):
        result = []
        for cert in self:
            result.append((cert.id, "%s" % ( cert.code and cert.code or cert.name)))
        return result
    
    name = fields.Char(string='Certificate', required=True, copy=False, index=True, default='New')
    code = fields.Char(string='Code', required=True, copy=False, index=True)
    premium = fields.Float(string='Premium', required=True, copy=False, index=True, default=0)
    currency_id = fields.Many2one("res.currency", string="Currency", required=True, default=_default_currency_id)
    description = fields.Text('Description', copy=False)
    active = fields.Boolean(string='Active', default=True, copy=False)
    name_print = fields.Char(string='Certificate Print', required=True)
    combine = fields.Boolean(string='Is Combine')

    
    
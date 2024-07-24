# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class StockZone(models.Model):
    _name = "stock.zone"
    _inherit = ['mail.thread']
    _order = 'create_date desc, id desc'
    
    name = fields.Char(string='Name', required=True, size=128)
    code = fields.Char(string='Code', required=False, size=128)
    description = fields.Char(string='Description', required=False, size=128)
    # stack_ids = fields.One2many('stock.stack', 'zone_id' , string='Stack Line')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    active = fields.Boolean(string='Active', default=True)
    hopper = fields.Boolean(string='HOPPER', default=False)
    location_wip = fields.Boolean(string='Location Wip', default=False)
    
    
    @api.constrains('name')
    def is_code_uniq(self):
        for zone in self:
            zone_ids = self.search([('name','=', zone.name),
                                              ('id','<>', zone.id)])
            if zone_ids:
                raise ValidationError(_(
                    "Zone is Exist"
                ))
        return True



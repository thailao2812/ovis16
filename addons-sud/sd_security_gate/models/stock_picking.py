

import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from lxml import etree
import base64
import xlrd
import math
utr = [' ',',','.','/','<','>','?',':',';','"',"'",'[','{','}',']','=','+','-','_',')','(','*','&','^','%','$','#','@','!','`','~','|']
"""
Used for queue incoming trucks and collect truck data. 
Requiring approval from procurement staff for converting to GRN form.
"""

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    @api.depends('picking_type_id')
    def _compute_transfer_picking_type(self):
        for this in self:
            if this.picking_type_id and this.picking_type_id.code =='incoming' and this.picking_type_id.operation == 'station':
                this.transfer_picking_type = True
        return
    
    security_gate_id = fields.Many2one('ned.security.gate.queue','Security Gate')
    transfer_picking_type = fields.Boolean('Transfer Picking Type',compute='_compute_transfer_picking_type',store = True)
    check_link_backorder = fields.Boolean('Check Link Back Order',compute='_compute_check_link_backorder',store = True)
    trucking_id = fields.Many2one('res.partner', string='Trucking Co')
    link_backorder_id = fields.Many2one('stock.picking','Link Backorder',domain=[('picking_type_id.code','=','incoming'),
                                                                                 ('state','=','done'),
                                                                                 ('picking_type_id.operation','=', 'factory')])
    
    
    def button_link_backorder(self):
        for pick in self:
            if pick.link_backorder_id:
                for old_backorder_id in self.env['stock.picking'].sudo().search([('backorder_id','=',pick.id)]):
                    if old_backorder_id.backorder_id:
                        old_backorder_id.origin = ''
                        old_backorder_id.backorder_id = False

                names =''
                if pick.link_backorder_id.origin:
                    names = (pick.description_name) + '; '+ pick.link_backorder_id.origin
                else:
                    names = (pick.description_name)
                pick.link_backorder_id.backorder_id = pick.id
                pick.link_backorder_id.origin = names
        return
    
    @api.depends('backorder_id')
    def _compute_check_link_backorder(self):
        for this in self:
            if this.backorder_id:
                this.sudo().backorder_id.check_link_backorder = True
        return
    
    @api.model
    def create(self, vals):
        #Kiet chua ro
        # if vals.get('warehouse_id') and not self.env['stock.warehouse'].browse(vals.get('warehouse_id')).sequence_id:
        #     raise UserError(_("No Session Sequence is defined for this shop yet."))
        
        res = super(StockPicking, self).create(vals)
        return res
        
        if res.picking_type_id and res.picking_type_id.code =='incoming' and res.picking_type_id.operation == 'factory' and res.warehouse_id and res.warehouse_id.sequence_id:
            crop = self.env['ned.crop'].sudo().search([('start_date','<=',datetime.now().date()),('to_date','>=',datetime.now().date())],limit = 1)
            if crop:
                name = self.env['stock.warehouse'].browse(res.warehouse_id.id).sequence_id.next_by_id()
                res.name = _(name)[0:len(res.warehouse_id.sequence_id.prefix)] + '-' + _(crop.short_name) + '.' + _(name)[len(res.warehouse_id.sequence_id.prefix):len(res.warehouse_id.sequence_id.prefix)+res.warehouse_id.sequence_id.padding]
        return res
    
    # def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
    #     if context is None:
    #         context = {}
    #     res = super(StockPicking, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
    #
    #     if view_type == 'form':
    #         doc = etree.XML(res['arch'])
    #         # Kim: Edit xml 
    #         for node in doc.xpath("//field[@name='partner_id']"):
    #             node.set('attrs', """{'required': [('transfer_picking_type', '!=', False)],
    #                                   'invisible': [('picking_type_code', 'in',('production_in','production_out','phys_adj'))],
    #                                          'readonly': [('state', 'in',('cancel','done'))]
    #                 }""")
    #         xarch, xfields = self._view_look_dom_arch(cr, uid, doc, view_id, context=context)
    #         res['arch'] = xarch
    #         res['fields'] = xfields
    #     if view_type == 'tree':
    #         doc = etree.XML(res['arch'])
    #         for node in doc.xpath("//field[@name='security_gate_id']"):
    #             if not context.get('picking_grn_Goods'):
    #                 node.set('invisible', '1')
    #
    #         for node in doc.xpath("//field[@name='link_backorder_id']"):
    #             if not context.get('fot'):
    #                 node.set('invisible', '1')
    #
    #         xarch, xfields = self._view_look_dom_arch(cr, uid, doc, view_id, context=context)
    #         res['arch'] = xarch
    #         res['fields'] = xfields
    #     return res
    

    
    
    
    

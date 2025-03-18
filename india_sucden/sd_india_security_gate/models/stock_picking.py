# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    quality_slip_no = fields.Char(string='1St Quality Slip No', related='security_gate_id.quality_slip_no', store=True)

    type_contract = fields.Selection([
        ('cr', 'CR'),
        ('cs', 'CS'),
        ('ra_cr', 'RA-CR'),
        ('ra_cs', 'RA-CS'),
        ('sdv_cr', 'SDV-CR'),
        ('sdv_cs', 'SDV-CS'),
        ('eudr_cr', 'EUDR-CR'),
        ('eudr_cs', 'EUDR-CS'),
    ], string='Type Contract', related='security_gate_id.type_contract', store=True)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += [('name', operator, name)]
        if self.env.context.get('stock_allocation_india'):
            contract_id = self.env['purchase.contract'].browse(self.env.context.get('contract_id'))
            if contract_id and contract_id.type == 'purchase':
                if name:
                    args = [('partner_id','=',contract_id.partner_id.id),('picking_type_code','=','incoming'),
                            ('qty_available','!=',0),('state_kcs','=','approved'),
                            ('date_done','>=',contract_id.date_order), ('product_id', '=', contract_id.product_id.id),
                            ('allocation_id','=',False), ('name', operator, name)]
                else:
                    args = [('partner_id', '=', contract_id.partner_id.id), ('picking_type_code', '=', 'incoming'),
                            ('qty_available', '!=', 0), ('state_kcs', '=', 'approved'),
                            ('date_done', '>=', contract_id.date_order), ('product_id', '=', contract_id.product_id.id),
                            ('allocation_id', '=', False)]
            if contract_id and contract_id.type == 'consign':
                if name:
                    args = [('partner_id', '=', contract_id.partner_id.id), ('picking_type_code', '=', 'incoming'),
                            ('qty_available', '!=', 0), ('state_kcs', '=', 'approved'),
                            ('packing_id', '=', contract_id.packing_id.id), ('total_bag', '=', contract_id.number_of_bags),
                            ('date_done', '>=', contract_id.date_order), ('product_id', '=', contract_id.product_id.id),
                            ('allocation_id', '=', False), ('name', operator, name)]
                else:
                    args = [('partner_id', '=', contract_id.partner_id.id), ('picking_type_code', '=', 'incoming'),
                            ('qty_available', '!=', 0), ('state_kcs', '=', 'approved'),
                            ('packing_id', '=', contract_id.packing_id.id),
                            ('total_bag', '=', contract_id.number_of_bags),
                            ('date_done', '>=', contract_id.date_order), ('product_id', '=', contract_id.product_id.id),
                            ('allocation_id', '=', False)]
        print(args)
        picking = self.with_context(from_name_search=True).search(args, limit=limit)
        return picking.name_get()
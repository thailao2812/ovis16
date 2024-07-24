# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class ShippingSplit(models.Model):
    _inherit = 'shipping.split'

    traffic_id = fields.Many2one('traffic.contract', string='Traffic Link')

    @api.onchange('traffic_id', 'new_qty')
    def onchange_traffic(self):
        for record in self:
            if record.traffic_id:
                if record.traffic_id:
                    record.name = record.traffic_id.name
                    record.qty_contract = float(record.traffic_id.p_qty)
                if record.new_qty:
                    record.res_qty = record.qty_contract - record.new_qty

    def split_scontract(self):
        for rc in self:
            mess = ''
            if rc.traffic_id:
                s_contract = self.env['s.contract'].search([
                    ('traffic_link_id', '=', rc.traffic_id.id)
                ])
                if s_contract:
                    shipping_instruction = self.env['shipping.instruction'].search([
                        ('contract_id', 'in', s_contract.ids)
                    ])
                    if shipping_instruction:
                        sale_contract = self.env['sale.contract'].search([
                            ('shipping_id', 'in', shipping_instruction.ids)
                        ])
                        for i in sale_contract:
                            if i.state != 'cancel' and i.detail_ids:
                                mess += "Your S Contract have Allocated with P Contract in %s, " \
                                        "please delete allocated P contract from S-P Allocation before Split S " \
                                        "Contract \n"\
                                        % i.name
                        if mess != '':
                            raise UserError(_(mess))
                record = rc.traffic_id
                parent_id = record.parent_id and record.parent_id or record
                rc_name = parent_id.name or ''
                parent_id = parent_id.id
                if parent_id == record.id:
                    counts = 1
                else:
                    counts = len(self.env['traffic.contract'].search([('parent_id', '=', parent_id)])) + 1

                new_record = record.copy({
                    'name': '%s-%s' % (rc_name, str(int(counts) + 1)),
                    'port_of_loading': record.port_of_loading and record.port_of_loading.id,
                    'port_of_discharge': record.port_of_discharge and record.port_of_discharge.id or 0,
                    'p_qty': rc.new_qty,
                    'parent_id': parent_id,
                    'no_of_pack': round((rc.new_qty / 60), 0),
                })
                record.write({
                    'p_qty': rc.res_qty,
                    'no_of_pack': round((rc.res_qty / 60), 0),
                    'name': '%s-%s' % (rc_name, str(int(counts)))
                })
                return {
                    'name': 'S Contract',
                    'view_type': 'form',
                    'view_mode': 'tree',
                    'domain': ['|', ('parent_id', '=', parent_id), ('id', '=', parent_id)],
                    'res_model': 'traffic.contract',
                    'type': 'ir.actions.act_window',
                    'target': 'current'
                }
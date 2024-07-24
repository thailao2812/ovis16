# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from datetime import datetime
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"
DAT= "%Y-%m-%d"
from odoo.exceptions import ValidationError, UserError


class StockStackTransfer(models.Model):
    _inherit = 'stock.stack.transfer'
    _description = "Zone to Zone"

    from_building = fields.Many2one('building.warehouse', string='From Building')
    to_building = fields.Many2one('building.warehouse', string='To Building')
    type = fields.Selection([
        ('zone', 'Zone'),
        ('building', 'Building')
    ], string='Type')
    document = fields.Char(string="Document Number")
    doc_date = fields.Date(string='Doc Date')

    @api.onchange('stack_id')
    def onchange_stack_id_for_building(self):
        if self.stack_id:
            self.from_building = self.stack_id.building_id
        else:
            self.from_building = False

    def button_transfer_building(self):
        for lock in self:
            if lock.to_building:
                if lock.to_building.warehouse_id != lock.from_building.warehouse_id:
                    raise UserError(_("You have to choose building inside this WH %S")
                                    % lock.from_building.warehouse_id.name)
                lock.stack_id.building_id = lock.to_building.id
            if lock.to_zone_id:
                if lock.to_zone_id.warehouse_id != lock.from_zone_id.warehouse_id:
                    raise UserError(_("You have to choose zone inside this WH %S")
                                    % lock.from_zone_id.warehouse_id.name)
                lock.stack_id.zone_id = lock.to_zone_id.id
            if not lock.to_building and not lock.to_zone_id:
                raise UserError(_("You have to input To zone or To building in order to Approve this transfer!!"))
            self.write({'state': 'approved', 'user_approve_id': self.env.uid,
                        'date_approve': datetime.now()})

    def set_to_draft(self):
        for record in self:
            record.state = 'draft'
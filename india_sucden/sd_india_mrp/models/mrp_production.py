# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    transaction_no = fields.Char(string='Transaction No.')

    def button_mark_done(self):
        # Kiet hàm check lại thông tin
        for production in self:
            note = ''
            if len(production.move_line_material_ids.filtered(lambda d: d.state not in ('cancel', 'done'))) >= 1:
                for gip in production.move_line_material_ids.filtered(lambda d: d.state not in ('cancel', 'done')):
                    note += gip.picking_id.name + '; '
                raise UserError(
                    _('Please done GIP: \n %s \n before done this Manufacturing Order - %s') % (note, production.name))

            if len(production.move_line_finished_good_ids.filtered(lambda d: d.state not in ('cancel', 'done'))) >= 1:
                for grp in production.move_line_finished_good_ids.filtered(lambda d: d.state not in ('cancel', 'done')):
                    note += grp.picking_id.name + ';'
                raise UserError(
                    _('Please done GRP: \n %s \n before done this Manufacturing Order - %s') % (note, production.name))

            if production.product_issued == 0 and production.product_received == 0:
                raise UserError(
                    _('The total Issued amount and total received amount = 0. You can not Done this MO - %s , please check again!!') % (
                        production.name))

            if production.product_balance > 0:
                raise UserError(
                    _('The balance amount of this MO - %s,  > 0. You can not Done this MO!!') % (production.name))

            production.write({
                'date_finished': fields.Datetime.now(),
                # Kiệt doạn này cần sửa lại thành phẩm sản xuất được
                # 'product_qty': production.qty_produced,
                'priority': '0',
                'is_locked': True,
                'state': 'done',
            })
        self._compute_qty()
        self.create_report_pnl()
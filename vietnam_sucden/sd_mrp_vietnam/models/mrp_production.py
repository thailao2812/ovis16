# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"    

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_cancel(self):
        """ Kiểm tra các điều kiện rùi cập nhật trạng thái cancel """
        if self.state == 'done':
            raise UserError(_('The Other is Done, cannot cancel'))
        # Trường hợp đã tạo git rùi thì ko có tạo phiếu Cancel
        if self.request_count > 0:
            for production in self:
                note = ''
                if len(production.move_line_material_ids.filtered(lambda d:d.state != 'cancel')) >= 1:
                    for gip in production.move_line_material_ids.filtered(lambda d:d.state != 'cancel'):
                        note += gip.picking_id.name +'; ' 
                    raise UserError(_('Please cancel GIP: \n %s \n before cancel this Manufacturing Order - %s')%(note, production.name))

                if len(production.move_line_finished_good_ids.filtered(lambda d:d.state != 'cancel')) >= 1:
                    for grp in production.move_line_finished_good_ids.filtered(lambda d:d.state != 'cancel'):
                        note += grp.picking_id.name +';' 
                    raise UserError(_('Please cancel GRP: \n %s \n before cancel this Manufacturing Order - %s')%(note, production.name))

            # raise UserError(_('You have Request Material for this MO, cannot Cancel it!'))

        self.state = 'cancel'
        # self._action_cancel()
        return True
 
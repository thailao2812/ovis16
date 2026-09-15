# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from datetime import datetime, date, timedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
import time
from odoo.exceptions import ValidationError, UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    state_kcs = fields.Selection(
        selection=[('draft', 'New'), ('confirmed', 'Confirmed'), ('waiting', 'Waiting Another Operation'), ('approved', 'Approved'),
                   ('rejected', 'Rejected'), ('cancel', 'Cancel')], string='KCS Status', readonly=True, copy=False,
        index=True, default='draft', tracking=True, )

    def button_qc_confirm(self):
        for pick in self:
            if not pick.kcs_line:
                raise UserError(_('You cannot Confirm this Request KCS without any Request KCS Line.'))

            for line in pick.kcs_line:
                if line.bb_sample_weight == 0 or line.sample_weight == 0 :
                    raise UserError(_('You need to input sample weigh or sample weight before Confirm'))

            pick.state_kcs = 'confirmed'

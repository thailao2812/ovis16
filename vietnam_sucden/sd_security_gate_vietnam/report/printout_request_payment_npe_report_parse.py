# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser

import datetime
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

bank_name =False
partner = False
account_holder = False
acc_number = False

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

import datetime
from datetime import datetime
from pytz import timezone
import time
from datetime import datetime, timedelta

class Parser(models.AbstractModel):
    _name = 'report.printout_request_payment_npe_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.printout_request_payment_npe_report'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_date': self.get_date,
            'get_70_dr': self.get_70_dr,
            'get_90_grn': self.get_90_grn,
            'get_done_grn_factory': self.get_done_grn_factory,
            'get_grn_done_fot': self.get_grn_done_fot,
            'get_history_request_payment': self.get_history_request_payment,
            'manage_datetime': self.manage_datetime
        })
        return localcontext

    def manage_datetime(self, date):
        date_str = str(date + timedelta(hours=7))
        datetime_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
        new_datetime_str = datetime_obj.strftime('%d-%m-%Y %H:%M:%S')
        return new_datetime_str

    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        return date_user_tz.strftime('%d/%m/%Y')

    def get_70_dr(self, request_payment):
        if request_payment:
            delivery_status_goods = request_payment.status_goods_ids.filtered(lambda x: x.payment_percent == 70)
            if delivery_status_goods:
                dr_name = ', '.join(i.name for i in delivery_status_goods.mapped('delivery_registration_ids'))
                return (dr_name, '{:,}'.format(int(sum(delivery_status_goods.mapped('total_quantity')))),
                        '{:,}'.format(int(sum(delivery_status_goods.mapped('paid_quantity')))), '{:,}'.format(int(sum(delivery_status_goods.mapped('request_quantity')))))
            else:
                return '', 0, 0, 0

    def get_90_grn(self, request_payment):
        if request_payment:
            grn_ready_status_goods = request_payment.status_goods_ids.filtered(lambda x: x.payment_percent == 90)
            if grn_ready_status_goods:
                grn_ready = ', '.join(i.name for i in grn_ready_status_goods.mapped('picking_ids'))
                return (grn_ready, '{:,}'.format(int(sum(grn_ready_status_goods.mapped('total_quantity')))),
                        '{:,}'.format(int(sum(grn_ready_status_goods.mapped('paid_quantity')))), '{:,}'.format(int(sum(grn_ready_status_goods.mapped('request_quantity')))))
            else:
                return '', 0, 0, 0

    def get_done_grn_factory(self, request_payment):
        if request_payment:
            grn_done_factory_status_goods = request_payment.status_goods_ids.filtered(lambda x: x.payment_percent == 100 and x.code == 4)
            if grn_done_factory_status_goods:
                grn_done_factory = ', '.join(i.name for i in grn_done_factory_status_goods.mapped('picking_ids'))
                return (grn_done_factory, '{:,}'.format(int(sum(grn_done_factory_status_goods.mapped('total_quantity')))),
                        '{:,}'.format(int(sum(grn_done_factory_status_goods.mapped('paid_quantity')))), '{:,}'.format(int(sum(grn_done_factory_status_goods.mapped('request_quantity')))))
            else:
                return '', 0, 0, 0

    def get_grn_done_fot(self, request_payment):
        if request_payment:
            grn_done_fot_status_goods = request_payment.status_goods_ids.filtered(lambda x: x.payment_percent == 100 and x.code == 5)
            if grn_done_fot_status_goods:
                grn_done_fot = ', '.join(i.name for i in grn_done_fot_status_goods.mapped('picking_ids'))
                return (grn_done_fot, '{:,}'.format(int(sum(grn_done_fot_status_goods.mapped('total_quantity')))),
                        '{:,}'.format(int(sum(grn_done_fot_status_goods.mapped('paid_quantity')))), '{:,}'.format(int(sum(grn_done_fot_status_goods.mapped('request_quantity')))))
            else:
                return '', 0, 0, 0

    def get_history_request_payment(self, request_payment):
        if request_payment:
            val = []
            for seq, i in enumerate(request_payment.history_quantity_payment):
                val.append(seq+1)
            if val:
                return val
            else:
                return []
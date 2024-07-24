# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from datetime import datetime, date, timedelta
import datetime as dt
DATE_FORMAT = "%Y-%m-%d"
import calendar


class CashBook(models.Model):
    _name = 'v.cash.book'

    categ_name = fields.Char(string="Prod. Group", size=128)
    period = fields.Char(string="Shipment Month", size=128)
    p_contract = fields.Char(string="P Contract", size=128)
    p_qty = fields.Float(string="Contract Quantity")
    grn = fields.Char(string="Picking List", size=128)
    stack = fields.Char(string="Stack", size=128)
    wr = fields.Char(string="Warehouse Receipt", size=128)
    warehouse = fields.Char(string="Warehouse", size=128)
    received = fields.Float(string="Received")
    delivered = fields.Float(string="Delivered")
    balance = fields.Float(string="Balance")
    allocated = fields.Float(string="Allocated")
    weight_in = fields.Float(string="Weight In")
    weight_out = fields.Float(string="Weight Out")

    def add_months(sourcedate, months):
        month = sourcedate.month - 1 + months
        year = int(sourcedate.year + month / 12)
        month = month % 12 + 1
        day = min(sourcedate.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)

    def get_month_year(sdate):
        to_date = sdate.strftime('%b %y')
        return to_date

    a = datetime.now()
    prod_group = fields.Char(string='Prod. Group')
    product = fields.Char(string='Product Code')
    product_id = fields.Many2one('product.product', string='Prod. ID')
    sitting_stock = fields.Float(string='Current Stock', digits=(12, 0))

    npe_received_unfixed = fields.Float(string='NPE Unfixed', digits=(12, 0))
    gross_ls = fields.Float(string='  Gross Long/Short', digits=(12, 0))
    nvp_receivable = fields.Float(string='To be Received', digits=(12, 0))
    unshipped_qty = fields.Float(string='To be Shipped', digits=(12, 0))
    net_ls = fields.Float(string=get_month_year(add_months(a, 0)) + ' L/S', digits=(12, 0))

    nvp_next1_receivable = fields.Float(string=get_month_year(add_months(a, 1)) + ' - TB Receivable', digits=(12, 0))
    sale_next1_unshipped = fields.Float(string=get_month_year(add_months(a, 1)) + ' - TB Shipped', digits=(12, 0))
    next1_net_ls = fields.Float(string=get_month_year(add_months(a, 1)) + ' L/S', digits=(12, 0))

    nvp_next2_receivable = fields.Float(string=get_month_year(add_months(a, 2)) + ' - TB Receivable', digits=(12, 0))
    sale_next2_unshipped = fields.Float(string=get_month_year(add_months(a, 2)) + ' - TB Shipped', digits=(12, 0))
    next2_net_ls = fields.Float(string=get_month_year(add_months(a, 2)) + ' L/S', digits=(12, 0))

    nvp_next3_receivable = fields.Float(string=get_month_year(add_months(a, 3)) + ' - TB Receivable', digits=(12, 0))
    sale_next3_unshipped = fields.Float(string=get_month_year(add_months(a, 3)) + ' - TB Shipped', digits=(12, 0))
    next3_net_ls = fields.Float(string=get_month_year(add_months(a, 3)) + ' L/S', digits=(12, 0))

    nvp_next4_receivable = fields.Float(string=get_month_year(add_months(a, 4)) + ' - TB Receivable', digits=(12, 0))
    sale_next4_unshipped = fields.Float(string=get_month_year(add_months(a, 4)) + ' - TB Shipped', digits=(12, 0))
    next4_net_ls = fields.Float(string=get_month_year(add_months(a, 4)) + ' L/S', digits=(12, 0))

    nvp_next5_receivable = fields.Float(string=get_month_year(add_months(a, 5)) + ' - TB Receivable', digits=(12, 0))
    sale_next5_unshipped = fields.Float(string=get_month_year(add_months(a, 5)) + ' - TB Shipped', digits=(12, 0))
    next5_net_ls = fields.Float(string=get_month_year(add_months(a, 5)) + ' L/S', digits=(12, 0))

    nvp_next6_receivable = fields.Float(string=get_month_year(add_months(a, 6)) + ' - TB Receivable', digits=(12, 0))
    sale_next6_unshipped = fields.Float(string=get_month_year(add_months(a, 6)) + ' - TB Shipped', digits=(12, 0))
    next6_net_ls = fields.Float(string=get_month_year(add_months(a, 6)) + ' L/S', digits=(12, 0))
    faq_derivable = fields.Float(string='FAQ Derivable', digits=(12, 0))

# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re

class ReportSalesShipments(models.Model):
    _name = 'report.v.shipment'
    _description = 'Report Sales Shipments'

    shipment_date_from = fields.Date(string = 'From Shipment date')
    shipment_date_to = fields.Date(string = 'To Shipment date')

    factory_etd_from = fields.Date(string = 'From Factory ETD')
    factory_etd_to = fields.Date(string = 'From Factory ETD')

    shipment_ids = fields.Many2many('v.shipment', 'shipment_filter_rel', 'report_id', 'shipment_id', string='Shipment')

    def load_shipment(self):
        shipment_obj = self.env['v.shipment']
        shipment_ids = []
        for rc in self:
            domain = []
            # if rc.shipment_date_from:
            #     domain.append(('shipment_date', '>', str(rc.shipment_date_from)))

            # if rc.shipment_date_to:
            #     domain.append(('shipment_date', '>', str(rc.shipment_date_to)))

            # if rc.factory_etd_from:
            #     domain.append(('factory_etd', '>', rc.factory_etd_from))

            # if rc.factory_etd_to:
            #     domain.append(('factory_etd', '>', rc.factory_etd_to))

            # if domain:
            #     shipment_ids = shipment_obj.search(domain)
            #     if shipment_ids:
            #         shipment_ids = [idd.id for idd in shipment_ids]

            if rc.shipment_date_from and rc.shipment_date_to:
                print (''' select id, shipment_date from v_shipment where shipment_date between '%s' and '%s' ''') % (str(rc.shipment_date_from),str(rc.shipment_date_to))
                self.env.cr.execute(''' select id, shipment_date from v_shipment where si_number in 
                (select name from shipping_instruction where shipment_date between '%s' and '%s') ''' % (str(rc.shipment_date_from),str(rc.shipment_date_to)))
                kk = self.env.cr.fetchall()
                shipment_ids = [int(idd[0]) for idd in kk]
                # print (shipment_ids,' >>>>>>>>>  ', kk)
            return  {
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'v.shipment',
                'domain': [('id', 'in', shipment_ids)],
                'target': 'current',
                'context': {}
            }


class VCashBook(models.Model):
    _name = 'v.cash.book'
    #_auto = False

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
        year = int(sourcedate.year + month / 12 )
        month = month % 12 + 1
        day = min(sourcedate.day,calendar.monthrange(year,month)[1])
        return dt.date(year,month,day)

    def get_month_year(sdate):
        to_date = sdate.strftime('%b %y')
        return to_date

    a = datetime.now()
    prod_group = fields.Char(string = 'Prod. Group')
    product = fields.Char(string = 'Product Code')
    product_id = fields.Many2one('product.product',string = 'Prod. ID')
    sitting_stock = fields.Float(string = 'Current Stock', digits=(12, 0))

    npe_received_unfixed = fields.Float(string = 'NPE Unfixed', digits=(12, 0))
    gross_ls = fields.Float(string = '  Gross Long/Short', digits=(12, 0))
    nvp_receivable = fields.Float(string = 'To be Received', digits=(12, 0))
    unshipped_qty = fields.Float(string = 'To be Shipped', digits=(12, 0))
    net_ls = fields.Float(string = get_month_year(add_months(a, 0)) + ' L/S', digits=(12, 0))
    
    nvp_next1_receivable = fields.Float(string = get_month_year(add_months(a, 1)) + ' - TB Receivable', digits=(12, 0))
    sale_next1_unshipped = fields.Float(string = get_month_year(add_months(a, 1)) + ' - TB Shipped', digits=(12, 0))
    next1_net_ls = fields.Float(string = get_month_year(add_months(a, 1)) + ' L/S', digits=(12, 0))

    nvp_next2_receivable = fields.Float(string = get_month_year(add_months(a, 2)) + ' - TB Receivable', digits=(12, 0))
    sale_next2_unshipped = fields.Float(string = get_month_year(add_months(a, 2)) + ' - TB Shipped', digits=(12, 0))
    next2_net_ls = fields.Float(string = get_month_year(add_months(a, 2)) + ' L/S', digits=(12, 0))

    nvp_next3_receivable = fields.Float(string = get_month_year(add_months(a, 3)) + ' - TB Receivable', digits=(12, 0))
    sale_next3_unshipped = fields.Float(string = get_month_year(add_months(a, 3)) + ' - TB Shipped', digits=(12, 0))
    next3_net_ls = fields.Float(string = get_month_year(add_months(a, 3)) + ' L/S', digits=(12, 0))

    nvp_next4_receivable = fields.Float(string = get_month_year(add_months(a, 4)) + ' - TB Receivable', digits=(12, 0))
    sale_next4_unshipped = fields.Float(string = get_month_year(add_months(a, 4)) + ' - TB Shipped', digits=(12, 0))
    next4_net_ls = fields.Float(string = get_month_year(add_months(a, 4)) + ' L/S', digits=(12, 0))

    nvp_next5_receivable = fields.Float(string = get_month_year(add_months(a, 5)) + ' - TB Receivable', digits=(12, 0))
    sale_next5_unshipped = fields.Float(string = get_month_year(add_months(a, 5)) + ' - TB Shipped', digits=(12, 0))
    next5_net_ls = fields.Float(string = get_month_year(add_months(a, 5)) + ' L/S', digits=(12, 0))

    nvp_next6_receivable = fields.Float(string = get_month_year(add_months(a, 6)) + ' - TB Receivable', digits=(12, 0))
    sale_next6_unshipped = fields.Float(string = get_month_year(add_months(a, 6)) + ' - TB Shipped', digits=(12, 0))
    next6_net_ls = fields.Float(string = get_month_year(add_months(a, 6)) + ' L/S', digits=(12, 0))
    faq_derivable = fields.Float(string = 'FAQ Derivable', digits=(12, 0))


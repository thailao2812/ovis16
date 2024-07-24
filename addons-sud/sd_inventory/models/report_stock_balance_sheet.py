# -*- coding: utf-8 -*-
from datetime import datetime, date as date_object
from dateutil.relativedelta import relativedelta

# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

from datetime import datetime
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"
DAT= "%Y-%m-%d"

    
class ReportStockBalanceSheet(models.Model):
    _name = "report.stock.balance.sheet"
    _description = "Report Stock Balance Sheet"
    
    
    
    @api.model
    def _get_current_month(self):
        return time.strftime('%m')
    
    name = fields.Char(string="Name", default='Report Stock Balance Sheet')
    
    times = fields.Selection([
        ('dates','Date'),
        ('month', 'Month'),
        ('quarter','Quarter'),
        ('years','Years')], string='Periods Type', required=True, default='dates')
#     period_id= fields.Many2one('account.period', string='Period', 
#                                       default=lambda self: self.env['account.period'].find(dt=time.strftime('%Y-%m-%d'))[0])
    
    date_start = fields.Date(string='Date start', default=time.strftime('%Y-%m-%d'))
    date_end = fields.Date(string='Date end', default=time.strftime('%Y-%m-%d'))
    month = fields.Selection([
        ('01','1'),
        ('02','2'),
        ('03','3'),
        ('04','4'),
        ('05','5'),
        ('06','6'),
        ('07','7'),
        ('08','8'),
        ('09','9'),
        ('10','10'),
        ('11','11'),
        ('12','12')], string='Month', default=_get_current_month)
    quarter = fields.Selection([
        ('1', '1'),
        ('2','2'),
        ('3','3'),
        ('4','4')], string='Quarter', default='1')
    
    period_length = fields.Selection([
        ('day', 'Day'),
        ('week','Week'),
        ('month','Month'),
        ('quarter','Quarter'),
        ('year','Year')], string='Period Length', required=True, default='day')
    
    categ_ids = fields.Many2many('product.category', 'balancesheet_category_rel', 'balanceshe_id', 'categ_id', string='Categories')
    product_ids = fields.Many2many('product.product', 'balancesheet_product_rel', 'balanceshe_id', 'product_id', string='Products')
    warehouse_ids = fields.Many2many('stock.warehouse', 'balancesheet_warehouse_rel', 'balanceshe_id', 'warehouse_id', string='Warehouses', required=False)
    location_ids = fields.Many2many('stock.location', 'balancesheet_location_rel', 'balanceshe_id', 'location_id', string='Locations', domain=[('usage','!=','view')])
    
    report_lines = fields.One2many('report.stock.balance.sheet.line', 'report_id', 'Lines', readonly=True)
    company_id  = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id.id)
    load_again = fields.Boolean(string='Load again', default=False)
    
    # @api.onchange('categ_ids')
    # def _onchange_categ_ids(self):
    #     self.product_ids = False
    #     return
    
    # @api.onchange('warehouse_ids')
    # def _onchange_warehouse_ids(self):
    #     self.location_ids = False
    #     return
    
    def get_period(self, report):
        start_date, end_date = False, False
        if report.times == 'dates':
            start_date = report.date_start
            end_date = report.date_end
        else:
            year = report.fiscalyear_id.name
            
            if report.times =='month':
                date = date_object(int(year), int(report.month), 1)
                
                start_date = year + '-%s-01'%(report.month)
                end_date = date + relativedelta(day=1, months=+1, days=-1)
                end_date = end_date.strftime('%Y-%m-%d')
            if report.times == 'years':
                start_date = report.fiscalyear_id.date_start
                end_date   = report.fiscalyear_id.date_stop
            if report.times == 'quarter':
                if report.quarter == '1':
                    start_date = year + '-01-01'
                    end_date = year + '-03-31'
                elif report.quarter == '2':
                    start_date = year + '-04-01'
                    end_date = year + '-06-30'
                elif report.quarter == '3':
                    start_date = year + '-07-01'
                    end_date = year + '-09-30'
                else:
                    start_date = year + '-10-01'
                    end_date = year + '-12-31'
                            
        return start_date, end_date
    
    def load_details(self, report, date_start, date_end):
        where = 'WHERE 1=1'
        
        #
        # a = date_start
        # b = date_end
        # delta = b - a
        # period_length = delta.days
        period_length = 0
        
        sql ='''
            select '%s'::date - '%s'::date as day
        '''%(date_end, date_start)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            period_length =line['day'] or 0.0
        
        
            
        if len(report.categ_ids):
            categ_ids = [x.id for x in report.categ_ids]
            full_categ_ids = self.env['product.category'].search([('parent_id', 'child_of', categ_ids)])
            full_categ_ids = [x.id for x in full_categ_ids]
            where += ' AND pt.categ_id in (%s)'%(','.join(map(str, full_categ_ids)))
        if len(report.product_ids):
            where += ' AND pp.id in (%s)'%(','.join(map(str, [x.id for x in report.product_ids])))

        if not len(report.location_ids):
            sql ='''  
                Insert Into report_stock_balance_sheet_line(report_id, categ_id, product_id, uom_id, conversion,
                    bg_qty, bg_value, in_qty, in_value, out_qty, out_value, end_qty, end_value, turnover_ratio, turnover, com_currency_id)
                    
                SELECT %(report_id)s, pt.categ_id, pp.id, pu.id, 0.0,
                 
                    sum(start_onhand_qty) start_onhand_qty, sum(start_val) start_val, 
                    
                    sum(nhaptk_qty) nhaptk_qty, sum(nhaptk_val) nhaptk_val,
                    sum(xuattk_qty) xuattk_qty, sum(xuattk_val) xuattk_val,    
                    
                    sum(end_onhand_qty) end_onhand_qty,sum(end_val) end_val,
                    
                    case when sum(end_onhand_qty) > 0
                    then sum(xuattk_qty) / sum(end_onhand_qty)
                    else 0.0 end turnover_ratio,
                    
                    case when sum(end_onhand_qty) > 0 and sum(xuattk_qty) > 0
                    then %(period_length)s / (sum(xuattk_qty) / sum(end_onhand_qty))
                    else 0.0 end turnover,
                    
                    %(com_currency_id)s
                    
                    From
                        (SELECT
                            stm.product_id,stm.product_uom_id, 
                            
                            case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',sp.date_done::timestamp)) < '%(start_date)s'
                            then stm.qty_done
                            else
                            case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',sp.date_done::timestamp)) < '%(start_date)s'
                            then -1*stm.qty_done 
                            else 0.0 end
                            end start_onhand_qty,
                            
                            case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',sp.date_done::timestamp)) < '%(start_date)s'
                            then (stm.price_unit * stm.qty_done)
                            else
                            case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',sp.date_done::timestamp)) < '%(start_date)s'
                            then -1*(stm.price_unit * stm.qty_done)
                            else 0.0 end
                            end start_val,
                            
                            case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',sp.date_done::timestamp)) between '%(start_date)s' and '%(end_date)s'
                            then stm.qty_done
                            else 0.0 end nhaptk_qty,
                            
                            case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',sp.date_done::timestamp)) between '%(start_date)s' and '%(end_date)s'
                            then 1*stm.qty_done 
                            else 0.0
                            end xuattk_qty,
                    
                            case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',sp.date_done::timestamp)) between '%(start_date)s' and '%(end_date)s'
                            then (stm.price_unit * stm.qty_done)
                            else 0.0 end nhaptk_val,
                            
                            case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',sp.date_done::timestamp)) between '%(start_date)s' and '%(end_date)s'
                            then 1*(stm.price_unit * stm.qty_done)
                            else 0.0
                            end xuattk_val,        
                             
                            case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',sp.date_done::timestamp)) <= '%(end_date)s'
                            then stm.qty_done
                            else
                            case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',sp.date_done::timestamp)) <= '%(end_date)s'
                            then -1*stm.qty_done 
                            else 0.0 end
                            end end_onhand_qty,
                            
                            case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',sp.date_done::timestamp)) <= '%(end_date)s'
                            then (stm.price_unit * stm.qty_done)
                            else
                            case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',sp.date_done::timestamp)) <= '%(end_date)s'
                            then -1*(stm.price_unit * stm.qty_done)
                            else 0.0 end
                            end end_val            
                        FROM stock_move_line stm 
                            join stock_location loc1 on stm.location_id=loc1.id
                            join stock_location loc2 on stm.location_dest_id=loc2.id
                            join stock_picking sp on stm.picking_id = sp.id
                            join stock_picking_type spt on sp.picking_type_id = spt.id
                        WHERE 
                            sp.state= 'done'
                            and spt.code in ('material_in','material_out'))foo
                    
                    left join product_product pp on foo.product_id = pp.id
                        left join product_template pt on pp.product_tmpl_id = pt.id
                        left join uom_uom pu on pt.uom_id = pu.id
                    
                    %(where)s
                    
                    group by pt.categ_id, pp.id, pu.id
                    having (sum(end_onhand_qty) !=0 or sum(start_onhand_qty) !=0 or sum(nhaptk_qty) !=0 or sum(xuattk_qty) !=0)
                    order by pp.default_code
            '''%({
              'start_date': date_start,
              'end_date': date_end,
              'report_id':report.id,
              'com_currency_id':report.company_id.currency_id.id,
              'period_length': period_length,
              'where': where,
              })
        else:
            sql = '''
                   Insert Into report_stock_balance_sheet_line(report_id, categ_id, product_id, uom_id, conversion,
                       bg_qty, bg_value, in_qty, in_value, out_qty, out_value, end_qty, end_value, turnover_ratio, turnover, com_currency_id)

                   SELECT %(report_id)s, pt.categ_id, pp.id, pu.id, 0.0,

                       sum(start_onhand_qty) start_onhand_qty, 
                       sum(start_val) start_val, 

                       sum(nhaptk_qty) nhaptk_qty, 
                       sum(nhaptk_val) nhaptk_val,
                       sum(xuattk_qty) xuattk_qty, 
                       sum(xuattk_val)  xuattk_val,    
                       sum(end_onhand_qty) end_onhand_qty,
                       sum(end_val) end_val,

                       case when sum(end_onhand_qty) > 0
                       then sum(xuattk_qty) / sum(end_onhand_qty)
                       else 0.0 end turnover_ratio,

                       case when sum(end_onhand_qty) > 0 and sum(xuattk_qty) > 0
                       then %(period_length)s / (sum(xuattk_qty) / sum(end_onhand_qty))
                       else 0.0 end turnover,

                       %(com_currency_id)s

                       From
                           (SELECT  
                               stm.product_id,stm.product_uom_id,

                               case when loc1.id not in (%(location_ids)s) and loc2.id in (%(location_ids)s) and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                               then stm.qty_done
                               else
                               case when loc1.id in (%(location_ids)s) and loc2.id not in (%(location_ids)s) and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                               then -1*stm.qty_done 
                               else 0.0 end
                               end start_onhand_qty,

                               case when loc1.id not in (%(location_ids)s) and loc2.id in (%(location_ids)s) and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                               then (stm.price_unit * stm.qty_done)
                               else
                               case when loc1.id in (%(location_ids)s) and loc2.id not in (%(location_ids)s) and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                               then -1*(stm.price_unit * stm.qty_done)
                               else 0.0 end
                               end start_val,

                               case when loc1.id not in (%(location_ids)s) and loc2.id in (%(location_ids)s) and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                               then stm.qty_done
                               else 0.0 end nhaptk_qty,

                               case when loc1.id in (%(location_ids)s) and loc2.id not in (%(location_ids)s) and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                               then 1*stm.qty_done 
                               else 0.0
                               end xuattk_qty,

                               case when loc1.id not in (%(location_ids)s) and loc2.id in (%(location_ids)s) and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                               then (stm.price_unit * stm.qty_done)
                               else 0.0 end nhaptk_val,

                               case when loc1.id in (%(location_ids)s) and loc2.id not in (%(location_ids)s) and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                               then 1*(stm.price_unit * stm.qty_done)
                               else 0.0
                               end xuattk_val,        

                               case when loc1.id not in (%(location_ids)s) and loc2.id in (%(location_ids)s) and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                               then stm.qty_done
                               else
                               case when loc1.id in (%(location_ids)s) and loc2.id not in (%(location_ids)s) and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                               then -1*stm.qty_done 
                               else 0.0 end
                               end end_onhand_qty,

                               case when loc1.id not in (%(location_ids)s) and loc2.id in (%(location_ids)s) and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                               then (stm.price_unit * stm.qty_done)
                               else
                               case when loc1.id in (%(location_ids)s) and loc2.id not in (%(location_ids)s) and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                               then -1*(stm.price_unit * stm.qty_done)
                               else 0.0 end
                               end end_val            
                           FROM stock_move_line stm 
                               join stock_location loc1 on stm.location_id=loc1.id
                               join stock_location loc2 on stm.location_dest_id=loc2.id

                           WHERE stm.state= 'done')foo

                       left join product_product pp on foo.product_id = pp.id
                           left join product_template pt on pp.product_tmpl_id = pt.id
                           left join uom_uom pu on pt.uom_id = pu.id                    
                       %(where)s                    
                       group by pt.categ_id, pp.id, pu.id
                       having (sum(end_onhand_qty) !=0 or sum(start_onhand_qty) !=0 or sum(nhaptk_qty) !=0 or sum(xuattk_qty) !=0)
                       order by pp.id
               ''' % ({
                'start_date': date_start,
                'end_date': date_end,
                'location_ids': ','.join(map(str, [x.id for x in report.location_ids])),
                'report_id': report.id,
                'period_length': period_length,
                'com_currency_id': report.company_id.currency_id.id,
                'where': where,
            })
        self.env.cr.execute(sql)
        return True
    
    def load_data(self):
        for report in self:
            self.env.cr.execute('''
                DELETE FROM report_stock_balance_sheet_line where report_id = %s
                '''%(report.id))
                
            date_start, date_end = self.get_period(report)
            report.date_start = date_start
            report.date_end = date_end
            self.load_details(report, date_start, date_end)
        
        return True
    
    
class ReportStockBalanceSheetLine(models.Model):
    _name = "report.stock.balance.sheet.line"
    
    report_id = fields.Many2one('report.stock.balance.sheet')
    
    categ_id = fields.Many2one('product.category', string="Category")
    product_id = fields.Many2one('product.product', string="Product")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    conversion = fields.Float(string="Conversion", digits=(16,4))
    
    #bg_qty = fields.Float(string='Open Qty', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    bg_qty = fields.Float(string='Open Qty', digits=(16,0), readonly=True)
    bg_value = fields.Float(string='Open Value', readonly=True, )
    
    # in_qty = fields.Float(string='In Qty', readonly=True)
    in_qty = fields.Float(string='In Qty', digits=(16,0), readonly=True)
    out_qty = fields.Float(string='Out Qty', digits=(16,0), readonly=True)
    in_value = fields.Float(string='In Value', readonly=True, )
    #out_qty = fields.Float(string='Out Qty', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    out_value = fields.Float(string='Out Value', readonly=True, )
    
    end_qty = fields.Float(string='Bal Qty', digits=(16,0), readonly=True)
    #end_qty = fields.Float(string='Bal Qty', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    end_value = fields.Float(string='Balance Value', readonly=True, )
    
    turnover_ratio = fields.Float(string='Turnover Ratio', digits=(16,2), readonly=True)
    turnover = fields.Float(string='Turnover', digits=(16,2), readonly=True)
    
    com_currency_id = fields.Many2one('res.currency', string="Company Currency")
#     second_currency_id = fields.Many2one(compute="_compute_currency", relation='res.currency', string="Second Currency", store= True)

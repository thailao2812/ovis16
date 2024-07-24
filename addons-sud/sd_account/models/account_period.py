# -*- coding: utf-8 -*-
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"

class account_fiscalyear(models.Model):
    _name = "account.fiscalyear"
    _description = "Fiscal Year"
    _order = "date_stop DESC"
    
    name = fields.Char('Fiscal Year', required=True, readonly=True, states={'draft': [('readonly', False)]})
    code = fields.Char('Code', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date('Start Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date_stop = fields.Date('End Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
    period_ids = fields.One2many('account.period', 'fiscalyear_id', 'Periods', copy=False, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft','Open'), ('done','Closed')], 'Status', readonly=True, copy=False, default='draft')
    company_id  = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    
    #THANH: 2 fields for closing va opening balance
    next_fiscalyear_id = fields.Many2one('account.fiscalyear', 'Next Fiscal Year', states={'done':[('readonly',True)]},
                                         domain="[('state','=','draft'), ('date_start','>',date_stop)]")
    
    closing_entry_ids = fields.Many2many('account.move', 'account_fiscalyear_closing_entry_rel', 'fiscalyear_id', 'move_id', 
                                         string='Closing Entries', readonly=True)
    closing_balances = fields.One2many('account.fiscalyear.closing', 'fiscalyear_id', 'Closing Balances', copy=False, readonly=True)
    
    opening_entry_ids = fields.Many2many('account.move', 'account_fiscalyear_opening_entry_rel', 'fiscalyear_id', 'move_id', 
                                         string='Opening Entries',  store=False, readonly=True)
    
#     opening_balances = fields.Many2many('account.move.line', string='Opening Balances', compute='_load_opening', store=False)
    
    def create_period(self):
        interval = hasattr(self.env, 'interval') and self.env.interval or 1
        period_obj = self.env['account.period']
        for fy in self:
            # ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            ds = fy.date_start
            period_obj.create({
                    'name':  "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                    'code': '00/' + fy.name,
                    'date_start': ds,
                    'date_stop': ds,
                    'special': True,
                    'fiscalyear_id': fy.id,
                })
            
            dem = 0
            while ds < fy.date_stop:
                de = ds + relativedelta(months=interval, days=-1)

                if de > fy.date_stop:
                    de = fy.date_stop
                
                dem += 1
                code = '%%0%sd' % 2 % dem
                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': code + '/' + fy.name,
                    'date_start': ds,
                    'date_stop': de,
                    'fiscalyear_id': fy.id,
                })
                ds = ds + relativedelta(months=interval)
        return True
    

class account_period(models.Model):
    _name = "account.period"
    _description = "Account period"
    _order = "fiscalyear_id, date_start, code"
    
    
    name = fields.Char('Period Name', required=True)
    code = fields.Char('Code')
    special = fields.Boolean('Opening/Closing Period',help="These periods can overlap.")
    date_start = fields.Date('Start of Period', required=True, states={'done':[('readonly',True)]})
    date_stop = fields.Date('End of Period', required=True, states={'done':[('readonly',True)]})
    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal Year', required=True, states={'done':[('readonly',True)]})
    state = fields.Selection([('draft','Open'), ('done','Closed')], 'Status', readonly=True, copy=False, default = 'draft',
                              help='When monthly periods are created. The status is \'Draft\'. At the end of monthly period it is in \'Done\' status.')
    company_id = fields.Many2one('res.company', related='fiscalyear_id.company_id', string='Company', store=True, readonly=True)


class account_fiscalyear_closing(models.Model):
    _name = "account.fiscalyear.closing"
    _order = "acc_code,acc_level,id"
  
    fiscalyear_id = fields.Many2one('account.fiscalyear')
    
    acc_level = fields.Integer(string="Acc Level")
    acc_type = fields.Char(string="Acc Type")#THANH: store it view account
    acc_code = fields.Char(string="Acc Code")
    acc_name = fields.Char(string="Acc Name")
    account_id = fields.Many2one('account.account', string="Account")
    partner_id = fields.Many2one('res.partner', string="Partner")
    internal_type = fields.Selection([
            ('view', 'View'),
            ('public', 'Public'),
            ('internal', 'Internal'),
        ], string='Internal Type', default='public')
    
    begin_dr = fields.Monetary(string="Begin Dr", currency_field='com_currency_id')
    begin_cr = fields.Monetary(string="Begin Cr", currency_field='com_currency_id')
    period_dr = fields.Monetary(string="Period Dr", currency_field='com_currency_id')
    period_cr = fields.Monetary(string="Period Cr", currency_field='com_currency_id')
    end_dr = fields.Monetary(string="End Dr", currency_field='com_currency_id')
    end_cr = fields.Monetary(string="End Cr", currency_field='com_currency_id')
    com_currency_id = fields.Many2one('res.currency', string="Currency", readonly=True)
    
    begin_dr_2rd = fields.Monetary(string="Begin Dr", currency_field='second_currency_id')
    begin_cr_2rd = fields.Monetary(string="Begin Cr", currency_field='second_currency_id')
    period_dr_2rd = fields.Monetary(string="Period Dr", currency_field='second_currency_id')
    period_cr_2rd = fields.Monetary(string="Period Cr", currency_field='second_currency_id')
    end_dr_2rd = fields.Monetary(string="End Dr", currency_field='second_currency_id')
    end_cr_2rd = fields.Monetary(string="End Cr", currency_field='second_currency_id')
    second_currency_id = fields.Many2one('res.currency', string="2nd Currency", readonly=True)
    
    
        

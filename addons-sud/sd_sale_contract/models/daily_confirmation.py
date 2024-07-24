# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import xlrd
import base64
from xlrd import open_workbook


class DailyConfirmation(models.Model):
    _name = 'daily.confirmation'
    _order = 'id desc'
    
    name = fields.Char(string="Name", default=lambda self: _('New'))
    date_create = fields.Datetime('Create Date',default=fields.Datetime.now)
    user_id = fields.Many2one('res.users',string="User Create",default=lambda self: self.env.user)

    liffe = fields.Float(string='LIFFE')
    diff = fields.Float(string='DIFF')
    cost_price = fields.Float(string='Cost Price')
    exchange_rate = fields.Float(string='Exchange Rate', digits=(12,0))
    state = fields.Selection([('draft','Draft'),('done','Done')],string="State",default='draft')
    failure = fields.Integer('Error(s)', default=0, copy=False)
    warning_mess = fields.Text('Message', copy=False)
    file = fields.Binary('File', help='Choose file Excel', copy=False, readonly=True, states={'draft':[('readonly',False)],'sent':[('readonly',False)]})
    file_name =  fields.Char('Filename', size=100, readonly=True, copy=False, default='Daily Confirmation.xls')
    daily_confirmation_ids = fields.One2many('daily.confirmation.line','daily_id', string='Daily Confirmation Detail')

    @api.model
    def create(self,vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('daily.confirmation') or '/'
        return super(DailyConfirmation, self).create(vals)

    def print_template(self):
        return {'type': 'ir.actions.report.xml', 'report_name': 'template_import_data'}

    def button_warning_mess(self):
        if not self.warning_mess:
            return
        raise UserError(_(self.warning_mess))

    def action_read_file(self):
        purchase_contract = self.env['purchase.contract']
        success = failure = 0
        daily_comfirmation_list = []
        warning = False
        for this in self:
            try:
                recordlist = base64.decodestring(this.file)
                excel = xlrd.open_workbook(file_contents = recordlist)
                sh = excel.sheet_by_index(0)
            except Exception:
                raise UserError(('No define file daily confirmation. Please upload file!'))
            if sh:
                #Kiet Import thêm, không bị xóa history 
                # self.env.cr.execute('''
                # BEGIN;
                #     DELETE FROM daily_confirmation_line where daily_id = %s;
                # COMMIT;'''%(this.id))
                messenger = ''
                for row in range(sh.nrows):
                    error = False
                    mess = ''
                    if row > 0:
                        im_name = sh.cell(row,0).value or False
                        im_p = sh.cell(row,1).value or False

                        im_liffe = sh.cell(row,2).value or False
                        im_diff = sh.cell(row,3).value or False

                        im_exchange = sh.cell(row,4).value or 0.0

                        im_qty = sh.cell(row,5).value or 0.0
                        
                        im_diff_price = sh.cell(row,6).value or False
                        contract_id = False
                        p_contract = ''
                        diff_price = liffe = exchange_rate = diff = qty = 0.0

                        if im_name:
                            im_name = im_name.lstrip()
                            im_name = im_name.rstrip()
                            print (im_name)
                            exist_id = purchase_contract.search([('name','=',im_name)],limit=1)
                            if exist_id:
                                contract_id = exist_id.id
                            else:
                                error = True
                                mess += _(' Purchase Contract number does not exist.')
                        else:
                            error = True
                            mess += _(' Purchase Contract number is not null.')
                        
                        if im_p:
                            im_p = im_p.lstrip()
                            im_p = im_p.rstrip()
                            p_contract = im_p
                        
                        if im_liffe:
                            if isinstance(im_liffe, float):
                                liffe = im_liffe
                            else:
                                error = True
                                mess = mess + _(' LIFFE must be data kind of numeric.')
                        
                        if im_diff:
                            if isinstance(im_diff, float):
                                diff = im_diff
                            else:
                                error = True
                                mess = mess + _(' DIFF must be data kind of numeric.')
                        
                        if im_diff_price:
                            if isinstance(im_diff_price, float):
                                diff_price = im_diff_price
                            else:
                                error = True
                                mess = mess + _(' DIFF must be data kind of numeric.')

                        if im_exchange:
                            if isinstance(im_exchange, float):
                                exchange_rate = im_exchange
                            else:
                                error = True
                                mess = mess + _(' DIFF must be data kind of numeric.')

                        if not im_qty or im_qty == 0.0:
                            if contract_id:
                                qty = purchase_contract.search([('id','=',contract_id)],limit=1).total_qty
                        else:
                            if isinstance(im_qty, float):
                                qty = im_qty
                            else:
                                error = True
                                mess = mess + _(' Quantity must be data kind of numeric.')

                        if not error:
                            success += 1 
                            daily_comfirmation_list.append((0,0,{
                                    'contract_id': contract_id,
                                    'p_contract': p_contract,
                                    'liffe': liffe,
                                    'diff': diff,
                                    'exchange_rate': exchange_rate,
                                    'qty': qty,
                                    'daily_id': this.id,
                                    'diff_price':diff_price,
                                    }))
                        else:
                            failure += 1
                            line = row + 1
                            messenger += _('\n - Line ') + _(str(line)) + ':' + _(mess) or ''
            
                
            this.failure = 0
            if failure > 0:
                this.failure = failure or  0
                warning = _('Errors arising at: ' + messenger)
                this.warning_mess = warning or False
            if daily_comfirmation_list != []:
                this.daily_confirmation_ids = daily_comfirmation_list
            else:
                this.daily_confirmation_ids = False
        return True

    def confirm_import(self):
        self.action_read_file()
#         self._auto_load_daily_confirmation()
        if self.daily_confirmation_ids:
            self.update({'state':'done'})
        return
    
    def _auto_load_daily_confirmation(self):
        sql= ''' 
            SELECT a.analysis_id
            FROM production_analysis_line_input_value a
                JOIN purchase_contract pur ON a.source_contract_id = pur.id
                JOIN npe_nvp_relation npe ON npe.npe_contract_id = pur.id
            WHERE (a.contract_id IN (%(contract_ids)s) OR npe.contract_id IN (%(contract_ids)s))
                AND a.analysis_id IS NOT NULL
            GROUP BY a.analysis_id
            '''%({"contract_ids":','.join(map(str, [x.contract_id.id for x in self.daily_confirmation_ids]))})
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            analysis_id = self.env['production.analysis'].browse(line['analysis_id'])
            analysis_id.action_load_daily_confirmation()
            if analysis_id.liffe == 0.0 and analysis_id.diff == 0.0 and analysis_id.exchange_rate == 0.0 and analysis_id.cost_price == 0.0:
                analysis_id.load_liffe_diff()
                analysis_id.action_allocation_price()
                analysis_id.update_allocation_price()
                
    def action_cancel(self):
        self.ensure_one()
        if self.daily_confirmation_ids:
            self.daily_confirmation_ids = [(5,)]
            self.update({'state': 'draft'})
        return

class DailyConfirmationLine(models.Model):
    _name ='daily.confirmation.line'

    daily_id = fields.Many2one('daily.confirmation',string="Daily Confirmation", ondelete='cascade')
    contract_id = fields.Many2one('purchase.contract', string='Contract No.')
    p_contract = fields.Char(string='P Contract')
    liffe = fields.Float(string='LIFFE')
    diff = fields.Float(string='DIFF')
    diff_price = fields.Float(string='Diff to supplier')
    exchange_rate = fields.Float(string='Exchange Rate')
    qty = fields.Float(string='Quantity')

    
    
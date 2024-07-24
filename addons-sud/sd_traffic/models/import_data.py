# -*- coding: utf-8 -*-
from odoo import tools
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64, xlrd
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class ImportData(models.Model):
    _name = 'import.data'

    name = fields.Char(string="Name", default=lambda self: _('New'))

    import_type = fields.Selection(selection=[('p.contract','P Contract'),('s.contract','S Contract')],string="Import Type", default='p.contract',readonly=True, 
                           states={'draft':[('readonly',False)],})
    date_import = fields.Datetime('Import Date',default=fields.Datetime.now)
    user_import = fields.Many2one('res.users',string="User Import",default=lambda self: self.env.user)

    pcontract_ids = fields.Many2many('s.contract','p_contract_import_data_rel','import_id','contract_id',string="Contract")
    pcontract_import_ids = fields.One2many('import.data.line','import_id', string="Contract")
    scontract_import_ids = fields.One2many('import.data.line','s_import_id', string="Contract")

    state = fields.Selection([('draft','Draft'),('done','Done')],string="State",default='draft')

    file = fields.Binary('File', help='Choose file Excel', copy=False, readonly=True, states={'draft':[('readonly',False)],'sent':[('readonly',False)]})
    file_name =  fields.Char('Filename', size=100, readonly=True, copy=False, default='Import Template.xls')
    
    failure = fields.Integer('Error(s)', default=0, copy=False)
    warning_mess = fields.Text('Message', copy=False)

    line_pcontract_error_ids = fields.One2many('error.import','import_id',string='Line Error', readonly=True, states={'draft':[('readonly',False)]}, copy=False)

    @api.model
    def create(self,vals):
        if vals.get('name', 'New') == 'New':
#             if vals.get('import_type') == 'p.contract':
            vals['name'] = self.env['ir.sequence'].next_by_code('import.data.p') or '/'
        return super(ImportData, self).create(vals)


    def unlink(self):
        for i in self:
            if i.state != 'draft':
                raise UserError(_('You can only delete draft!'))
        return super(ImportData, self).unlink()

    def button_warning_mess(self):
        if not self.warning_mess:
            return
        raise UserError(_(self.warning_mess))
    
    def update_p_a(self):
        for this in self:
            try:
                recordlist = base64.decodestring(this.file)
                excel = xlrd.open_workbook(file_contents = recordlist)
                sh = excel.sheet_by_index(0)
            except Exception as e:
                raise UserError(('Please select File'))
            if sh:
                for row in range(sh.nrows):
                    row_values = sh.row_values(row)
                    hd = row_values[1]
                    p = row_values[0]
                    hd_obj = self.env['purchase.contract'].search([('name', '=' ,hd)])
                    if hd_obj:
                        if not hd_obj.contract_p_id:
                            p_con = self.env['s.contract'].search([('name', '=' ,p)])
                            if not p_con:
                                continue
                            hd_obj.contract_p_id = p_con.id

    def import_p_contract(self):
        self.update_p_a()
        return
        contract = self.env['s.contract']
        success = failure = 0
        contract_line = []
        error_line = []
        warning = False
        for this in self:
            try:
                recordlist = base64.decodestring(this.file)
                excel = xlrd.open_workbook(file_contents = recordlist)
                sh = excel.sheet_by_index(0)
            except Exception as e:
                raise UserError(('Please select File'))
            if sh:
                self.env.cr.execute('''
                BEGIN;
                    DELETE FROM import_data_line where import_id = %s;
                    DELETE FROM error_import WHERE import_id = %s;
                COMMIT;'''%(this.id,this.id))
                messenger = ''
                for row in range(sh.nrows):
                    error = False
                    mess = ''
                    if row > 0:
                        im_name = sh.cell(row,0).value or False
                        im_date = sh.cell(row,1).value or False
                        im_date_catalog = sh.cell(row,2).value or False
                        im_qty = sh.cell(row,3).value or 0.0
                        im_market = sh.cell(row,4).value or 0.0
                        im_diff = sh.cell(row,5).value or 0.0
                        name = date = date_catalog = False
                        qty = market = diff = 0.0

                        if im_name:
                            if isinstance(im_name, unicode):
                                im_name = im_name.lstrip()
                                im_name = im_name.rstrip()
                            exist_id = contract.search([('name','=',im_name)],limit=1)
                            if not exist_id:
                                name = im_name
                            else:
                                error = True
                                mess += _(' P-Contract number existed.')
                        else:
                            error = True
                            mess += _(' P-Contract number is not null.')

                        if im_date:
                            if isinstance(im_date, unicode):
                                im_date = im_date.lstrip()
                                im_date = im_date.rstrip()
                            date = datetime.strptime(im_date, tools.DEFAULT_SERVER_DATE_FORMAT).date()
                        else:
                            date = datetime.now().date()
                        if im_date_catalog:
                            if isinstance(im_date_catalog, unicode):
                                im_date_catalog = im_date_catalog.lstrip()
                                im_date_catalog = im_date_catalog.rstrip()
                            date_catalog = datetime.strptime(im_date_catalog, tools.DEFAULT_SERVER_DATE_FORMAT).date()
                        else:
                            date_catalog = datetime.now().date()

                        if not im_qty:
                            qty = 1
                        else:
                            if isinstance(im_qty, float):
                                if im_qty < 0:
                                    error = True
                                    mess = mess + _(' Quantity must be greater than 0.')
                                else:
                                    qty = im_qty
                            else:
                                error = True
                                mess = mess + _(' Quantity must be data kind of numeric.')
                        
                        if im_market:
                            if isinstance(im_market, float):
                                market = im_market
                            else:
                                error = True
                                mess = mess + _(' Market price must be data kind of numeric.')
                        
                        if im_diff:
                            if isinstance(im_diff, float):
                                diff = im_diff
                            else:
                                error = True
                                mess = mess + _(' Diff price must be data kind of numeric.')

                        if not error:
                            success += 1 
                            contract_line.append((0,0,{
                                    'name': name,
                                    'date': date,
                                    'date_catalog': date_catalog,
                                    'product_qty': qty,
                                    'market_price':market,
                                    'p_contract_diff': diff,
                                    'partner_id': self.env['res.partner'].search([('name','=','NEDCOFFEE BV')]).id,
                                    'product_id': self.env['product.product'].search([('default_code','=','G13-ST1')]).id,
                                    'product_uom': self.env['product.uom'].search([('name','=','Tấn')]).id,
                                    'import_id': this.id
                                    }))
                        else:
                            error_line.append((0,0,{
                                    'name': im_name,
                                    'date': im_date,
                                    'date_catalog': im_date_catalog,
                                    'product_qty': im_qty,
                                    'market_price':im_market,
                                    'p_contract_diff': im_diff,
                                    'notes': mess}))
                            failure += 1
                            line = row + 1
                            messenger += _('\n - Line ') + _(str(line)) + ':' + _(mess) or ''
            if contract_line != []:
                this.pcontract_import_ids = contract_line
            else:
                this.pcontract_import_ids = False    
            if error_line != []:
                this.line_pcontract_error_ids = error_line
            else:
                this.line_pcontract_error_ids = False
                
            this.failure = 0
            if failure > 0:
                this.failure = failure or  0
                warning = _('Errors arising at: ' + messenger)
            this.warning_mess = warning or False
        return True
    
    def slip_name(self,name):
        # if isinstance(name, unicode):
        name = name.lstrip()
        name = name.rstrip()
        return name
    
    def get_date(self,date,excel):
        if date:
            # if isinstance(date, unicode):
            date = date.strip()

            if isinstance(date, float):
                datetuple = xlrd.xldate_as_tuple(
                    date, excel.datemode)
                date = '{}-{}-{}'.format(
                    datetuple[0], datetuple[1], datetuple[2])

            # if isinstance(date, unicode):
            date = date.strip()
            Check_date = True
            try:
                date = fields.Date.from_string(date)
            except ValueError:
                Check_date = False
                pass
            if not Check_date:
                dtFormat = ('%Y/%m/%d','%Y-%m-%d','%Y\%m\%d','%d/%m/%Y','%d-%m-%Y','%d\%m\%Y','%m/%d/%Y','%m-%d-%Y','%m\%d\%Y','%d-%m-%Y','%d-%m-%y')
                for i in dtFormat:
                    try:
                        date = datetime.strptime(date, i).strftime(DEFAULT_SERVER_DATE_FORMAT)
                        break
                    except ValueError:
                        pass
                
                
            if not date:
                raise
            return date
    
    
#     def create_delivery_place(self):
    def import_s_contract(self):
        contract = self.env['s.contract']
        success = failure = 0
        contract_line = []
        error_line = []
        warning = False
        for this in self:
            try:
                recordlist = base64.decodestring(this.file)
                excel = xlrd.open_workbook(file_contents = recordlist)
                sh = excel.sheet_by_index(0)
            except Exception as e:
                raise UserError(('Please select File'))
            messenger = ''
            if sh:
                self.env.cr.execute('''
                BEGIN;
                    DELETE FROM import_data_line where s_import_id = %s;
                    DELETE FROM error_import WHERE import_id = %s;
                COMMIT;'''%(this.id,this.id))

                for row in range(sh.nrows):
                    error = False
                    mess = ''
                    if row > 1:
                        
                        allocation_status = sh.cell(row,0).value or False
                        allocation_date = sh.cell(row,1).value or False
                        entity_date = sh.cell(row,2).value or False
                        origin =  sh.cell(row,3).value or False
                        shipment_month = sh.cell(row,4).value or False
                        s_contract = sh.cell(row,5).value or False
                        client_ref = sh.cell(row,6).value or False
                        partner_id = sh.cell(row,7).value or False
                        quality = sh.cell(row,8).value or False
                        product_id = sh.cell(row,10).value or False
                        specifications = sh.cell(row,10).value or False
                        ned_packing = sh.cell(row,12).value or False
                        pss_type = sh.cell(row,13).value or False
                        delivery_term = sh.cell(row,14).value or False
                        start_of_Ship_period = sh.cell(row,15).value or False
                        end_of_ship_period = sh.cell(row,16).value or False
                        delivery_type = sh.cell(row,17).value or False
#                         del_period = sh.cell(row,14).value or False
                        pic = sh.cell(row,21).value or False
                        port_of_discharge = sh.cell(row,22).value or False
                        port_of_loading = sh.cell(row,23).value or False
                        precalculated_freight_cost = sh.cell(row,21).value or False
                        
                        print(row,s_contract,allocation_date,shipment_month,start_of_Ship_period,end_of_ship_period,delivery_type)
                        
                        
                        if product_id:
                            exit = False
                            product_id = self.slip_name(product_id)
                            exit = product_id
                            product_id = self.env['mapping.product'].search([('quality','=',product_id)],limit =1)
                            if product_id:
                                product_id= product_id.product_id
                            else:
                                error = True
                                mess += _(' Product not existed: %s'%(exit))
                        if delivery_type:
                            if isinstance(delivery_type, float):
                                delivery_type = int(delivery_type)
                                delivery_type = str(delivery_type)
                            if delivery_type not in ('10','50'):
                                delivery_type = '50'
                        
                        
                        exisit = False
                        if s_contract:
                            if isinstance(s_contract, float):
                                s_contract = int(s_contract)
                                s_contract = str(s_contract)
                            s_contract = self.slip_name(s_contract)
                            exisit = self.env['s.contract'].search([('name','=',s_contract)]) or False
                        if exisit:
                            error = True
                            mess += _('S-Contract number existed: %s '%(s_contract))
                            
                        packing = False
                        if ned_packing:
                            ned_packing = self.slip_name(ned_packing)
                            ned_packing = self.env['ned.packing'].search([('name','=',ned_packing)])
                            if ned_packing:
                                packing = ned_packing
                            
                        if shipment_month:
                            shipment_month =self.get_date(shipment_month,excel)
                        
                        if entity_date:
                            entity_date = self.get_date(entity_date,excel)

                        if allocation_date:
                            allocation_date =self.get_date(allocation_date,excel)
                        
                        if start_of_Ship_period:
                            start_of_Ship_period =self.get_date(start_of_Ship_period,excel)
                        
                        if end_of_ship_period:
                            end_of_ship_period =self.get_date(end_of_ship_period,excel)

                        if not quality:
                            quality = 1
                        else:
                            if isinstance(quality, float):
                                if quality < 0:
                                    error = True
                                    mess = mess + _(' Quantity must be greater than 0.')
                                else:
                                    quality = quality
                            else:
                                error = True
                                mess = mess + _(' Quantity must be data kind of numeric.')
                        
                        if partner_id:
                            partner_id = self.slip_name(partner_id)
                            partner_id = self.env['mapping.partner'].search([('client_name','=',partner_id)],limit =1)
                            if partner_id:
                                partner_id = partner_id.patner_id
                            else:
                                error = True
                                mess += _(' Customer number existed.')
                        
                        if port_of_loading:
                            port_of_loading = self.slip_name(port_of_loading)
                            port_of_loading = self.env['delivery.place'].search(['|',('name','=',port_of_loading),('code','=',port_of_loading)],limit =1)
                            if port_of_loading:
                                port_of_loading = port_of_loading
                        
                        if port_of_discharge:
                            port_of_discharge = self.slip_name(port_of_discharge)
                            port_of_discharge = self.env['delivery.place'].search(['|',('name','=',port_of_discharge),('code','=',port_of_discharge)],limit =1)
                            if port_of_discharge:
                                port_of_discharge = port_of_discharge
                        
                        if pic:
                            pic = self.slip_name(pic)
                            employee = self.env['hr.employee'].search(['|',('name','=',pic),('code','=',pic)],limit =1)
                            if employee:
                                pic = employee
                        if pss_type not in ('SAS','SAP','PSS','PSS+OTS','No'):
                            pss_type= False
                            
                        if not error:
                            success += 1 
                            contract_line.append((0,0,{
                                    'allocation_date':allocation_date,
                                    'allocation_status':allocation_status,
                                    'name': s_contract,
                                    'date': entity_date,
                                    'shipment_month':shipment_month,
                                    'product_qty': quality,
                                    'no_of_bags':quality/60,
                                    'partner_id': partner_id and partner_id.id or False,
                                    'product_id': product_id.id,
                                    'packing_id':packing and packing.id or False,
                                    'pss_type':pss_type,
                                    'product_uom': product_id and product_id.uom_id.id,
                                    's_import_id': this.id,
                                    'specifications':specifications,
                                    'port_of_discharge':port_of_discharge and port_of_discharge.id or False,
                                    'port_of_loading': port_of_loading and port_of_loading.id or False,
                                    'start_of_Ship_period':start_of_Ship_period,
                                    'delivery_type':delivery_type,
                                    'end_of_ship_period':end_of_ship_period,
                                    'client_ref':client_ref,
                                    'precalculated_freight_cost':precalculated_freight_cost,
                                    'employess_id':pic,
#                                     'del_period':del_period
                                    }))
                        else:
                            error_line.append((0,0,{
                                    'name': s_contract,
#                                     'date': shipment_month,
                                    'notes': mess}))
                            failure += 1
                            line = row + 1
                            messenger += _('\n - Line ') + _(str(line)) + ':' + _(mess) or ''
            if contract_line != []:
                this.pcontract_import_ids = contract_line
            else:
                this.pcontract_import_ids = False    
            if error_line != []:
                this.line_pcontract_error_ids = error_line
            else:
                this.line_pcontract_error_ids = False
                
            this.failure = 0
            if failure > 0:
                this.failure = failure or  0
                warning = _('Errors arising at: ' + messenger)
            this.warning_mess = warning or False
        return True


    def confirm_p_contract(self):
        for line in self.pcontract_import_ids:
            p_id = self.env['s.contract'].create({
                        'name': line.name,
                        'date': line.date,
                        'date_catalog': line.date_catalog,
                        'partner_id': line.partner_id.id,
                        'type': 'p_contract'
            })
            p_id.onchange_partner_id()
            self.env['s.contract.line'].create({
                        'product_id': line.product_id.id,
                        'name': line.product_id.default_code,
                        'product_uom': line.product_uom.id,
                        'product_qty': line.product_qty or 0.0,
                        'market_price': line.market_price or 0.0,
                        'p_contract_diff': line.p_contract_diff or 0.0,
                        'p_contract_id': p_id.id
            })
            self.pcontract_ids = [(4, p_id.id)]
    
    def confirm_s_contract(self):
        for line in self.pcontract_import_ids:
            p_id = self.env['s.contract'].create({
                        'name': line.name,
                        'date': line.date,
                        'date_catalog': line.date,
                        'partner_id': line.partner_id.id,
                        'type': 'export',
                        'allocation_status':line.allocation_status,
                        'allocation_date':line.allocation_date,
                        'shipment_month':line.shipment_month,
                        'client_ref':line.client_ref,
                        'pss_type':line.pss_type,
                        'incoterms_id':line.incoterms_id and line.incoterms_id.id,
                        'start_of_Ship_period':line.start_of_Ship_period,
                        'end_of_ship_period':line.end_of_ship_period,
                        'delivery_type':line.delivery_type,
                        'employess_id':line.employess_id and line.employess_id.id or False,
                        'port_of_loading':line.port_of_loading and line.port_of_loading.id or False,
                        'port_of_discharge':line.port_of_discharge and line.port_of_discharge.id or False,
                        'precalculated_freight_cost':line.precalculated_freight_cost
            })
            p_id.onchange_partner_id()
            self.env['s.contract.line'].create({
                        'contract_id': p_id.id,
                        'product_id': line.product_id.id,
                        'name': line.specifications,
                        'product_uom': line.product_uom.id,
                        'product_qty': line.product_qty or 0.0,
                        'market_price': line.market_price or 0.0,
                        'p_contract_diff': line.p_contract_diff or 0.0,
                        'packing_id':line.packing_id and line.packing_id.id or False,
            })
            self.pcontract_ids = [(4, p_id.id)]
            return
    
    def import_contract(self):
        try:
#             for line in self.env['mapping.product'].search([]):
#                 line._product()
            
            for line in self.env['mapping.partner'].search([]):
                line._partner()
            # return
            if self.import_type =='p.contract':
                for line in self.env['mapping.product'].search([]):
                    line._product()
            
            for line in self.env['mapping.partner'].search([]):
                line._partner()
                
#                 self.import_p_contract()
            if self.import_type == 's.contract':
                self.import_s_contract()
        except Exception as e:
            raise e
        return 
    
    def confirm_import(self):
        try:
            if self.import_type =='p.contract':
                self.confirm_p_contract()
            if self.import_type == 's.contract':
                self.confirm_s_contract()
        except Exception as e:
            raise e
        self.update({'state':'done'})
        return 

    def button_reopen(self):
        try:
            if self.import_type =='p.contract':
                self.pcontract_ids = [(5, 0, 0)]
            if self.import_type =='s.contract':
                for line in self.pcontract_ids:
                    line.unlink()
                self.pcontract_ids = [(5, 0, 0)]
        except Exception as e:
            raise e
        self.update({'state':'draft'})
        return 


    def print_template_import_p(self):
        return {'type': 'ir.actions.report.xml', 'report_name': 'import_data_p_contract'}
    
    def print_p_data_error(self):
        return {'type': 'ir.actions.report.xml', 'report_name': 'import_data_p_contract_error'}


class ImportDataLine(models.Model):
    _name = 'import.data.line'

    import_id = fields.Many2one('import.data',string="Import")
    s_import_id = fields.Many2one('import.data',string="Import")
    name = fields.Char(string='Name')
    certificate = fields.Char(string='Certificate')
    partner_id = fields.Many2one('res.partner', string='Customer')
    date = fields.Date(string='Date')
    date_catalog = fields.Date(string='Date Catalog')
    product_id = fields.Many2one('product.product',string='Product')
    packing_id = fields.Many2one('ned.packing',string='Packing')
    quality_condition = fields.Char(string="Quality condition")
    product_qty = fields.Float(string='Qty')
    product_uom = fields.Many2one('product.uom',string='Uom')
    market_price = fields.Float(string='Market Price')
    p_contract_diff = fields.Float(string='P-Contract Differencial')
    client_ref = fields.Char('Client ref.')
    pss_condition = fields.Selection([('pss', 'Pss'), ('none-pss', 'None PSS')], string='Pss Condition')
    pss_type = fields.Selection([('SAS','SAS'),('SAP','SAP'),('PSS','PSS'),('PSS+OTS','PSS+OTS'),('No','No')],string="Pss type")
    start_of_Ship_period = fields.Date(string="Start of Ship. period")
    end_of_ship_period = fields.Date(string="End of ship. Period")
    delivery_type = fields.Char(string="Delivery type")
    del_period = fields.Char(string="Del period")
    specifications = fields.Char(string="specifications")
    port_of_loading = fields.Many2one('delivery.place', string='Port Of Loading', copy=False, readonly=True, )
    port_of_discharge = fields.Many2one('delivery.place', string='Port of Discharge', copy=False, readonly=True)
    incoterms_id = fields.Many2one('stock.incoterms', string='Term', required=False)
    shipment_month = fields.Date(string="Shipment month")
    no_of_bags = fields.Float(string="No. of bags")
    precalculated_freight_cost = fields.Integer(string="Precalculated freight Cost")
    employess_id = fields.Many2one('hr.employee',string="PIC")
    allocation_status = fields.Selection([('Third party','Third party'),('Paco BWH','Paco BWH'),('MBN BWH','MBN BWH'),('KTN-BWH','KTN-BWH'),('Ned VN','Ned VN'),('Local sale','Local sale'),('Spot','Spot'),('Unallocated','Unallocated'),('Afloat','Afloat'),('Cancel','Cancel')],string="Allocation Status")
    allocation_date = fields.Date(string="Allocation date")
    
class ErrorImport(models.Model):
    _name = "error.import"

    import_id = fields.Many2one('import.data',string="Import")

    name = fields.Char(string='Name')

    date = fields.Date(string='Date')
    date_catalog = fields.Date(string='Date Catalog')

    product_qty = fields.Float(string='Qty')

    market_price = fields.Float(string='Market Price')
    p_contract_diff = fields.Float(string='P-Contract Differencial')

    notes = fields.Text(string='Text')


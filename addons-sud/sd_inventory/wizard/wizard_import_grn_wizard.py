# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
import time
import base64
import xlrd
import logging
_logger = logging.getLogger(__name__)


class ImportGRN(models.TransientModel):
    _name = "import.grn"

    file = fields.Binary('File', help='Choose file Excel')
    file_name = fields.Char('Filename', readonly=True)

    def import_grn(self):
        try:
            recordlist = base64.decodestring(self.file)
            excel = xlrd.open_workbook(file_contents=recordlist)
            lst_sheet = excel.sheet_names()
            sh = excel.sheet_by_index(0)
            if len(lst_sheet) > 1:
                sh2 = excel.sheet_by_index(1)
        except  e:
            raise UserError(_('Warning!'), str(e))
        if sh:
            picking_ids = []
            num_of_rows = sh.nrows
            for row in range(1, num_of_rows):
                picking = self.env['stock.picking']
                mess = ""
                value = {}
                line_value = {}
                picking_type = sh.cell(row, 0).value
                partner_code = sh.cell(row, 1).value
                source_location = sh.cell(row, 2).value
                warehouse = sh.cell(row, 3).value
                destination_location = sh.cell(row, 4).value
                certificate = sh.cell(row, 5).value
                source = sh.cell(row, 6).value
                vehical_no = sh.cell(row, 7).value
                schedule_date = sh.cell(row, 8).value
                date_transfer = sh.cell(row, 9).value
                cert_type = sh.cell(row, 10).value
                product = sh.cell(row, 11).value
                quantity = sh.cell(row, 12).value
                receipt = sh.cell(row, 13).value
                if receipt:
                    value.update({
                        'is_quota_temp': True
                    })
                if picking_type:
                    picking_type_id = self.env['stock.picking.type'].browse(int(picking_type))
                    if picking_type_id:
                        value.update({
                            'picking_type_id': int(picking_type_id.id)
                        })
                    else:
                        mess += "Avis not have Picking Type with ID %s, please check again\n" % picking_type
                if partner_code:
                    partner = self.env['res.partner'].search([
                        ('partner_code', '=', partner_code)
                    ])
                    if len(partner) > 1:
                        mess += "Found more than 1 partner with partner code %s in Avis, please check again\n" % partner_code
                    elif not partner:
                        mess += "Not found partner with partner code %s in Avis, please check again\n" % partner_code
                    else:
                        value.update({
                            'partner_id': partner.id
                        })
                if source_location:
                    source_location_id = self.env['stock.location'].browse(int(source_location))
                    if source_location_id:
                        value.update({
                            'location_id': int(source_location_id.id)
                        })
                        line_value.update({
                            'location_id': int(source_location_id.id)
                        })
                    else:
                        mess += "Avis not have Source Location Zone with ID %s, please check again\n" % source_location
                if warehouse:
                    warehouse_id = self.env['stock.warehouse'].search([
                        ('code', '=', warehouse)
                    ])
                    if len(warehouse_id) > 1:
                        mess += "Found more than 1 Warehouse with code %s in Avis, please check again\n" % warehouse
                    elif not warehouse_id:
                        mess += "Not found Warehouse with code %s in Avis, please check again\n" % warehouse
                    else:
                        value.update({
                            'warehouse_id': warehouse_id.id
                        })
                if destination_location:
                    destination_location_id = self.env['stock.location'].browse(int(destination_location))
                    if destination_location_id:
                        value.update({
                            'location_dest_id': int(destination_location_id.id)
                        })
                        line_value.update({
                            'location_dest_id': int(destination_location_id.id)
                        })
                    else:
                        mess += "Avis not have Destination Location Zone with ID %s, please check again\n"\
                                % destination_location
                if certificate:
                    certificate_id = self.env['ned.certificate'].search([
                        ('code', '=', certificate)
                    ])
                    if len(certificate_id) > 1:
                        mess += "Found more than 1 Certificate with code %s in Avis, please check again\n" % certificate
                    elif not certificate_id:
                        mess += "Not found Certificate with code %s in Avis, please check again\n" % certificate
                    else:
                        value.update({
                            'certificate_id': certificate_id.id
                        })
                if source:
                    district = self.env['res.district'].browse(int(source))
                    if district:
                        value.update({
                            'districts_id': int(district.id)
                        })
                    else:
                        mess += "Avis not have District with ID %s, please check again\n" % source
                if vehical_no:
                    value.update({
                        'vehicle_no': str(vehical_no)
                    })
                if schedule_date:
                    value.update({
                        'scheduled_date': str(schedule_date)
                    })
                if date_transfer:
                    value.update({
                        'date_done': str(date_transfer)
                    })
                if cert_type:
                    value.update({
                        'cert_type': str(cert_type)
                    })
                if product:
                    product_id = self.env['product.product'].search([
                        ('default_code', '=', product)
                    ])
                    if len(product_id) > 1:
                        mess += "Found more than 1 Product with code %s in Avis, please check again\n" % product
                    elif not product_id:
                        mess += "Not found Product with code %s in Avis, please check again\n" % product
                    else:
                        line_value.update({
                            'product_id': product_id.id,
                            'product_uom_id': product_id.uom_id.id if product_id.uom_id else False
                        })
                if quantity:
                    line_value.update({
                        'init_qty': quantity
                    })
                if mess:
                    raise UserError(_(mess))
                picking_id = picking.create(value)
                picking_ids.append(picking_id.id)
                picking_id.write({
                    'scheduled_date': str(schedule_date)
                })
                line_value.update({
                    'picking_id': picking_id.id,
                    #'name': 'GRN-Temp',
                })
                self.env['stock.move.line'].create(line_value)
            if picking_ids:
                return self.action_view_grn(picking_ids)
        return True
    
    
    def action_view_grn(self, picking_ids):
        
        return  {
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'stock.picking',
                'domain': [('id', 'in', picking_ids)],
                'target': 'current',
                'context': {}
            }
    
        
    
    
        
        
        
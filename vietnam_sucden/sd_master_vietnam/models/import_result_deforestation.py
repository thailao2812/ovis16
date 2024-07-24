# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _
import base64
import xlrd
from odoo.exceptions import ValidationError, UserError
from math import radians, sin, cos, sqrt, atan2
import json


class ImportDeforestation(models.Model):
    _name = 'import.deforestation'

    file = fields.Binary(string='File')
    filename = fields.Char(string='Name')

    def import_deforestation(self):
        try:
            recordlist = base64.decodebytes(self.file)
            excel = xlrd.open_workbook(file_contents=recordlist)
            lst_sheet = excel.sheet_names()
            sh = excel.sheet_by_index(0)
            if len(lst_sheet) > 1:
                sh2 = excel.sheet_by_index(1)
        except ImportError:
            raise UserError(_('Warning!'), str(ImportError))
        if sh:
            num_of_rows = sh.nrows
            for row in range(1, num_of_rows):
                farmer = self.env['res.partner'].search([
                    ('partner_code', '=', sh.cell(row, 0).value.strip()[:-1])
                ], limit=1)
                if farmer:
                    checking = sh.cell(row, 18).value
                    if checking > 0:
                        farmer.in_deforestation = 'yes'
                    else:
                        farmer.in_deforestation = 'no'
                if not farmer:
                    farmer_new = self.env['res.partner'].create({
                        'name': sh.cell(row, 13).value.strip(),
                        'partner_code': sh.cell(row, 0).value.strip()[:-1],
                        'is_farmer': True
                    })
                    checking = sh.cell(row, 18).value
                    if checking > 0:
                        farmer_new.in_deforestation = 'yes'
                    else:
                        farmer_new.in_deforestation = 'no'

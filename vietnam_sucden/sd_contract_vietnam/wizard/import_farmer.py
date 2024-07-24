# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _
import base64
import xlrd
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class ImportFarmer(models.TransientModel):
    _name = 'import.farmer'

    file = fields.Binary(string='File')
    filename = fields.Char(string='Name')

    def import_farmer(self):
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
            mess = ''
            value_contract = []
            if sh.cell(1, 9):
                if sh.cell(1, 9).value == 'GRN':
                    for row in range(2, num_of_rows):
                        if sh.cell(row, 10).value:
                            contract = self.env['purchase.contract'].search([
                                ('name', '=', sh.cell(row, 10).value.strip())
                            ])
                            if contract:
                                if contract not in value_contract:
                                    value_contract.append(contract)
                    for con in value_contract:
                        for far in con.list_farmer:
                            far.unlink()
                    for row in range(2, num_of_rows):
                        farmer = False
                        date = False
                        if isinstance(sh.cell(row, 0).value, float):
                            date = sh.cell(row, 0).value and datetime(
                                *xlrd.xldate_as_tuple(sh.cell(row, 0).value, excel.datemode)).date() or False
                        if sh.cell(row, 9).value:
                            continue
                        if sh.cell(row, 1).value:
                            farmer = self.env['res.partner'].search([
                                ('partner_code', '=', sh.cell(row, 1).value.strip())
                            ], limit=1)
                            if farmer:
                                farmer.is_farmer = True
                            if not farmer:
                                create_new_farmer = self.env['res.partner'].create({
                                    'name': sh.cell(row, 2).value.strip(),
                                    'partner_code': sh.cell(row, 1).value.strip(),
                                    'is_farmer': True
                                })
                                farmer = create_new_farmer
                        if sh.cell(row, 10).value:
                            contract = self.env['purchase.contract'].search([
                                ('name', '=', sh.cell(row, 10).value.strip())
                            ])
                            if not contract:
                                mess += 'The contract cannot found in the system, please check your file again %s \n' \
                                        % sh.cell(row, 10).value
                            else:
                                if len(contract) > 1:
                                    mess += 'The contract found more than 2 with the same name in the system, ' \
                                            'please check your file again %s \n' \
                                            % sh.cell(row, 10).value
                                if len(contract) == 1:
                                    self.env['list.farmer'].create({
                                        'purchase_contract_id': contract.id,
                                        'farmer_id': farmer.id,
                                        'farmer_code': farmer.partner_code,
                                        'quantity': sh.cell(row, 3).value,
                                        'date': date
                                    })

            # if sh.cell(0, 0).value == 'Name':
            #     for row in range(1, num_of_rows):
            #         farmer = self.env['res.partner'].search([
            #             ('partner_code', '=', sh.cell(row, 12).value.strip())
            #         ], limit=1)
            #         if farmer:
            #             farmer.is_farmer = True
            #         if not farmer:
            #             self.env['res.partner'].create({
            #                 'name': sh.cell(row, 13).value.strip(),
            #                 'partner_code': sh.cell(row, 12).value.strip(),
            #                 'is_farmer': True
            #             })

            if sh.cell(2, 0).value == 'stt':
                for row in range(3, num_of_rows):
                    farmer = self.env['res.partner'].search([
                        ('partner_code', '=', sh.cell(row, 1).value.strip())
                    ], limit=1)
                    if farmer:
                        farmer.is_farmer = True
                        farmer.certificate_ids = [(5, 0, 0)]
                        if sh.cell(row, 3).value:
                            if '+' in sh.cell(row, 3).value:
                                cert = sh.cell(row, 3).value.strip().split('+')
                                for i in cert:
                                    ned_cert = self.env['ned.certificate'].search([
                                        ('code', '=', i)
                                    ])
                                    if ned_cert:
                                        farmer.certificate_ids = [(4, ned_cert.id)]
                            else:
                                ned_cert = self.env['ned.certificate'].search([
                                    ('code', '=', sh.cell(row, 3).value.strip())
                                ])
                                if ned_cert:
                                    farmer.certificate_ids = [(4, ned_cert.id)]
                    if not farmer:
                        farmer_new = self.env['res.partner'].create({
                            'name': sh.cell(row, 2).value.strip(),
                            'partner_code': sh.cell(row, 1).value.strip(),
                            'is_farmer': True
                        })
                        if sh.cell(row, 3).value:
                            if '+' in sh.cell(row, 3).value:
                                cert = sh.cell(row, 3).value.strip().split('+')
                                for i in cert:
                                    ned_cert = self.env['ned.certificate'].search([
                                        ('code', '=', i)
                                    ])
                                    if ned_cert:
                                        farmer_new.certificate_ids = [(4, ned_cert.id)]


            if mess != '':
                raise UserError(_(mess))

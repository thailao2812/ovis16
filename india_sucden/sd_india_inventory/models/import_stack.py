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
from base64 import b64encode
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class ImportStack(models.Model):
    _name = 'import.update.stack'

    file = fields.Binary(string='File')
    file_name = fields.Char(string='File name')

    def import_stack(self):
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
                if sh.cell(row, 4).value:
                    packing = self.env['ned.packing'].search([
                        ('name', 'like', sh.cell(row, 4).value.strip())
                    ])
                    stack = self.env['stock.lot'].search([
                        ('name', 'like', sh.cell(row, 0).value.strip())
                    ])
                    if stack:
                        stack.packing_id = packing.id
            # num_of_rows = sh.nrows
            # for row in range(1, num_of_rows):
            #     if sh.cell(row, 0).value:
            #         stack = self.env['stock.lot'].search([
            #             ('name', '=', sh.cell(row, 0).value.strip())
            #         ])
            #         print(stack)
            #         if stack:
            #             stack.outturn_percent = sh.cell(row, 1).value if sh.cell(row, 1).value else 0
            #             stack.aaa_percent = sh.cell(row, 2).value if sh.cell(row, 2).value else 0
            #             stack.aa_percent = sh.cell(row, 3).value if sh.cell(row, 3).value else 0
            #             stack.a_percent = sh.cell(row, 4).value if sh.cell(row, 4).value else 0
            #             stack.b_percent = sh.cell(row, 5).value if sh.cell(row, 5).value else 0
            #             stack.c_percent = sh.cell(row, 6).value if sh.cell(row, 6).value else 0
            #             stack.pb_percent = sh.cell(row, 7).value if sh.cell(row, 7).value else 0
            #             stack.bb_percent = sh.cell(row, 8).value if sh.cell(row, 8).value else 0
            #             stack.bleached_percent = sh.cell(row, 9).value if sh.cell(row, 9).value else 0
            #             stack.idb_percent = sh.cell(row, 10).value if sh.cell(row, 10).value else 0
            #             stack.bits_percent = sh.cell(row, 11).value if sh.cell(row, 11).value else 0
            #             stack.hulks_percent = sh.cell(row, 12).value if sh.cell(row, 12).value else 0
            #             stack.stone_percent = sh.cell(row, 13).value if sh.cell(row, 13).value else 0
            #             stack.skin_out_percent = sh.cell(row, 14).value if sh.cell(row, 14).value else 0
            #             stack.triage_percent = sh.cell(row, 15).value if sh.cell(row, 15).value else 0
            #             stack.wet_bean_percent = sh.cell(row, 16).value if sh.cell(row, 16).value else 0
            #             stack.red_beans_percent = sh.cell(row, 17).value if sh.cell(row, 17).value else 0
            #             stack.stinker_percent = sh.cell(row, 18).value if sh.cell(row, 18).value else 0
            #             stack.faded_percent = sh.cell(row, 19).value if sh.cell(row, 19).value else 0
            #             stack.flat_percent = sh.cell(row, 20).value if sh.cell(row, 20).value else 0
            #             stack.pb1_percent = sh.cell(row, 21).value if sh.cell(row, 21).value else 0
            #             stack.pb2_percent = sh.cell(row, 22).value if sh.cell(row, 22).value else 0
            #             stack.sleeve_6_up_percent = sh.cell(row, 23).value if sh.cell(row, 23).value else 0
            #             stack.sleeve_5_5_up_percent = sh.cell(row, 24).value if sh.cell(row, 24).value else 0
            #             stack.sleeve_5_5_down_percent = sh.cell(row, 25).value if sh.cell(row, 25).value else 0
            #             stack.sleeve_5_down_percent = sh.cell(row, 26).value if sh.cell(row, 26).value else 0
            #             stack.sleeve_5_up_percent = sh.cell(row, 27).value if sh.cell(row, 27).value else 0
            #             stack.unhulled_percent = sh.cell(row, 28).value if sh.cell(row, 28).value else 0
            #             stack.remaining_coffee_percent = sh.cell(row, 29).value if sh.cell(row, 29).value else 0
            #             stack.blacks_percent = sh.cell(row, 30).value if sh.cell(row, 30).value else 0
            #             stack.half_monsoon_percent = sh.cell(row, 31).value if sh.cell(row, 31).value else 0
            #             stack.good_beans_percent = sh.cell(row, 32).value if sh.cell(row, 32).value else 0
            #             stack.moisture_percent = sh.cell(row, 33).value if sh.cell(row, 33).value else 0
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re


import base64
import xlrd
import logging
_logger = logging.getLogger(__name__)


class ImportQcGRN(models.TransientModel):
    _name = "import.qc.grn"

    file = fields.Binary('File', help='Choose file Excel')
    file_name = fields.Char('Filename', readonly=True)

    def import_qc_grn(self):
        try:
            recordlist = base64.decodestring(self.file)
            excel = xlrd.open_workbook(file_contents=recordlist)
            lst_sheet = excel.sheet_names()
            sh = excel.sheet_by_index(0)
            if len(lst_sheet) > 1:
                sh2 = excel.sheet_by_index(1)
        except e:
            raise UserError(_('Warning!'), str(e))
        if sh:
            request_kcs_line_ids = []
            num_of_rows = sh.nrows
            for row in range(1, num_of_rows):
                picking = self.env['stock.picking']
                mess = ""
                stock_picking = False
                warehouse = False
                s_contract = False
                value = {}
                picking_name = sh.cell(row, 0).value
                warehouse_code = sh.cell(row, 1).value
                p_contract = sh.cell(row, 2).value
                mc = sh.cell(row, 3).value
                fm = sh.cell(row, 4).value
                black = sh.cell(row, 5).value
                broken = sh.cell(row, 6).value
                brown = sh.cell(row, 7).value
                mold = sh.cell(row, 8).value
                cherry = sh.cell(row, 9).value
                excelsa = sh.cell(row, 10).value
                sc20 = sh.cell(row, 11).value
                sc19 = sh.cell(row, 12).value
                sc18 = sh.cell(row, 13).value
                sc17 = sh.cell(row, 14).value
                sc16 = sh.cell(row, 15).value
                sc15 = sh.cell(row, 16).value
                sc14 = sh.cell(row, 17).value
                sc13 = sh.cell(row, 18).value
                sc12 = sh.cell(row, 19).value
                belowsc12 = sh.cell(row, 20).value
                burned = sh.cell(row, 21).value
                insect_bean = sh.cell(row, 22).value
                immature = sh.cell(row, 23).value
                analysis_by = sh.cell(row, 24).value
                sampler = sh.cell(row, 25).value
                bulk = sh.cell(row, 26).value
                stone = sh.cell(row, 27).value
                stick = sh.cell(row, 28).value
                inspector = False
                if sampler:
                    inspector = self.env['x_inspectors.kcs'].search([
                        ('name', '=', sampler)
                    ])
                    if not inspector:
                        inspector = self.env['x_inspectors.kcs'].create({
                            'name': sampler
                        })
                if picking_name:
                    stock_picking = picking.search([
                        ('name', '=', picking_name)
                    ])
                    if not stock_picking:
                        mess += "Picking %s cannot found at row %s\n" % (picking_name, row + 1)
                if warehouse_code:
                    warehouse = self.env['stock.warehouse'].search([
                        ('code', '=', warehouse_code)
                    ])
                    if not warehouse:
                        mess += "Warehouse %s cannot found at row %s\n" % (warehouse_code, row + 1)
                if p_contract:
                    s_contract = self.env['s.contract'].search([
                        ('name', '=', p_contract)
                    ])
                    if not s_contract:
                        mess += "P Contract %s cannot found at row %s\n" % (p_contract, row+1)

                # if warehouse and stock_picking:
                #     if warehouse.x_is_bonded and stock_picking.pcontract_id:
                #         if stock_picking.pcontract_id != s_contract:
                #             mess += "P Contract %s does not mapping with Picking %s at row %s\n" % (s_contract, stock_picking.name, row + 1)
                if mess:
                    raise UserError(_(mess))
                else:
                    if inspector:
                        value.update({
                            'sample_weight': 100,
                            'bb_sample_weight': 100,
                            'mc_degree': mc,
                            'fm_gram': fm,
                            'black_gram': black,
                            'broken_gram': broken,
                            'brown_gram': brown,
                            'mold_gram': mold,
                            'cherry_gram': cherry,
                            'excelsa_gram': excelsa,
                            'screen20_gram': sc20,
                            'screen19_gram': sc19,
                            'screen18_gram': sc18,
                            'screen17_gram': sc17,
                            'screen16_gram': sc16,
                            'screen15_gram': sc15,
                            'screen14_gram': sc14,
                            'screen13_gram': sc13,
                            'greatersc12_gram': sc12,
                            'belowsc12_gram': belowsc12,
                            'immature_gram': immature,
                            'burned_gram': burned,
                            'eaten_gram': insect_bean,
                            'stone_count': stone,
                            'stick_count': stick,
                            'sampler': analysis_by,
                            'x_bulk_density': bulk,
                            'x_inspectator': inspector.id
                        })
                        if stock_picking.kcs_line:
                            for i in stock_picking.kcs_line:
                                i.write(value)
                                request_kcs_line_ids.append(i.id)
                        else:
                            stock_picking.btt_loads()
                            for i in stock_picking.kcs_line:
                                i.write(value)
                                request_kcs_line_ids.append(i.id)
                    else:
                        value.update({
                            'sample_weight': 100,
                            'bb_sample_weight': 100,
                            'mc_degree': mc,
                            'fm_gram': fm,
                            'black_gram': black,
                            'broken_gram': broken,
                            'brown_gram': brown,
                            'mold_gram': mold,
                            'cherry_gram': cherry,
                            'excelsa_gram': excelsa,
                            'screen20_gram': sc20,
                            'screen19_gram': sc19,
                            'screen18_gram': sc18,
                            'screen17_gram': sc17,
                            'screen16_gram': sc16,
                            'screen15_gram': sc15,
                            'screen14_gram': sc14,
                            'screen13_gram': sc13,
                            'greatersc12_gram': sc12,
                            'belowsc12_gram': belowsc12,
                            'immature_gram': immature,
                            'burned_gram': burned,
                            'eaten_gram': insect_bean,
                            'stone_count': stone,
                            'stick_count': stick,
                            'sampler': analysis_by,
                            'x_bulk_density': bulk,
                            'x_inspectator': False
                        })
                        if stock_picking.kcs_line:
                            for i in stock_picking.kcs_line:
                                i.write(value)
                                request_kcs_line_ids.append(i.id)
                        else:
                            stock_picking.btt_loads()
                            for i in stock_picking.kcs_line:
                                i.write(value)
                                request_kcs_line_ids.append(i.id)
                                
            if request_kcs_line_ids:
                return self.action_view_p_contract(request_kcs_line_ids)
                        
        return True
    
    def action_view_p_contract(self, request_kcs_line_ids):
        return  {
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'request.kcs.line',
                'domain': [('id', 'in', request_kcs_line_ids)],
                'target': 'current',
                'context': {}
            }


    def template_import(self):
        return self.env.ref(
                'sd_quality.report_template_import_qc_grn').report_action(self)
                

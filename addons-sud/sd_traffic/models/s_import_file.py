# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
myear = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
import base64
from xlrd import open_workbook
lst_status = ['Paco BWH', 'MBN BWH', 'KTN BWH', '3rd party', 'Ned VN', 'Local sale', 'Spot', 'Unallocated', 'Afloat', 'Factory', 'Cancel']


class SImportFile(models.Model):
    _inherit = "s.import.file"

    s_contract_id = fields.Many2one('traffic.contract', string='S Contract')


    def import2p(self):
        smonth_obj = self.env['s.period']
        partner_obj = self.env['res.partner']
        product_obj = self.env['product.product']
        cert_obj = self.env['ned.certificate']
        pack_obj = self.env['ned.packing']
        incoterm_obj = self.env['account.incoterms']
        import_data_obj = self.env['import.data']
        map_partner_obj = self.env['mapping.partner']
        map_prod_obj = self.env['mapping.product']
        ware_obj = self.env['stock.warehouse']
        contract_obj = self.env['s.contract']
        for record in self:
            if record.im_file:
                filecontent = base64.b64decode(record.im_file)
                temp_path = '/tmp/import_pcontract_%s.xls' % str(datetime.now())
                with open(temp_path, 'wb') as f:
                    f.write(filecontent)

                wb = open_workbook(temp_path)
                for sheet in wb.sheets():
                    number_of_rows = sheet.nrows
                    number_of_columns = sheet.ncols
                    items = []
                    rows = []
                    nrow = 0
                    for row in range(1, number_of_rows):
                        vals = {'type': 'p_contract'}
                        nrow += 1
                        if sheet.cell(row, 0).value:
                            warehouse_id = ware_obj.search([('code', '=', sheet.cell(row, 0).value)], limit=1)
                            warehouse_id = warehouse_id and warehouse_id.id or 0
                            if warehouse_id:
                                vals.update({'warehouse_id': warehouse_id})

                        if sheet.cell(row, 6).value:
                            if self.map_datetime(sheet.cell_value(row, 6), wb.datemode):
                                fmyear = self.map_datetime(sheet.cell_value(row, 6), wb.datemode)
                                remyear = '%s-%s' % (myear[fmyear.month], str(fmyear.year))
                                smonth_id = smonth_obj.search([('name', '=', remyear)], limit=1)
                                smonth_id = smonth_id and smonth_id.id or 0
                                if not smonth_id:
                                    smonth_id = smonth_obj.create({'name': remyear})
                                    smonth_id = smonth_id and smonth_id.id or 0
                                if smonth_id:
                                    vals.update({'shipt_month': smonth_id})
                            else:
                                smonth_id = smonth_obj.search([('name', '=', sheet.cell(row, 6).value)], limit=1)
                                smonth_id = smonth_id and smonth_id.id or 0
                                if not smonth_id:
                                    smonth_id = smonth_obj.create({'name': sheet.cell(row, 6).value})
                                    smonth_id = smonth_id and smonth_id.id or 0
                                if smonth_id:
                                    vals.update({'shipt_month': smonth_id})

                        prod_id = 0
                        packing_id = 0

                        if sheet.cell(row, 13).value:
                            prod_id = product_obj.search([
                                ('name', '=', sheet.cell(row, 13).value)
                            ], limit=1)
                            prod_id = prod_id and prod_id.id or 0
                            if not prod_id:
                                # product_id = import_data_obj.slip_name(sheet.cell(row,7).value)
                                product_id = map_prod_obj.search([
                                    ('quality', '=', sheet.cell(row, 13).value)], limit=1)
                                if product_id:
                                    prod_id = product_id and product_id.product_id.id or 0
                            if not prod_id:
                                prod_id = self.env.ref('ned_contract.product_product_tpaned')
                                prod_id = prod_id.read([])[0]
                                prod_id = prod_id and prod_id['id'] or 0
                            if prod_id:
                                vals.update({'standard_id': prod_id})

                        if sheet.cell(row, 5).value:
                            partner_id = partner_obj.search([
                                '|', ('name', '=', sheet.cell(row, 5).value),
                                ('shortname', '=', sheet.cell(row, 5).value)
                            ], limit=1)
                            if not partner_id:
                                partner_id = map_partner_obj.search([('client_name', '=', sheet.cell(row, 5).value)],
                                                                    limit=1)
                                if partner_id:
                                    partner_id = partner_id.patner_id and partner_id.patner_id.id or 0
                                else:
                                    partner_id = partner_obj.create({
                                        'name': sheet.cell(row, 5).value,
                                        'shortname': sheet.cell(row, 5).value
                                    })
                                    partner_id = partner_id and partner_id.id or 0
                            else:
                                partner_id = partner_id and partner_id.id or 0
                            if partner_id:
                                vals.update({'partner_id': partner_id})

                        packing_id = pack_obj.search([('name', '=', sheet.cell(row, 12).value)], limit=1)
                        packing_id = packing_id and packing_id.id or 0
                        if packing_id:
                            vals.update({'packing_id': packing_id})

                        try:
                            vals.update({'name': 'P-%s' % str(int(sheet.cell(row, 4).value))})
                        except:
                            vals.update({'name': 'P-%s' % str(sheet.cell(row, 4).value)})
                        if sheet.cell(row, 14).value:
                            certificate = self.env['ned.certificate'].search([
                                ('code', '=', sheet.cell(row, 14).value)
                            ], limit=1)
                            if certificate:
                                cert_obj = certificate
                        if sheet.cell(row, 15).value:
                            origin = self.env['res.country'].search([
                                ('code', '=', sheet.cell(row, 15).value)
                            ])
                            if origin:
                                vals.update({
                                    'origin_new': origin.id
                                })
                        vals.update({
                            'p_qty': sheet.cell(row, 8).value,
                            'x_coffee_type': sheet.cell(row, 3).value or '',
                            'no_of_pack': sheet.cell(row, 9).value,
                            'p_quality': sheet.cell(row, 7).value,
                            'type': 'p_contract',
                            'x_is_bonded': True,
                            'certificate_id': cert_obj.id if cert_obj else False,
                        })
                        contract_id = contract_obj.create(vals)

                        self.env['s.contract.line'].create({
                            'product_id': prod_id,
                            'name': sheet.cell(row, 7).value or '',
                            'packing_id': packing_id,
                            'product_qty': sheet.cell(row, 8).value,
                            'number_of_bags': sheet.cell(row, 9).value,
                            'product_uom': product_obj.browse(prod_id).uom_po_id.id,
                            'p_contract_id': contract_id.id
                        })
        return 1

    def import2s(self):
        smonth_obj = self.env['s.period']
        pic_obj = self.env['s.pic']
        partner_obj = self.env['res.partner']
        product_obj = self.env['product.product']
        cert_obj = self.env['ned.certificate']
        pack_obj = self.env['ned.packing']
        shipby_obj = self.env['s.ship.by']
        incoterm_obj = self.env['account.incoterms']
        import_data_obj = self.env['import.data']
        map_partner_obj = self.env['mapping.partner']
        map_prod_obj = self.env['mapping.product']
        ware_obj = self.env['stock.warehouse']
        contract_obj = self.env['traffic.contract']
        del_place_obj = self.env['delivery.place']
        shiping_line_obj = self.env['shipping.line']
        for record in self:
            lst_errors = []
            if record.im_file:
                filecontent = base64.b64decode(record.im_file)
                temp_path = '/tmp/import_scontract_%s.xls' % str(datetime.now())
                with open(temp_path, 'wb') as f:
                    f.write(filecontent)
                wb = open_workbook(temp_path)
                if 2 > 1:
                    sheet = wb.sheets()[0]
                    number_of_rows = sheet.nrows
                    number_of_columns = sheet.ncols
                    items = []

                    rows = []
                    nrow = 0
                    for row in range(1, number_of_rows):
                        vals = {}
                        nrow += 1
                        try:
                            if sheet.cell(row, 0).value:
                                shipby_id = shipby_obj.search([
                                    '|', ('name', '=', sheet.cell(row, 0).value),
                                    ('code', '=', sheet.cell(row, 0).value)
                                ], limit=1)
                                shipby_id = shipby_id and shipby_id.id or 0
                                if not shipby_id:
                                    shipby_id = shipby_obj.create({
                                        'name': sheet.cell(row, 0).value,
                                        'code': sheet.cell(row, 0).value
                                    })
                                    shipby_id = shipby_id and shipby_id.id or 0
                                if shipby_id:
                                    vals.update({'shipby_id': shipby_id})

                            if sheet.cell(row, 2).value:
                                if self.map_datetime(sheet.cell_value(row, 2), wb.datemode):
                                    fmyear = self.map_datetime(sheet.cell_value(row, 2), wb.datemode)
                                    remyear = '%s-%s' % (myear[fmyear.month], str(fmyear.year))
                                    smonth_id = smonth_obj.search([('name', '=', remyear)], limit=1)
                                    smonth_id = smonth_id and smonth_id.id or 0
                                    if not smonth_id:
                                        smonth_id = smonth_obj.create({'name': remyear})
                                        smonth_id = smonth_id and smonth_id.id or 0
                                    if smonth_id:
                                        vals.update({'shipt_month': smonth_id})
                                else:
                                    smonth_id = smonth_obj.search([('name', '=', sheet.cell(row, 2).value)], limit=1)
                                    smonth_id = smonth_id and smonth_id.id or 0
                                    if not smonth_id:
                                        smonth_id = smonth_obj.create({'name': sheet.cell(row, 2).value})
                                        smonth_id = smonth_id and smonth_id.id or 0
                                    if smonth_id:
                                        vals.update({'shipt_month': smonth_id})

                            start_ship_pe = ''
                            try:
                                start_ship_pe = sheet.cell_value(row, 15) and self.map_datetime(
                                    sheet.cell_value(row, 15), wb.datemode) or False
                                start_ship_pe = start_ship_pe and '%s-%s-%s' % (
                                str(start_ship_pe.year), str(start_ship_pe.month), str(start_ship_pe.day)) or False
                                if start_ship_pe:
                                    vals.update({'start_of_ship_period': start_ship_pe})
                            except:

                                start_ship_pe = self.convert_date(sheet.cell(row, 15).value)
                                if start_ship_pe:
                                    vals.update({'start_of_ship_period': start_ship_pe})

                            end_ship_pe = ''
                            try:
                                end_ship_pe = sheet.cell_value(row, 16) and self.map_datetime(sheet.cell_value(row, 16),
                                                                                              wb.datemode) or False
                                end_ship_pe = end_ship_pe and '%s-%s-%s' % (
                                str(end_ship_pe.year), str(end_ship_pe.month), str(end_ship_pe.day)) or False
                                if end_ship_pe:
                                    vals.update({'end_of_ship_period': end_ship_pe})
                            except:
                                end_ship_pe = self.convert_date(sheet.cell(row, 16).value)
                                if end_ship_pe:
                                    vals.update({'end_of_ship_period': end_ship_pe})

                            end_ship_act = ''
                            try:
                                end_ship_act = sheet.cell_value(row, 18) and self.map_datetime(
                                    sheet.cell_value(row, 18), wb.datemode) or False
                                end_ship_act = end_ship_act and '%s-%s-%s' % (
                                str(end_ship_act.year), str(end_ship_act.month), str(end_ship_act.day)) or False
                                if end_ship_act:
                                    vals.update({'end_of_ship_period_actual': end_ship_act})
                            except:
                                end_ship_act = self.convert_date(sheet.cell(row, 18).value)
                                if end_ship_act:
                                    vals.update({'end_of_ship_period_actual': end_ship_act})

                            allo_date = ''
                            try:
                                allo_date = sheet.cell_value(row, 1) and self.map_datetime(sheet.cell_value(row, 1),
                                                                                           wb.datemode) or False
                                allo_date = allo_date and '%s-%s-%s' % (
                                str(allo_date.year), str(allo_date.month), str(allo_date.day)) or False
                                if allo_date:
                                    vals.update({'allocated_date': allo_date})
                            except:
                                allo_date = self.convert_date(sheet.cell(row, 1).value)
                                if allo_date:
                                    vals.update({'allocated_date': allo_date})

                            if sheet.cell(row, 6).value:
                                partner_id = partner_obj.search([
                                    '|', ('name', '=', sheet.cell(row, 6).value),
                                    ('shortname', '=', sheet.cell(row, 6).value)
                                ], limit=1)
                                if not partner_id:
                                    partner_id = import_data_obj.slip_name(sheet.cell(row, 6).value)
                                    partner_id = map_partner_obj.search(
                                        [('client_name', '=', sheet.cell(row, 6).value)], limit=1)
                                    if partner_id:
                                        partner_id = partner_id.patner_id and partner_id.patner_id.id or 0
                                    else:
                                        partner_id = partner_obj.create({
                                            'name': sheet.cell(row, 6).value,
                                            'shortname': sheet.cell(row, 6).value
                                        })
                                        partner_id = partner_id and partner_id.id or 0
                                else:
                                    partner_id = partner_id and partner_id.id or 0
                                if partner_id:
                                    vals.update({'partner_id': partner_id})

                            if sheet.cell(row, 9).value:
                                prod_id = product_obj.search([
                                    ('name', '=', sheet.cell(row, 9).value)
                                ], limit=1)
                                prod_id = prod_id and prod_id.id or 0
                                if not prod_id:
                                    # product_id = import_data_obj.slip_name(sheet.cell(row, 11).value)
                                    # product_id = product_obj.search([
                                    #     '|', ('name', '=', sheet.cell(row, 9).value),
                                    #     ('default_code', '=', sheet.cell(row, 9).value)], limit=1)
                                    # if product_id:
                                    #     prod_id = product_id and product_id.id or 0
                                    vals.update({'standard_id': False})
                                # if not prod_id:
                                #     prod_id = self.env.ref('ned_contract.product_product_tpaned')
                                #     prod_id = prod_id.read([])[0]
                                #     prod_id = prod_id and prod_id['id'] or 0
                                if prod_id:
                                    vals.update({'standard_id': prod_id})

                            pic_id = 0
                            if sheet.cell(row, 19).value:
                                try:
                                    pic_id = pic_obj.search([('code', '=', str(int(sheet.cell(row, 19).value)))],
                                                            limit=1)
                                except:
                                    pic_id = pic_obj.search([('name', '=', sheet.cell(row, 19).value)], limit=1)
                                if not pic_id:
                                    pic_id = pic_obj.create({'name': sheet.cell(row, 19).value})
                                    pic_id = pic_id and pic_id.id or 0
                                else:
                                    pic_id = pic_id and pic_id.id or 0
                                if pic_id:
                                    vals.update({'pic_id': pic_id})

                            if sheet.cell(row, 10).value:
                                certificate_id = cert_obj.search([
                                    '|', ('name', '=', sheet.cell(row, 10).value),
                                    ('code', '=', sheet.cell(row, 10).value)], limit=1)
                                certificate_id = certificate_id and certificate_id.id or 0
                                if certificate_id:
                                    vals.update({'certificate_id': certificate_id})

                            if sheet.cell(row, 14).value:
                                incoterm_id = incoterm_obj.search([('code', '=', sheet.cell(row, 14).value)], limit=1)
                                incoterm_id = incoterm_id and incoterm_id.id or 0
                                if incoterm_id:
                                    vals.update({'incoterms_id': incoterm_id})

                            if sheet.cell(row, 12).value:
                                warehouse_id = ware_obj.search([('code', '=', sheet.cell(row, 12).value)], limit=1)
                                warehouse_id = warehouse_id and warehouse_id.id or 0
                                if warehouse_id:
                                    vals.update({'warehouse_id': warehouse_id})

                            pack_value = sheet.cell(row, 12).value
                            if pack_value == 'B':
                                pack_value = 'Bulk'
                            elif pack_value == 'P':
                                pack_value = 'Bag'
                            packing_id = pack_obj.search([('name', '=', pack_value)], limit=1)
                            packing_id = packing_id and packing_id.id or 0
                            if packing_id:
                                vals.update({'packing_id': packing_id})

                            if sheet.cell(row, 20).value:
                                port_of_lo = del_place_obj.search([
                                    ('code', '=', sheet.cell(row, 20).value),
                                    '|', ('name', '!=', False),
                                    ('name', '=', sheet.cell(row, 20).value)], limit=1)
                                if not port_of_lo:
                                    port_of_lo = del_place_obj.create({
                                        'name': sheet.cell(row, 20).value,
                                        'code': sheet.cell(row, 20).value,
                                    })
                                    port_of_lo = port_of_lo and port_of_lo.id or 0
                                else:
                                    port_of_lo = port_of_lo and port_of_lo.id or 0
                                if port_of_lo:
                                    vals.update({'port_of_loading': port_of_lo})

                            if sheet.cell(row, 21).value:
                                port_of_dis = del_place_obj.search([
                                    ('code', '=', sheet.cell(row, 21).value),
                                    '|', ('name', '!=', False),
                                    ('name', '=', sheet.cell(row, 21).value)], limit=1)
                                if not port_of_dis:
                                    port_of_dis = del_place_obj.create({
                                        'name': sheet.cell(row, 21).value,
                                        'code': sheet.cell(row, 21).value,
                                    })
                                    port_of_dis = port_of_dis and port_of_dis.id or 0
                                else:
                                    port_of_dis = port_of_dis and port_of_dis.id or 0
                                if port_of_dis:
                                    vals.update({'port_of_discharge': port_of_dis})

                            if sheet.cell(row, 23).value:
                                vals.update({'x_p_contract_link': sheet.cell(row, 23).value or ''})

                            if sheet.cell(row, 24).value:
                                vals.update({'shipper_id': sheet.cell(row, 24).value or ''})

                            si_received_date = sheet.cell_value(row, 25) and self.map_datetime(
                                sheet.cell_value(row, 25), wb.datemode) or False
                            si_received_date = si_received_date and '%s-%s-%s' % (
                            str(si_received_date.year), str(si_received_date.month), str(si_received_date.day)) or False
                            if si_received_date:
                                vals.update({'si_received_date': si_received_date})

                            pss_send_schedule = sheet.cell_value(row, 26) and self.map_datetime(
                                sheet.cell_value(row, 26), wb.datemode) or False
                            pss_send_schedule = pss_send_schedule and '%s-%s-%s' % (
                            str(pss_send_schedule.year), str(pss_send_schedule.month),
                            str(pss_send_schedule.day)) or False
                            if pss_send_schedule:
                                vals.update({'pss_send_schedule': pss_send_schedule})

                            pss_sent_date = sheet.cell_value(row, 29) and self.map_datetime(sheet.cell_value(row, 29),
                                                                                            wb.datemode) or False
                            pss_sent_date = pss_sent_date and '%s-%s-%s' % (
                            str(pss_sent_date.year), str(pss_sent_date.month), str(pss_sent_date.day)) or False
                            if pss_sent_date:
                                vals.update({'si_sent_date': pss_sent_date})

                            pss_approved_date = sheet.cell_value(row, 28) and self.map_datetime(
                                sheet.cell_value(row, 28), wb.datemode) or False
                            pss_approved_date = pss_approved_date and '%s-%s-%s' % (
                            str(pss_approved_date.year), str(pss_approved_date.month),
                            str(pss_approved_date.day)) or False
                            if pss_approved_date:
                                vals.update({'pss_approved_date': pss_approved_date})

                            shipping_line_id = 0
                            if sheet.cell(row, 31).value:
                                try:
                                    shipping_line_id = shiping_line_obj.search(
                                        [('name', '=', sheet.cell(row, 31).value)], limit=1)

                                    if not shipping_line_id:
                                        shipping_line_id = shiping_line_obj.create({'name': sheet.cell(row, 31).value})
                                        shipping_line_id = shipping_line_id and shipping_line_id.id or 0
                                    else:
                                        shipping_line_id = shipping_line_id and shipping_line_id.id or 0
                                    if shipping_line_id:
                                        vals.update({'shipping_line_id': shipping_line_id})
                                except:
                                    pass

                            factory_etd = sheet.cell_value(row, 32) and self.map_datetime(sheet.cell_value(row, 32),
                                                                                          wb.datemode) or False
                            factory_etd = factory_etd and '%s-%s-%s' % (
                            str(factory_etd.year), str(factory_etd.month), str(factory_etd.day)) or False
                            if factory_etd:
                                vals.update({'factory_etd': factory_etd})

                            if sheet.cell_value(row, 33):
                                vals.update({'x_stuff_place': sheet.cell_value(row, 33)})

                            nominated_etd = sheet.cell_value(row, 34) and self.map_datetime(sheet.cell_value(row, 34),
                                                                                            wb.datemode) or False
                            nominated_etd = nominated_etd and '%s-%s-%s' % (
                            str(nominated_etd.year), str(nominated_etd.month), str(nominated_etd.day)) or False
                            if nominated_etd:
                                vals.update({'nominated_etd': nominated_etd})

                            bill_date = sheet.cell_value(row, 35) and self.map_datetime(sheet.cell_value(row, 35),
                                                                                        wb.datemode) or False
                            bill_date = bill_date and '%s-%s-%s' % (
                            str(bill_date.year), str(bill_date.month), str(bill_date.day)) or False
                            if bill_date:
                                vals.update({'bill_date': bill_date})

                            eta = sheet.cell_value(row, 37) and self.map_datetime(sheet.cell_value(row, 37),
                                                                                  wb.datemode) or False
                            eta = eta and '%s-%s-%s' % (str(eta.year), str(eta.month), str(eta.day)) or False
                            if eta:
                                vals.update({'eta': eta})

                            if sheet.cell(row, 38).value:
                                vals.update({'x_remark1': sheet.cell(row, 38).value})

                            if sheet.cell(row, 39).value:
                                vals.update({'x_remark2': sheet.cell(row, 39).value})

                            # late_ship_end = sheet.cell_value(row, 37) and self.map_datetime(sheet.cell_value(row, 37), wb.datemode) or False
                            # late_ship_end = late_ship_end and '%s-%s-%s' % (str(late_ship_end.year), str(late_ship_end.month), str(late_ship_end.day)) or False
                            # if late_ship_end:
                            #     vals.update({'x_remark1': late_ship_end})

                            # late_ship_est = sheet.cell_value(row, 38) and self.map_datetime(sheet.cell_value(row, 38), wb.datemode) or False
                            # late_ship_est = late_ship_est and '%s-%s-%s' % (str(late_ship_est.year), str(late_ship_est.month), str(late_ship_est.day)) or False
                            # if late_ship_est:
                            #     vals.update({'late_ship_est': late_ship_est})

                            if sheet.cell(row, 42).value:
                                if self.map_datetime(sheet.cell_value(row, 42), wb.datemode):
                                    fmyear = self.map_datetime(sheet.cell_value(row, 42), wb.datemode)
                                    remyear = '%s-%s' % (myear[fmyear.month], str(fmyear.year))
                                    smonth_idd = smonth_obj.search([('name', '=', remyear)], limit=1)
                                    smonth_idd = smonth_idd and smonth_idd.id or 0
                                    if not smonth_idd:
                                        smonth_idd = smonth_obj.create({'name': remyear})
                                        smonth_idd = smonth_idd and smonth_idd.id or 0
                                    if smonth_idd:
                                        vals.update({'contract_mship': smonth_idd})
                                else:
                                    smonth_idd = smonth_obj.search([('name', '=', sheet.cell(row, 42).value)], limit=1)
                                    smonth_idd = smonth_idd and smonth_idd.id or 0
                                    if not smonth_idd:
                                        smonth_idd = smonth_obj.create({'name': sheet.cell(row, 42).value})
                                        smonth_idd = smonth_idd and smonth_idd.id or 0
                                    if smonth_idd:
                                        vals.update({'contract_mship': smonth_idd})
                                # vals.update({'contract_mship': sheet.cell(row, 42).value})

                            od_doc_rec_date = sheet.cell_value(row, 44) and self.map_datetime(sheet.cell_value(row, 44),
                                                                                              wb.datemode) or False
                            od_doc_rec_date = od_doc_rec_date and '%s-%s-%s' % (
                            str(od_doc_rec_date.year), str(od_doc_rec_date.month), str(od_doc_rec_date.day)) or False
                            if od_doc_rec_date:
                                vals.update({'od_doc_rec_date': od_doc_rec_date})

                            od_doc_sent_date = sheet.cell_value(row, 46) and self.map_datetime(
                                sheet.cell_value(row, 46), wb.datemode) or False
                            od_doc_sent_date = od_doc_sent_date and '%s-%s-%s' % (
                            str(od_doc_sent_date.year), str(od_doc_sent_date.month), str(od_doc_sent_date.day)) or False
                            if od_doc_sent_date:
                                vals.update({'od_doc_sent_date': od_doc_sent_date})

                            exist_name = sheet.cell(row, 4).value
                            try:
                                exist_name = str(int(sheet.cell(row, 4).value))
                            except:
                                pass

                            delivery_type = False
                            try:
                                delivery_type = str(int(sheet.cell(row, 17).value))
                            except:
                                if sheet.cell(row, 17).value == 'Shipment':
                                    delivery_type = '50'
                                elif sheet.cell(row, 17).value == 'Delivery':
                                    delivery_type = '10'
                                else:
                                    delivery_type = False
                            if delivery_type:
                                vals.update({
                                    'delivery_type': delivery_type
                                })

                            if sheet.cell(row, 0).value:
                                vals.update({'status': sheet.cell(row, 0).value in lst_status and sheet.cell(row,
                                                                                                             0).value or ''})

                            if sheet.cell(row, 3).value:
                                origin = self.env['res.country'].search([
                                    ('code', '=', sheet.cell(row, 3).value)
                                ])
                                if origin:
                                    vals.update({'origin_new': origin.id})

                            if sheet.cell(row, 5).value:
                                vals.update({'client_ref': sheet.cell(row, 5).value or ''})

                            if sheet.cell(row, 7).value:
                                vals.update({'p_qty': sheet.cell(row, 7).value or 0})

                            if sheet.cell(row, 11).value:
                                vals.update({'p_quality': sheet.cell(row, 11).value or ''})

                            if sheet.cell(row, 8).value:
                                vals.update({'no_of_pack': sheet.cell(row, 8).value or 0})

                            if sheet.cell(row, 13).value:
                                vals.update({'pss_type': sheet.cell(row, 13).value or ''})

                            if sheet.cell(row, 22).value:
                                vals.update({'precalculated_freight_cost': sheet.cell(row, 22).value and float(
                                    sheet.cell(row, 22).value) or 0})

                            if sheet.cell(row, 30).value:
                                vals.update(
                                    {'freight': sheet.cell(row, 30).value and float(sheet.cell(row, 30).value) or 0})

                            if sheet.cell(row, 27).value:
                                vals.update({'pss_amount_send': sheet.cell(row, 27).value and float(
                                    sheet.cell(row, 27).value) or 0})

                            if sheet.cell(row, 36).value:
                                vals.update({'booking_ref_no': sheet.cell(row, 36).value or ''})

                            if sheet.cell(row, 40).value:
                                vals.update({'cause_by': sheet.cell(row, 40).value or ''})

                            if sheet.cell(row, 41).value:
                                vals.update({'remarks': sheet.cell(row, 41).value or ''})

                            if sheet.cell(row, 43).value:
                                vals.update({'shipment_status': sheet.cell(row, 43).value or ''})

                            if sheet.cell(row, 45).value:
                                vals.update({'od_doc_rec_awb': sheet.cell(row, 45).value or ''})

                            if sheet.cell(row, 47).value:
                                vals.update({'awb_sent_no': sheet.cell(row, 47).value or ''})

                            vals.update({
                                'name': exist_name,
                                # 'type': 'export'
                            })
                            contract_id = 0
                            contract_id = contract_obj.search([('name', '=', exist_name)], limit=1)
                            if contract_id:
                                contract_id.write(vals)
                            else:
                                contract_id = contract_obj.create(vals)

                        except Exception as e:
                            #   Note error on line number
                            lst_errors.append('\n ' + 'Row  %s : %s' % (str(nrow), str(e)))

                        # self.env['s.contract.line'].create({
                        #     'product_id': prod_id,
                        #     'certificate_id': certificate_id,
                        #     'name': sheet.cell(row, 11).value,
                        #     'packing_id': packing_id,
                        #     'product_qty': sheet.cell(row, 7).value,
                        #     'number_of_bags': sheet.cell(row, 8).value,
                        #     'product_uom': product_obj.browse(prod_id).uom_id.id,
                        #     'contract_id': contract_id.id
                        # })

                        # for ship in contract_id.shipping_ids:
                        #     ship.button_load_sc()
            if lst_errors:
                return {
                    'name': 'Error when import!',
                    'view_mode': 'form',
                    'res_model': 'popup.result.import',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {'default_name': 'Please check again these rows: %s' % str(lst_errors)},
                }
        return 1


class PopupResultImport(models.Model):
    _name = "popup.result.import"

    name = fields.Char(string='Name', size=256)
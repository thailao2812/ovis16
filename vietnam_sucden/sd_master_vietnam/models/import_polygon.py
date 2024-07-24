# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _
import base64
import xlrd
from odoo.exceptions import ValidationError, UserError
from math import radians, sin, cos, sqrt, atan2
import json


class ImportPolygon(models.Model):
    """Inherit Drawing mixins model 'google.drawing.shape'"""
    _name = 'import.polygon'

    file = fields.Binary(string='File')
    filename = fields.Char(string='Name')

    def haversine(self, lat1, lng1, lat2, lng2):
        R = 6371.0
        lat1 = radians(lat1)
        lng1 = radians(lng1)
        lat2 = radians(lat2)
        lng2 = radians(lng2)
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c * 1000
        return distance

    def import_polygon(self):
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
            value = {"type": "polygon",
                     "options": {"path": []},
                     "lines": {}
                     }
            for row in range(1, num_of_rows):
                list = []
                list1 = []
                dict1 = {}
                if sh.cell(row, 0).value:
                    clear_data = sh.cell(row, 0).value.lstrip(' ')
                    clear_data = clear_data.replace('POLYGON', '')
                    clear_data = clear_data.replace('((', '')
                    clear_data = clear_data.replace('))', '')
                    clear_data = clear_data.lstrip()
                    clear_data = clear_data.split(',')
                    for i in clear_data:
                        list.append(i.lstrip().split(' '))
                    del list[-1:]
                    for i in list:
                        lng, lat = i
                        lng = float(lng)
                        lat = float(lat)
                        d = {'lat': lat, 'lng': lng}
                        list1.append(d)
                    value['options'] = {"path": list1}
                    for i, (start, stop) in enumerate(zip(list1, list1[1:] + list1[:1])):
                        key = str(i + 1)
                        val = {'start': start, 'stop': stop, 'length': self.haversine(start['lat'], start['lng'], stop['lat'], stop['lng'])}
                        dict1[key] = val
                    value['lines'] = dict1
                create_new_polygon = self.env['res.partner.area'].create({
                    'gshape_name': 'test 1',
                    'partner_id': 18306,
                    'gshape_paths': str(value)
                })
                create_new_polygon._compute_gshape_polygon_lines()
                a = create_new_polygon.gshape_paths.replace("'", '"')
                object_json = json.loads(a)
                object_json_2 = json.loads(a)
                last_key, last_parameter = object_json_2['lines'].popitem()
                object_json['lines'][last_key]['start'], object_json['lines'][last_key]['stop'] = object_json['lines'][last_key]['stop'], object_json['lines'][last_key]['start']
                create_new_polygon.gshape_paths = str(object_json)
                create_new_polygon._compute_gshape_polygon_lines()

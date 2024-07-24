# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _
import base64
import xlrd
from odoo.exceptions import ValidationError, UserError
from math import radians, sin, cos, sqrt, atan2
from shapely.geometry import shape, Polygon, Point
from shapely.errors import GEOSException
from shapely.wkt import loads
import json,ast
from datetime import datetime,date, timedelta
from geopy.distance import geodesic
from geopy import distance
import re



class ImportGeoJson(models.Model):
    _name = 'import.geojson'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    file = fields.Binary(string='File')
    filename = fields.Char(string='Name')
    vendor_id = fields.Many2one('res.partner', string='Responsibility Person')
    country_id = fields.Many2one('res.country', string='Country')
    import_date = fields.Date(string='Import Date', default=datetime.now())
    line_ids = fields.One2many('geojson.data', 'import_id')
    state = fields.Selection([
        ('new', 'New'),
        ('imported', 'Imported')
    ], string='State', default='new')
    count_polygon = fields.Integer(string='Count Polygon')
    count_point = fields.Integer(string='Count Point')
    contact_number = fields.Char(string='Contact Number')
    supplier_id = fields.Many2one('res.partner', string='Supplier Name')
    supplier_number = fields.Char(string='Supplier Number')
    supplier_master_id = fields.Many2one('supplier.master.data')
    purchase_no = fields.Char(string='Purchase #')
    total_data = fields.Integer(string='# Geometry', compute='compute_total_date', store=True)
    status_check = fields.Selection([
        ('red', 'Red'),
        ('green', 'Green'),
    ], string='Status Check')

    @api.depends('count_polygon', 'count_point')
    def compute_total_date(self):
        for rec in self:
            rec.total_data = rec.count_polygon + rec.count_point

    def calculate_length(self, start, stop):
        return geodesic((start[1], start[0]), (stop[1], stop[0])).meters

    def count_decimal_places(self, number):
        """Return the number of decimal places in a number."""
        number_str = str(number)
        if '.' in number_str:
            return len(number_str.split('.')[1])
        else:
            return 0

    def import_file(self):
        if self.file:
            self.line_ids = [(5, )]
            # Giải mã file từ dạng base64
            file_content = base64.b64decode(self.file)
            # Chuyển đổi nội dung file thành định dạng json
            geojson_data = json.loads(file_content)
            existing_polygons = self.env['res.partner.area'].search([])
            existing_polygons_shapes = []
            for record in existing_polygons:
                try:
                    gshape_paths = json.loads(record.gshape_paths)
                    coordinates = [(point['lng'], point['lat']) for point in gshape_paths['options']['paths']]
                    existing_polygons_shapes.append(Polygon(coordinates))
                except (json.JSONDecodeError, GEOSException, KeyError) as e:
                    continue

            duplicate_count = 0
            duplicate_point_count = 0
            partial_duplicate_count = 0
            partial_duplicate_percentage_list = []
            mess = ''

            existing_points = self.env['partner.multiple.point'].search([])
            existing_points_shapes = [Point(record.partner_longitude, record.partner_latitude) for record in
                                      existing_points]
            count_point = 0
            count_polygon = 0
            for feature in geojson_data['features']:
                # Giả sử mỗi feature là một bản ghi bạn muốn tạo
                geometry = feature.get('geometry', {})
                if geometry.get('type') in ['Polygon', 'MultiPolygon']:
                    coordinates = False
                    if geometry.get('type') == 'Polygon':
                        coordinates = geometry.get('coordinates', [])[0]
                    if geometry.get('type') == 'MultiPolygon':
                        coordinates = geometry.get('coordinates', [])[0][0]
                    count_polygon += 1

                    # Chuyển đổi tọa độ thành polygon shapely
                    new_polygon = Polygon([(coord[0], coord[1]) for coord in coordinates])
                    is_duplicate = any(new_polygon.equals(existing_polygon) for existing_polygon in existing_polygons_shapes)

                    # Check for partial duplicates
                    points_in_new_polygon = [Point(coord[0], coord[1]) for coord in coordinates]
                    points_inside_existing_polygons = 0
                    buffer_radius = 0.00001
                    if duplicate_count == 0:
                        for point in points_in_new_polygon:
                            if any(existing_polygon.intersects(point.buffer(buffer_radius)) for existing_polygon in existing_polygons_shapes):
                                points_inside_existing_polygons += 1

                    total_points = len(points_in_new_polygon)
                    if points_inside_existing_polygons > 0:
                        partial_duplicate_percentage = min((points_inside_existing_polygons / total_points) * 100, 100)
                        partial_duplicate_percentage_list.append(partial_duplicate_percentage)
                        partial_duplicate_count += 1

                    paths = []
                    lines = {}
                    check_decimal = False
                    for coord in coordinates:
                        lat, lng = coord[1], coord[0]
                        lat_decimal = self.count_decimal_places(lat)
                        lng_decimal = self.count_decimal_places(lng)
                        if lat_decimal < 6 or lng_decimal < 6:
                            print(lat, lng)
                            print(lat_decimal, 'vao')
                            print(lng_decimal, 'day')
                            check_decimal = True
                            continue
                        paths.append({"lat": lat, "lng": lng})
                    if not paths:
                        self.env['geojson.data'].create({
                            'name': 'Polygon number %s' % str(count_polygon),
                            'type': 'polygon',
                            'missing_geometry': True,
                            'state_check': 'red',
                            'import_id': self.id
                        })
                        continue
                    if coordinates[0] != coordinates[-1]:
                        self.env['geojson.data'].create({
                            'name': 'Polygon number %s' % str(count_polygon),
                            'type': 'polygon',
                            'is_unclose': True,
                            'state_check': 'red',
                            'import_id': self.id
                        })
                        continue
                    if is_duplicate:
                        duplicate_count += 1
                        self.env['geojson.data'].create({
                            'name': 'Polygon number %s' % str(count_polygon),
                            'type': 'polygon',
                            'is_overlapping': True,
                            'state_check': 'red',
                            'import_id': self.id
                        })
                        continue
                    if points_inside_existing_polygons > 0:
                        self.env['geojson.data'].create({
                            'name': 'Polygon number %s' % str(count_polygon),
                            'type': 'polygon',
                            'is_duplicate_partial': True,
                            'state_check': 'red',
                            'import_id': self.id
                        })
                        continue  # Skip creating this polygon
                    if check_decimal:
                        self.env['geojson.data'].create({
                            'name': 'Polygon number %s' % str(count_polygon),
                            'type': 'polygon',
                            'decimal_precision': True,
                            'state_check': 'red',
                            'import_id': self.id
                        })
                        continue
                    for i, coord_pair in enumerate(zip(coordinates, coordinates[1:] + [coordinates[0]]), start=1):
                        start, stop = coord_pair
                        start_lat, start_lng = start[1], start[0]
                        stop_lat, stop_lng = stop[1], stop[0]
                        lines[str(i)] = {
                            "start": {"lat": start_lat, "lng": start_lng},
                            "stop": {"lat": stop_lat, "lng": stop_lng},
                            "length": self.calculate_length(start, stop)
                        }
                    new_data_format = {
                        "type": "polygon",
                        "options": {
                            "paths": paths
                        },
                        "lines": lines
                    }

                    create_new_polygon = self.env['res.partner.area'].create({
                        'gshape_name': 'Farm of %s' % self.vendor_id.name,
                        'partner_id': self.vendor_id.id,
                        'gshape_paths': new_data_format
                    })
                    create_new_polygon._compute_gshape_polygon_lines()
                    dict_obj = ast.literal_eval(create_new_polygon.gshape_paths)
                    create_new_polygon.gshape_paths = json.dumps(dict_obj)
                    create_new_polygon._compute_gshape_polygon_lines()
                    create_new_polygon.import_id = self.id
                    self.count_polygon += 1
                    self.env['geojson.data'].create({
                        'name': 'Polygon number %s' % str(count_polygon),
                        'type': 'polygon',
                        'import_id': self.id,
                        'state_check': 'green'
                    })
                if geometry.get('type') == 'Point':
                    count_point += 1
                    multiple_point = self.env['partner.multiple.point']
                    coordinates = geometry.get('coordinates', [])
                    lat, lng = coordinates[1], coordinates[0]
                    new_point = Point(lng, lat)
                    is_duplicate = any(new_point.equals(existing_point) for existing_point in existing_points_shapes)
                    if is_duplicate:
                        duplicate_point_count += 1
                        self.env['geojson.data'].create({
                            'name': 'Point number %s' % str(count_point),
                            'type': 'point',
                            'is_overlapping': True,
                            'state_check': 'red',
                            'import_id': self.id
                        })
                        continue
                    self.env['geojson.data'].create({
                        'name': 'Point number %s' % str(count_point),
                        'type': 'point',
                        'import_id': self.id,
                        'state_check': 'green'
                    })
                    multiple_point.create({
                        'partner_id': self.vendor_id.id,
                        'partner_latitude': lat,
                        'partner_longitude': lng,
                        'import_id': self.id
                    })
                    self.count_point += 1
            if duplicate_count > 0:
                mess += "We have %s Polygon that have the same data that already stored in database, in your file, please check again!<br/>" % duplicate_count
            if duplicate_point_count > 0:
                mess += "We have %s Point that have the same data that already stored in database, in your file, please check again!<br/>" % duplicate_point_count
            if partial_duplicate_count > 0:
                mess += "We have %s Polygon that contains points already stored in the database. Please check again!<br/>" % partial_duplicate_count
                for i, percentage in enumerate(partial_duplicate_percentage_list, 1):
                    mess += "Polygon %s contains %.2f%% points already stored in the database.<br/>" % (i, percentage)
            if mess:
                self.message_post(body=mess)
            if any(self.line_ids.mapped('is_duplicate_partial')) or any(self.line_ids.mapped('is_overlapping')) or any(self.line_ids.mapped('is_unclose')) or any(self.line_ids.mapped('missing_geometry')) or any(self.line_ids.mapped('decimal_precision')):
                self.status_check = 'red'
            else:
                self.status_check = 'green'
            self.state = 'imported'
            self.import_date = datetime.now()

    def _get_action_view_polygon(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env["ir.actions.actions"]._for_xml_id("contacts_area.action_res_partner_area")
        partner_area = self.env['res.partner.area'].search([
            ('partner_id', '=', self.vendor_id.id),
            ('import_id', '=', self.id)
        ])
        if partner_area:
            action['domain'] = [
                ('partner_id', 'in', partner_area.mapped('partner_id').ids)
            ]
        return action

    def _get_action_view_point(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env["ir.actions.actions"]._for_xml_id("sd_master_ned.action_view_res_partner_multiple_google_map")
        multiple_point = self.env['partner.multiple.point'].search([
            ('partner_id', '=', self.vendor_id.id),
            ('import_id', '=', self.id)
        ])
        if multiple_point:
            action['domain'] = [
                ('id', 'in', multiple_point.ids)
            ]
        return action

    def open_view_polygon(self):
        return self._get_action_view_polygon()

    def open_view_point(self):
        return self._get_action_view_point()

    @api.model
    def default_get(self, fields):
        res = super(ImportGeoJson, self).default_get(fields)
        context = self.env.context
        if 'partner_id' in context:
            partner = self.env['res.partner'].browse(self.env.context.get('partner_id'))
            res['supplier_id'] = partner.id
        return res


class GeoJSonData(models.Model):
    _name = 'geojson.data'

    import_id = fields.Many2one('import.geojson')
    name = fields.Char(string='Name')
    type = fields.Selection([
        ('point', 'Point'),
        ('polygon', 'Polygon')
    ], string='Type', default=None)
    is_duplicate_partial = fields.Boolean(string='Is Duplicate Partial')
    is_overlapping = fields.Boolean(string='Is Overlapping')
    is_unclose = fields.Boolean(string='UnClosed Polygon')
    missing_geometry = fields.Boolean(string='Missing Geometry')
    decimal_precision = fields.Boolean(string='Decimal Precision')
    state_check = fields.Selection([
        ('red', 'Red'),
        ('green', 'Green')
    ], string='Status Check')
# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _
import base64
import numpy as np

from shapely.geometry import shape, Polygon, Point
from shapely.errors import GEOSException
from shapely.wkt import loads
import json,ast
from datetime import datetime,date, timedelta
from geopy.distance import geodesic

import json
import pandas as pd
from rasterstats import zonal_stats
import os
import glob

from odoo.exceptions import UserError

# merge_layer_tif_filepath_vn = "/Users/laoquocthai/VNM_Regions_Crop"
# merge_layer_tif_filepath_col = "/Users/laoquocthai/COL_Regions_Crop"
# merge_layer_tif_filepath_bra = "/Users/laoquocthai/BRA_Regions_Crop"
merge_layer_tif_filepath_vn = "/opt/VNM_Regions_Crop"
merge_layer_tif_filepath_col = "/opt/COL_Regions_Crop"
merge_layer_tif_filepath_bra = "/opt/BRA_Regions_Crop"


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
    properties_ids = fields.Many2many('properties.polygon')

    @api.depends('count_polygon', 'count_point')
    def _compute_total_data(self):
        for rec in self:
            rec.total_data = rec.count_polygon + rec.count_point

    def get_layers_in_folder(self, folder_name):
        """Retrieve layer files from a specified folder."""
        return glob.glob(os.path.join(folder_name, "*.tif"))

    def count_decimal_places(self, number):
        """Return the number of decimal places in a number."""
        number_str = str(number)
        return len(number_str.split('.')[1]) if '.' in number_str else 0

    def calculate_length(self, start, stop):
        """Calculate the geodesic distance between two points."""
        return geodesic((start[1], start[0]), (stop[1], stop[0])).meters

    def calculate_angle(self, coordinate_1, coordinate_2, coordinate_3):
        """Calculate the angle at coordinate_2 given points coordinate_1, coordinate_2, and coordinate_3."""
        vector_1 = np.array(coordinate_1) - np.array(coordinate_2)
        vector_2 = np.array(coordinate_3) - np.array(coordinate_2)
        cosine_angle = np.dot(vector_1, vector_2) / (np.linalg.norm(vector_1) * np.linalg.norm(vector_2))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))  # Clip to handle floating-point errors
        return np.degrees(angle)

    def check_angle(self, geom, minimum_angle_degree):
        """Check if any angle in the polygon geometry is less than the specified minimum angle degree."""
        try:
            if geom.geom_type == "MultiPolygon":
                geom = geom.convex_hull

            vertices = list(geom.exterior.coords)[:-1]  # Exclude the last point as it duplicates the first
            num_points = len(vertices)

            angles = [
                self.calculate_angle(vertices[i - 1], vertices[i], vertices[(i + 1) % num_points])
                for i in range(num_points)
            ]
            return any(angle < minimum_angle_degree for angle in angles)

        except Exception:
            return True

    def checking_deforestation(self, geometry, country):
        """Check deforestation percentage based on geometry and country."""
        region_layer_paths = False
        if country.code == 'VN':
            region_layer_paths = self.get_layers_in_folder(merge_layer_tif_filepath_vn)
        if country.code == 'CO':
            region_layer_paths = self.get_layers_in_folder(merge_layer_tif_filepath_col)
        if country.code == 'BR':
            region_layer_paths = self.get_layers_in_folder(merge_layer_tif_filepath_bra)
        if not region_layer_paths:
            # raise UserError(f"No layer files found for country {country.name}.")
            return 0
        for layer_path in region_layer_paths:
            stats = zonal_stats(geometry, layer_path, stats=["max", "sum", "count"])
            if stats:
                total_pixels, sum_overlap_pixels = stats[0]["count"], stats[0]["sum"]
                if sum_overlap_pixels:
                    overlap_percentage = round((sum_overlap_pixels - total_pixels) * 100 / total_pixels, 1)
                    return overlap_percentage
        return 0

    def import_file(self):
        """Import GeoJSON file and process geometries."""
        if not self.file:
            return

        # Decode the file and load GeoJSON data
        self.line_ids = [(5,)]
        file_content = base64.b64decode(self.file)
        geojson_data = json.loads(file_content)

        # Cache for existing polygons and points to avoid duplicate checks
        existing_polygons = self.env['res.partner.area'].search([])
        existing_polygons_shapes = []
        for record in existing_polygons:
            try:
                gshape_paths = json.loads(record.gshape_paths)
                coordinates = [(point['lng'], point['lat']) for point in gshape_paths['options']['paths']]
                existing_polygons_shapes.append(Polygon(coordinates))
            except (json.JSONDecodeError, GEOSException, KeyError) as e:
                continue

        existing_points = self.env['partner.multiple.point'].search([])
        existing_points_shapes = [Point(record.partner_longitude, record.partner_latitude) for record in
                                  existing_points]

        # Cache for properties to reduce database hits
        properties_cache = {prop.name: prop.id for prop in self.env['properties.polygon'].search([])}

        line_data = []
        count_point, count_polygon = 0, 0

        for feature in geojson_data['features']:
            geometry = feature.get('geometry', {})
            properties = feature.get('properties', {})

            # Process properties
            for line in properties:
                line_name = line.strip()
                if line_name not in properties_cache:
                    new_prop = self.env['properties.polygon'].create({'name': line_name})
                    properties_cache[line_name] = new_prop.id
                self.properties_ids = [(4, properties_cache[line_name])]

            if geometry.get('type') in ['Polygon', 'MultiPolygon']:
                coordinates = geometry.get('coordinates', [])[0] if geometry.get('type') == 'Polygon' else \
                geometry.get('coordinates', [])[0][0]
                new_polygon = Polygon(coordinates)

                is_duplicate = any(new_polygon.equals(existing_polygon) for existing_polygon in existing_polygons_shapes)
                count_polygon += 1
                if self.country_id.code in ['BR', 'CO', 'VN']:
                    deforestation_percent = self.checking_deforestation(new_polygon, self.country_id)
                else:
                    deforestation_percent = 0
                check_spike = self.check_angle(new_polygon, 1)
                less_4_point = len(coordinates) < 4
                un_close = coordinates and coordinates[0] != coordinates[-1]
                check_decimal = any(
                    self.count_decimal_places(coord[0]) < 6 or self.count_decimal_places(coord[1]) < 6 for coord in
                    coordinates)

                line_entry = {
                    'name': f'Polygon number {count_polygon}',
                    'type': 'polygon',
                    'missing_geometry': not coordinates,
                    'spike': check_spike,
                    'points_check': less_4_point,
                    'is_unclose': un_close,
                    'decimal_precision': check_decimal,
                    'is_duplicate_partial': False,
                    'is_overlapping': is_duplicate,
                    'deforestation_percentage': deforestation_percent if deforestation_percent > 5 else 0,
                    'state_check': 'red' if (
                                not coordinates or less_4_point or check_spike or un_close or is_duplicate or check_decimal or deforestation_percent > 5) else 'green',
                    'import_id': self.id,
                    'properties_data': json.dumps(properties)
                }
                line_data.append(line_entry)

            elif geometry.get('type') == 'Point':
                coordinates = geometry.get('coordinates', [])
                count_point += 1
                lat, lng = coordinates[1], coordinates[0]
                new_point = Point(lng, lat)
                check_decimal = self.count_decimal_places(lat) < 6 or self.count_decimal_places(lng) < 6
                is_duplicate = any(new_point.equals(existing_point) for existing_point in existing_points_shapes)

                line_entry = {
                    'name': f'Point number {count_point}',
                    'type': 'point',
                    'is_overlapping': is_duplicate,
                    'decimal_precision': check_decimal,
                    'state_check': 'red' if is_duplicate or check_decimal else 'green',
                    'import_id': self.id,
                    'properties_data': json.dumps(properties)
                }
                line_data.append(line_entry)

        # Batch create `geojson.data` entries
        self.env['geojson.data'].create(line_data)

        # Update status check based on `state_check` values in `line_data`
        self.status_check = 'red' if any(line['state_check'] == 'red' for line in line_data) else 'green'
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

    def open_wizard_export_error(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Export Error',
            'view_mode': 'form',
            'res_model': 'wizard.export.error',
            'view_id': self.env.ref('sd_master_ned.wizard_export_error').id,
            'target': 'new',  # Mở wizard trong modal pop-up
        }


class GeoJSonData(models.Model):
    _name = 'geojson.data'

    import_id = fields.Many2one('import.geojson', ondelete='cascade')
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
    spike = fields.Boolean(string='Spikes')
    points_check = fields.Boolean(string='Less than 4 points')
    state_check = fields.Selection([
        ('red', 'Red'),
        ('green', 'Green')
    ], string='Status Check')
    properties_data = fields.Char(string='Properties Data')
    deforestation_percentage = fields.Float(string='Deforestation Percentage', digits=(16, 1))
    data = fields.Char(string='Data')
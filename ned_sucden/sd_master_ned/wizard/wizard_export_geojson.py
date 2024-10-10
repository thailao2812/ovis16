# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import json
import base64


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class WizardExportGeojson(models.TransientModel):
    _name = "wizard.export.geojson"

    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    partner_id = fields.Many2one('res.partner')
    country_id = fields.Many2one('res.country', string='Country')
    contract_number = fields.Char(string='Contract Number')
    geojson_file = fields.Binary(string="GeoJSON File")

    def truncate_to_six_digits(self, value):
        """Helper method to truncate value to 6 decimal places without rounding."""
        return float(str(value)[:str(value).find('.') + 7])

    def df_to_geojson(self, properties, lat='latitude', lon='longitude'):
        geojson = {'type': 'FeatureCollection', 'features': []}
        for _, row in self.iterrows():
            feature = {'type': 'Feature',
                       'properties': {},
                       'geometry': {'type': 'Point',
                                    'coordinates': []}}
            lng = self.truncate_to_six_digits(row[lon])
            lat = self.truncate_to_six_digits(row[lat])
            feature['geometry']['coordinates'] = [lng, lat]
            for prop in properties:
                feature['properties'][prop] = row[prop]
            geojson['features'].append(feature)
        return geojson

    def generate_report(self):
        if not self.date_from and self.date_to:
            raise UserError(_("You have to fulfillment date to and date from before generate data"))
        if self.date_from and not self.date_to:
            raise UserError(_("You have to fulfillment date to and date from before generate data"))
        domain = []
        if self.date_from and self.date_to:
            domain += [('create_date', '>=', self.date_from), ('create_date', '<=', self.date_to)]
        if self.partner_id:
            domain += [('partner_id', '=', self.partner_id.id)]
        if self.country_id:
            domain += [('import_id.country_id', '=', self.country_id.id)]
        if self.contract_number:
            domain += [('import_id.purchase_no', '=', self.contract_number.strip())]
        areas = self.env['res.partner.area'].search(domain)
        # Initialize an empty list to store GeoJSON features
        features = []

        # Loop through each area to extract polygon data
        for row in areas:
            feature = {
                "type": "Feature",    "properties": {
                    "ID": f"{row.id}",
                    "ProducerCountry": self.country_id.code
                },
                "geometry": {
                    "type": "Polygon" if row.type_geometry == 'polygon' else 'Point',
                }
            }
            # Append each feature to the features list
            data = json.loads(row.gshape_paths)
            if row.type_geometry == 'polygon':
                # Create a GeoJSON feature for each polygon
                feature["geometry"]["coordinates"] = [[
                            [self.truncate_to_six_digits(point["lng"]), self.truncate_to_six_digits(point["lat"])] for point
                            in data["options"]["paths"]
                        ]]
            if row.type_geometry == 'point':
                point = data["options"]["center"]
                feature["geometry"]["coordinates"] = [self.truncate_to_six_digits(point["lng"]), self.truncate_to_six_digits(point["lat"])]
            features.append(feature)
        # Create the final GeoJSON structure with all features
        geojson_data = {
            "type": "FeatureCollection",
            "features": features
        }

        # Convert the GeoJSON structure to a string and encode it to base64
        geojson_str = json.dumps(geojson_data, indent=4)
        self.geojson_file = base64.b64encode(geojson_str.encode('utf-8'))

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=wizard.export.geojson&id={self.id}&field=geojson_file&download=true&filename=Polygon_%s.geojson' % self.country_id.code,
            'target': 'self',
        }
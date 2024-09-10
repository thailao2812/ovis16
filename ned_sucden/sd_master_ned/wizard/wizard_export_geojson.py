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
    geojson_file = fields.Binary(string="GeoJSON File")

    def df_to_geojson(self, properties, lat='latitude', lon='longitude'):
        geojson = {'type': 'FeatureCollection', 'features': []}
        for _, row in self.iterrows():
            feature = {'type': 'Feature',
                       'properties': {},
                       'geometry': {'type': 'Point',
                                    'coordinates': []}}
            feature['geometry']['coordinates'] = [row[lon], row[lat]]
            for prop in properties:
                feature['properties'][prop] = row[prop]
            geojson['features'].append(feature)
        return geojson

    def generate_report(self):
        if not self.date_from and self.date_to:
            raise UserError(_("You have to fulfillment date to and date from before generate data"))
        if self.date_from and not self.date_to:
            raise UserError(_("You have to fulfillment date to and date from before generate data"))
        area = self.env['res.partner.area'].search([])
        for row in area:
            print(row.gshape_paths)
            print(type(row.gshape_paths))
            data = json.loads(row.gshape_paths)
            geojson_data = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [point["lng"], point["lat"]] for point in data["options"]["paths"]
                            ]]
                        },
                        "properties": {
                            "description": "Polygon from paths"
                        }
                    }
                ]
            }
            geojson_str = json.dumps(geojson_data, indent=4)
            self.geojson_file = base64.b64encode(geojson_str.encode('utf-8'))
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/?model=wizard.export.geojson&id={self.id}&field=geojson_file&download=true&filename=output.geojson',
                'target': 'self',
            }

            # lat = 'latitude'
            # lon = 'longitude'
            # feature = {'type': 'Feature',
            #            'properties': {},
            #            'geometry': {'type': 'Polygon',
            #                         'coordinates': []}}
            # feature['geometry']['coordinates'] = [row[lon], row[lat]]
            # for point in row.gshape_paths["options"]["paths"]:
            #     lat = point["lat"]
            #     lng = point["lng"]
            #     print(f"Lat: {lat}, Lng: {lng}")
            # for prop in properties:
            #     feature['properties'][prop] = row[prop]
            # geojson['features'].append(feature)


        return True
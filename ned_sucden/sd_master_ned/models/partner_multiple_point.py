# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PartnerMultiplePoint(models.Model):
    _name = 'partner.multiple.point'

    partner_id = fields.Many2one('res.partner')
    contact_address = fields.Char(string='Contact Address', related='partner_id.contact_address', store=True)
    display_name = fields.Char(string='Display Name', related='partner_id.display_name', store=True)
    partner_latitude = fields.Float(string='Geo Latitude', digits=(10, 7))
    partner_longitude = fields.Float(string='Geo Longitude', digits=(10, 7))
    marker_color = fields.Integer(string='Marker Color', default=1)
    import_id = fields.Many2one('import.geojson', string='Import ID')
    gplace_id = fields.Char(
        string='Place ID',
        help='A textual identifier that uniquely identifies a place',
    )
    gplace_url = fields.Char(string='Place URL')
    gplace_opening_hours = fields.Text(string='Opening Hours')
    gplace_type_ids = fields.Many2many(
        comodel_name='google.places.type',
        column1='address_id',
        column2='place_type',
        string='Types',
    )
    gplace_plus_code_global = fields.Char(string='Global Code')
    gplace_plus_code_compound = fields.Char(string='Compound Code')
    gplace_plus_code_url = fields.Char(
        compute='compute_gplace_plus_url', string='PLus code URL'
    )
    gplace_vicinity = fields.Char(
        string='Vicinity',
        help='A simplified address for the place, '
             'including the street name, street number, '
             'and locality, but not the province/state, '
             'postal code, or country',
    )
    gplace_photos_url = fields.Text(string='Photos')

    def _prepare_geolocation_fields(self, odoo_fields, location_dict):
        values = {}
        if (
            odoo_fields.get('lat')
            and location_dict.get('lat')
            and odoo_fields.get('lng')
            and location_dict.get('lng')
        ):
            values[odoo_fields['lat']] = location_dict['lat']
            values[odoo_fields['lng']] = location_dict['lng']

        return values

    def _prepare_address_fields(self, address_components, mode='create'):
        odoo_fields = self._get_mapping_odoo_fields()
        google_address = self.env['res.country'].prepare_google_address(
            address_components, odoo_fields
        )

        if mode == 'create':
            if google_address.get('country_id'):
                google_address['country_id'] = google_address['country_id'][0]
            if google_address.get('state_id'):
                google_address['state_id'] = google_address['state_id'][0]

        return google_address

    def _get_mapping_odoo_fields(self):
        '''Mapping odoo fields
        key: alias
        value: odoo fields
        '''
        return {
            'name': 'name',
            'street': 'street',
            'street2': 'street2',
            'city': 'city',
            'zip': 'zip',
            'state_id': 'state_id',
            'country_id': 'country_id',
            'lat': 'partner_latitude',
            'lng': 'partner_longitude',
            'phone': 'phone',
            'website': 'website',
        }

    @api.model
    def action_google_place_quick_create(self, place_dict):
        place_id = place_dict.get('gplace_id')
        exists = False
        if place_id:
            values = {}
            record_count = self.search_count([('gplace_id', '=', place_id)], limit=1)
            if record_count:
                exists = True
        else:
            values = self.default_get(self._fields.keys())

        place = place_dict.get('place')
        address_components = place.get('address_components')
        location = (place.get('geometry') or {}).get('location') or {}
        place.pop('photos', None)
        places_value = place_dict.get('values') or {}
        values.update(places_value)

        if values.get('gplace_type_ids'):
            gplace_type_ids = values['gplace_type_ids'].get('resIds') or []
            values['gplace_type_ids'] = [(6, 0, gplace_type_ids)]

        odoo_fields = self._get_mapping_odoo_fields()
        if place:
            if odoo_fields.get('name') and place.get('name'):
                values[odoo_fields['name']] = place['name']

            if odoo_fields.get('website') and place.get('website'):
                values[odoo_fields['website']] = place['website']

            if odoo_fields.get('phone') and place.get('international_phone_number'):
                values[odoo_fields['phone']] = place['international_phone_number']

            # address
            if address_components:
                address_values = self._prepare_address_fields(address_components)
                values.update(address_values)

            # geolocation
            if location:
                geo_values = self._prepare_geolocation_fields(odoo_fields, location)
                values.update(geo_values)

            if values.get('gplace_photos_url') and 'image_1920' in self._fields:
                photos = values['gplace_photos_url'].split(',')
                image = self._google_get_place_image(photos[0])
                if image:
                    values['image_1920'] = image

        if exists:
            return values

        default_values = {}
        for key, val in values.items():
            default_values['default_{}'.format(key)] = val

        return default_values

    def button_view_google_map(self):
        action = self.env.ref('sd_master_ned.action_view_res_partner_multiple_google_map').read()[0]
        # action['domain'] = [('id', '=', self.partner_id.id)]
        return action

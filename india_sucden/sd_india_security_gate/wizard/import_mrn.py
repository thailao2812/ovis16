# -*- coding: utf-8 -*-
"""Bulk import of Material Receipt Notes from the Excel export.

One row is one MRN. The sheet is the export of the MRN list view, so its
columns are the field labels of ``stock.picking``:

    A Reference          -> note          (text only; the MRN keeps its own number)
    B Contact            -> partner_id    (matched by name)
    C Estate Name        -> ignored       (it is a related field shown from the
                                            partner, and cannot be written here)
    D Date of Transfer   -> date_done
    E Vehicle No.        -> vehicle_no
    F Packing            -> the move line's product, matched by the code that
                            opens the cell: "15002 PP Bags" -> default_code 15002
    G Bag                -> the move line's bag_no

Each MRN is built the way the screen builds it -- one move line, quantity
zero, the bag count on the line -- and then validated through the same button
the screen uses, so it ends up ``done`` exactly like the 4,000 already there.

The operation type is never chosen by the user: it is the ``material_in`` type
of the selected warehouse. The MRN number is left to the sequence; the row's
own reference goes into the note where the existing records already keep it.
"""
import base64
import logging
import re

import xlrd

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Column positions in the sheet, zero based.
COL_REFERENCE, COL_CONTACT, COL_ESTATE, COL_DATE, COL_VEHICLE, COL_PACKING, COL_BAG = range(7)


class ImportMRN(models.TransientModel):
    _name = 'import.mrn'
    _description = 'Import Material Receipt Notes'

    file = fields.Binary(string='File', required=True, help='The Excel export of MRN lines.')
    file_name = fields.Char(string='File name')
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse', required=True,
        default=lambda self: self.env['stock.warehouse'].search([('code', '=', 'KSNG')], limit=1),
        help='Every MRN in the file is created in this warehouse, using its '
             'Material Receipt operation type.')

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------
    def _picking_type(self):
        picking_type = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', self.warehouse_id.id),
            ('code', '=', 'material_in'),
            ('active', '=', True),
        ], limit=1)
        if not picking_type:
            raise UserError(_(
                'Warehouse %s has no "Material In" operation type. '
                'Create one before importing.') % self.warehouse_id.display_name)
        return picking_type

    @api.model
    def _find_partner(self, name, row_no):
        """Match on the name, case and surrounding spaces ignored.

        More than one partner with the same name is refused rather than guessed
        at: the bags will be booked against whoever is picked, so it has to be
        a person's decision. Archiving the duplicate is the usual fix.
        """
        cleaned = (name or '').strip()
        if not cleaned:
            raise UserError(_('Row %s: the Contact is empty.') % row_no)
        partners = self.env['res.partner'].search([
            ('name', '=ilike', cleaned), ('active', '=', True)])
        if not partners:
            raise UserError(_('Row %s: no partner named "%s".') % (row_no, cleaned))
        if len(partners) > 1:
            raise UserError(_(
                'Row %s: %s partners are named "%s" (ids %s). '
                'Archive the wrong one and import again.'
            ) % (row_no, len(partners), cleaned, ', '.join(map(str, partners.ids))))
        return partners

    @api.model
    def _find_product(self, packing, row_no):
        """The code is whatever opens the cell: "15002 PP Bags" -> 15002."""
        match = re.match(r'\s*(\d+)', str(packing or ''))
        if not match:
            raise UserError(_(
                'Row %s: cannot read a product code from Packing "%s". '
                'Expected something like "15002 PP Bags".') % (row_no, packing))
        code = match.group(1)
        products = self.env['product.product'].search([
            ('default_code', '=', code), ('active', '=', True)])
        if not products:
            raise UserError(_('Row %s: no product with code %s.') % (row_no, code))
        if len(products) > 1:
            raise UserError(_('Row %s: %s products share the code %s.') % (row_no, len(products), code))
        return products

    @staticmethod
    def _cell_datetime(sheet, row, col, book, row_no):
        cell = sheet.cell(row, col)
        if cell.ctype == xlrd.XL_CELL_DATE:
            return xlrd.xldate.xldate_as_datetime(cell.value, book.datemode)
        if cell.ctype == xlrd.XL_CELL_EMPTY or cell.value in ('', None):
            return False
        raise UserError(_(
            'Row %s: "Date of Transfer" is not a date (%s). '
            'Format the column as a date in Excel.') % (row_no, cell.value))

    @staticmethod
    def _cell_number(sheet, row, col, row_no, label):
        value = sheet.cell(row, col).value
        if value in ('', None):
            raise UserError(_('Row %s: %s is empty.') % (row_no, label))
        try:
            return float(value)
        except (TypeError, ValueError):
            raise UserError(_('Row %s: %s must be a number, got "%s".') % (row_no, label, value))

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------
    def action_import(self):
        self.ensure_one()
        try:
            book = xlrd.open_workbook(file_contents=base64.b64decode(self.file))
        except Exception as error:
            raise UserError(_('The file could not be read as Excel: %s') % error)
        sheet = book.sheet_by_index(0)
        if sheet.ncols < 7:
            raise UserError(_(
                'The sheet has %s columns; seven are expected '
                '(Reference, Contact, Estate Name, Date of Transfer, '
                'Vehicle No., Packing, Bag).') % sheet.ncols)

        picking_type = self._picking_type()
        location_src = picking_type.default_location_src_id
        location_dest = picking_type.default_location_dest_id
        if not location_src or not location_dest:
            raise UserError(_(
                'Operation type %s has no default source or destination location.'
            ) % picking_type.display_name)

        # Resolve every row before creating anything, so a bad row on line 600
        # does not leave 599 MRNs behind: the whole file goes in or none of it.
        rows = []
        for row in range(1, sheet.nrows):
            row_no = row + 1
            reference = str(sheet.cell(row, COL_REFERENCE).value or '').strip()
            if not reference and not sheet.cell(row, COL_CONTACT).value:
                continue    # trailing blank line
            rows.append({
                'row_no': row_no,
                'reference': reference,
                'partner': self._find_partner(sheet.cell(row, COL_CONTACT).value, row_no),
                'date': self._cell_datetime(sheet, row, COL_DATE, book, row_no),
                'vehicle': str(sheet.cell(row, COL_VEHICLE).value or '').strip(),
                'product': self._find_product(sheet.cell(row, COL_PACKING).value, row_no),
                'bags': self._cell_number(sheet, row, COL_BAG, row_no, 'Bag'),
            })
        if not rows:
            raise UserError(_('The sheet has no data rows.'))

        Picking = self.env['stock.picking'].with_context(material_in=True)
        MoveLine = self.env['stock.move.line']
        created = self.env['stock.picking']
        for data in rows:
            picking = Picking.create({
                'picking_type_id': picking_type.id,
                'warehouse_id': self.warehouse_id.id,
                'location_id': location_src.id,
                'location_dest_id': location_dest.id,
                'partner_id': data['partner'].id,
                'note': data['reference'],
                'vehicle_no': data['vehicle'] or False,
                'scheduled_date': data['date'] or fields.Datetime.now(),
                'date_done': data['date'] or False,
                'origin': self.file_name or False,
            })
            # No move_id on purpose: Odoo creates the stock.move from the line,
            # which is how the screen does it and what every existing MRN has.
            MoveLine.create({
                'picking_id': picking.id,
                'product_id': data['product'].id,
                'product_uom_id': data['product'].uom_id.id,
                'location_id': location_src.id,
                'location_dest_id': location_dest.id,
                'company_id': picking.company_id.id,
                'date': data['date'] or fields.Datetime.now(),
                'bag_no': data['bags'],
                'qty_done': 0.0,
                'reserved_uom_qty': 0.0,
                'weighbridge': 0.0,
            })
            created |= picking

        # Same path as the Validate button on the form. It marks the picking
        # and its moves done directly, which is why the existing MRNs are done
        # with zero quantities and why the date from the file survives.
        created.button_sd_validate()

        _logger.info('Imported %s MRN(s) into %s from %s by %s',
                     len(created), self.warehouse_id.code, self.file_name, self.env.user.login)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Imported Material Receipt Notes'),
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created.ids)],
            'context': {'material_in': True},
        }

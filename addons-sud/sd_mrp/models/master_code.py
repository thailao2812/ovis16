# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime

class MasterCode(models.Model):
    _name = 'master.code'
    _desrciption = 'Master Code'
    
    name = fields.Char(string="Master Code", required=True, )
    type_code = fields.Char(string="Type", )
    remarks = fields.Text(string="Remarks", )
    
    def button_fix_onhand(self):
        admin_uid = self.env.ref('base.user_admin').id
        if self.env.user.id not in (SUPERUSER_ID, admin_uid):
            raise UserError(_("Only Administrator can do this action."))
        warehouse_ids = []
        for report in self:
            if report.warehouse_ids:
                warehouse_ids = report.warehouse_ids.ids

        where = ''
        location_ids = self.env['stock.location']
        location_ids |= self.env['stock.location'].search(
            [('location_id', 'child_of', self.location_ids.ids),
             ('usage', '=', 'internal')])

        if len(warehouse_ids):
            where += ' and loc.warehouse_id in (%s)' % (','.join(map(str, warehouse_ids)))
        if len(location_ids):
            where += ' and loc.id in (%s)' % (
                ','.join(map(str, location_ids.ids)))
            
        
        product_ids = []
        for report in self:
            if report.product_ids:
                product_ids = report.product_ids.ids
        if len(product_ids):
            # where += ' AND pp.id in (%s)'%(','.join(map(str, [x.id for x in report.product_ids])))
            where += report.product_ids and ' and sml.product_id in (%s)' % (
                ','.join(map(str, product_ids))) or ''

        sql_fix_internal_locations = '''
                UPDATE stock_quant quant
                SET quantity = foo.start_onhand_qty,
                    reserved_quantity = foo.reserved_qty
                    --virtual_available = foo.start_onhand_qty - foo.reserved_qty
                FROM (
                    SELECT begin.location_id, begin.product_id, begin.lot_id,
                        sum(begin.start_in_qty - begin.start_out_qty) start_onhand_qty,
                        sum(begin.reserved_qty) reserved_qty
                    FROM (
                        -- IN Transations (lay stock move line truoc ngay start date cua ky xem bao cao)
                        SELECT
                            loc.id location_id, sml.product_id, sml.lot_id,
                            sum(sml.product_qty_done) start_in_qty,
                            0.0 start_out_qty,
                            0.0 reserved_qty

                        FROM stock_move_line sml
                            JOIN stock_move stm ON stm.id = sml.move_id
                            JOIN stock_location loc ON loc.id = sml.location_dest_id
                        WHERE sml.state = 'done'
                            AND loc.usage = 'internal'
                            %(where)s
                            AND stm.date < CURRENT_TIMESTAMP
                        GROUP BY loc.id, sml.product_id, sml.lot_id

                        UNION ALL

                        -- OUT Transations (lay stock move line truoc ngay start date cua ky xem bao cao)
                        SELECT
                            loc.id location_id, sml.product_id, sml.lot_id,
                            0.0 start_in_qty,
                            sum(sml.product_qty_done) start_out_qty,
                            0.0 reserved_qty
                        FROM stock_move_line sml
                            JOIN stock_move stm ON stm.id = sml.move_id
                            JOIN stock_location loc ON loc.id = sml.location_id
                        WHERE sml.state = 'done'
                            AND loc.usage = 'internal'
                            %(where)s
                            AND stm.date < CURRENT_TIMESTAMP
                        GROUP BY loc.id, sml.product_id, sml.lot_id

                        UNION

                        -- Lấy giao dịch xuất kho o trang thai Ready
                        SELECT loc.id location_id, sml.product_id, sml.lot_id,
                            0.0 start_in_qty,
                            0.0 start_out_qty,
                            SUM(CASE WHEN sp.state = 'assigned' THEN coalesce(NULLIF(sml.product_qty_done, 0), sml.product_uom_qty)
                                ELSE 0.0 END) AS reserved_qty
                        FROM stock_move_line sml
                            JOIN stock_picking sp ON sml.picking_id = sp.id
                            JOIN stock_location loc ON loc.id = sml.location_id
                        WHERE  sp.state in ('assigned')
                            AND loc.usage != 'transit'
                            %(where)s
                        GROUP BY loc.id, sml.product_id, sml.lot_id
                    ) begin
                    GROUP BY begin.location_id, begin.product_id, begin.lot_id
                ) foo
                WHERE quant.product_id = foo.product_id and quant.location_id = foo.location_id 
                AND ((foo.lot_id is null and quant.lot_id is null) or (foo.lot_id = quant.lot_id));
                COMMIT;
            ''' % ({'where': where})
        print(sql_fix_internal_locations)
        self.env.cr.execute(sql_fix_internal_locations)

    
    
    
    
    
    


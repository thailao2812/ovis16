# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class VShipment(models.Model):
    _inherit = 'v.shipment'

    quality_type = fields.Selection([
        ('wet', 'Wet'),
        ('clean', 'Clean'),
        ('std', 'STD')
    ], string='Quality Type', default=None)
    # progress_qty = fields.Float(string='Progress')
    # pending_qty = fields.Float(string='Pending')
    # production_progress = fields.Float(string='QC Approved', digits=(12, 0))
    rejected_nestle = fields.Float(string='PSS rejected Nestle', digits=(12, 0))
    approved_nestle = fields.Float(string='PSS Approved Nestle', digits=(12, 0))

    def init(self):
        self.fun_week_num_year()
        tools.drop_view_if_exists(self.env.cr, 'v_shipment')
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW public.v_shipment AS
            SELECT row_number() OVER (

                ORDER BY (

                    sc.name,
                    CASE
                      WHEN rp.shortname IS NULL THEN rp.name
                      ELSE rp.shortname
                    END ,
                      sc.status,
                      si.name ,
                      pp.default_code ,
                      pc.id ,
                      pt.quality_type,
                      sil.product_qty ,
                      np.name ,
                      si.packing_place,
                      si.shipment_date,
                      nf.name ,
                      si.fumigation_date,
                      si.pss_condition,
                      si.pss_send_schedule,
                      si.factory_etd,
                      si.materialstatus,
                      si.production_status,
                      sc.allowed_franchise ,
                      si.packing_place  ,
                      pm.pss_count,
                      sc.type ,
                        CASE
                          WHEN si.factory_etd IS NULL THEN week_num_year(si.shipment_date)
                          ELSE week_num_year(si.factory_etd)
                        END ,
                      scline.name ,
                      cert.name ,
                      pm.approved,
                      pm.rejected
                ) DESC  

            ) AS id,
              sc.name AS s_contract,
                CASE
                  WHEN rp.shortname IS NULL THEN rp.name
                  ELSE rp.shortname
                END AS customer,
              sc.status AS ship_by,
              si.name AS si_number,
              pp.default_code AS product,
              pc.id AS grade_id,
              pt.quality_type AS quality_type,
              sil.product_qty AS si_quantity,
              np.name AS packing,
              si.packing_place,
              si.shipment_date,
              nf.name AS fumigation_type,
              si.fumigation_date,
              si.pss_condition,
              si.pss_send_schedule,
              si.factory_etd,
              si.materialstatus,
              si.production_status,
              sc.allowed_franchise as allowed_franchise,
              si.packing_place as warehouse,
              pm.pss_count,
              sc.type AS sales_type,
              COALESCE(sum(nvsl.product_qty), 0::numeric) AS nvs_allocated,
              COALESCE(sum(deli_v1.do_qty), 0::numeric) AS do_quantity,
              COALESCE(sum(deli.gdn_quantity), 0::numeric) AS gdn_quantity,
              si.priority_by_month AS priority,
                CASE
                  WHEN COALESCE(sum(deli.gdn_quantity), 0::numeric) = COALESCE(sil.product_qty, 0::numeric) OR (((sil.product_qty - sum(deli.gdn_quantity)) / sil.product_qty) * 100) <= 2 THEN 'Done'::text
                  WHEN COALESCE(sum(nvsl.product_qty), 0::numeric) = 0::numeric THEN 'Unallocated'::text
                  WHEN COALESCE(sum(deli.do_quantity), 0::numeric) > COALESCE(sum(deli.gdn_quantity), 0::numeric) THEN 'Waiting GDN'::text
                  WHEN COALESCE(sum(deli.gdn_quantity), 0::numeric) < sil.product_qty THEN 'In progress'::text
                  ELSE NULL::text
                END AS status,
                CASE
                  WHEN si.factory_etd IS NULL THEN week_num_year(si.shipment_date)
                  ELSE week_num_year(si.factory_etd)
                END AS week_num_year,
              si.prodcompleted AS prod_complete_date,
              si.prodcompleted + 1 AS goods_availability,
              si.closing_time,
              stock_allocation.allocated_qty AS production_progress,
              scline.name AS specification,
              cert.name as certificate,
              pm.approved as pss_approved,
              pm.rejected as pss_rejected,
              pm.rejected_nestle as rejected_nestle,
              pm.approved_nestle as approved_nestle

             FROM s_contract sc
               JOIN s_contract_line scline ON sc.id = scline.contract_id
               JOIN res_partner rp ON rp.id = sc.partner_id
               LEFT JOIN shipping_instruction si ON sc.id = si.contract_id
               LEFT JOIN shipping_instruction_line sil ON si.id = sil.shipping_id
               JOIN product_product pp ON pp.id = sil.product_id
               JOIN product_template pt ON pt.id = pp.product_tmpl_id
               join product_category pc on pc.id = pt.categ_id
               LEFT JOIN ned_packing np ON np.id = sil.packing_id
               LEFT JOIN ned_fumigation nf ON si.fumigation_id = nf.id
               LEFT JOIN ( SELECT pm_1.shipping_id,
                  count(pm_1.shipping_id) AS pss_count,
                    count(pm_1.pss_status) filter (where pm_1.pss_status = 'approved') as approved,
                    count(pm_1.pss_status) filter (where pm_1.pss_status = 'rejected') as rejected,
                    count(pm_1.status_nestle) filter (where pm_1.status_nestle in ('reject_phys', 'reject_gly', 'reject_cupping')) as rejected_nestle,
                    count(pm_1.status_nestle) filter (where pm_1.status_nestle = 'approved') as approved_nestle
                 FROM pss_management pm_1
                GROUP BY pm_1.shipping_id) pm ON si.id = pm.shipping_id
               LEFT JOIN sale_contract nvs ON si.id = nvs.shipping_id
               LEFT JOIN sale_contract_line nvsl ON nvs.id = nvsl.contract_id
               LEFT JOIN ( SELECT dor.contract_id,
                  sum(dol.product_qty) AS do_quantity,
                  sum(sm.gdn_quantity) AS gdn_quantity,
                  sp.state
                 FROM delivery_order dor
                   JOIN delivery_order_line dol ON dor.id = dol.delivery_id
                   LEFT JOIN stock_picking sp ON dor.picking_id = sp.id
                   LEFT JOIN ( SELECT stock_move_line.picking_id,
                      sum(stock_move_line.qty_done) AS gdn_quantity
                     FROM stock_move_line
                    GROUP BY stock_move_line.picking_id) sm ON dor.picking_id = sm.picking_id
                 where sp.state = 'done'
                GROUP BY dor.contract_id, sp.state) deli ON nvs.id = deli.contract_id
                 left join (
                     Select dor.contract_id,
                            sum(dol.product_qty) as do_qty
                     from delivery_order dor
                     JOIN delivery_order_line dol ON dor.id = dol.delivery_id
                     group by dor.contract_id
             ) deli_v1 on nvs.id = deli_v1.contract_id
               LEFT JOIN ( SELECT stock_contract_allocation.shipping_id,
                  sum(stock_contract_allocation.allocating_quantity) AS allocated_qty
                 FROM stock_contract_allocation
                GROUP BY stock_contract_allocation.shipping_id) stock_allocation ON si.id = stock_allocation.shipping_id
              left join ned_certificate cert on sil.certificate_id = cert.id
            where sc.status = 'Factory' and si.state != 'cancel'
            GROUP BY scline.name, sc.name, cert.name,pc.id, pt.quality_type,
                CASE
                  WHEN rp.shortname IS NULL THEN rp.name
                  ELSE rp.shortname
                END, sc.status, sc.allowed_franchise, si.name, pp.default_code, sil.product_qty, np.name, si.packing_place, si.shipment_date, nf.name, si.fumigation_date, si.pss_condition, si.pss_send_schedule, si.factory_etd, si.materialstatus, si.production_status, pm.shipping_id, pm.pss_count, si.priority_by_month, si.prodcompleted, si.closing_time, stock_allocation.allocated_qty, sc.type, pm.approved, pm.rejected,pm.rejected_nestle,pm.approved_nestle
            ORDER BY 
                sc.name, 
                CASE
                  WHEN rp.shortname IS NULL THEN rp.name
                  ELSE rp.shortname
                END, 
                sc.status,
                si.name,
                pp.default_code,
                np.name,
                si.priority_by_month,
                si.packing_place,
                si.shipment_date,
                nf.name,
                si.fumigation_date,
                si.pss_condition,
                si.pss_send_schedule,
                si.factory_etd,
                si.materialstatus,
                si.production_status,
                sc.allowed_franchise ,
                si.packing_place ,
                pm.pss_count,
                sc.type ,


                CASE
                  WHEN si.factory_etd IS NULL THEN week_num_year(si.shipment_date)
                  ELSE week_num_year(si.factory_etd)
                END;
                  ''')

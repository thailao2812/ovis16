# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"

class CertificateLicenseDetail(models.Model):
    _name = 'v.sd.certificate.license.detail'
    _description = 'Certificate License Detail'
    _auto = False
    _order = 'expired_date desc'
    
    cert_name = fields.Char('Certificate')
    license_number = fields.Char('License Number')
    type = fields.Char(string = 'Type')
    partner_name = fields.Char(string = 'Supplier')
    expired_date = fields.Date('Expired Date')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('active', 'Active'),
         ('expired', 'Expired'),
         ('deactive', 'Deactive')],
        string="Status", default='draft')
    warehouse_name = fields.Char(string = 'Warehouse')
    
    faq_tobe_received = fields.Float(string='FAQ Tobe Receive', digits=(12, 2))
    g1_s18_tobe_received = fields.Float(string='G1-S18 Tobe Receive', digits=(12, 2))
    g1_s16_tobe_received = fields.Float(string='G1-S16 Tobe Receive', digits=(12, 2))
    g2_tobe_received = fields.Float(string='G2 Tobe Receive', digits=(12, 2))
    
    faq_purchase = fields.Float(string='FAQ Purchase', digits=(12, 2))
    g1_s18_purchase = fields.Float(string='G1-S18 Purchase', digits=(12, 2))
    g1_s16_purchase = fields.Float(string='G1-S16 Purchase', digits=(12, 2))
    g2_purchase = fields.Float(string='G2 Purchase', digits=(12, 2))

    faq_derivable = fields.Float(string='FAQ Derivable', digits=(12, 2))
    g1_s18_derivable = fields.Float(string='G1-S18 Derivable', digits=(12, 2))
    g1_s16_derivable = fields.Float(string='G1-S16 Derivable', digits=(12, 2))
    g2_derivable = fields.Float(string='G2 Derivable', digits=(12, 2))
    g3_derivable = fields.Float(string='G3 Derivable', digits=(12, 2))

    faq_allocated = fields.Float(string='FAQ Allocated', digits=(12, 2))
    g1_s18_allocated = fields.Float(string='G1-S18 Allocated', digits=(12, 2))
    g1_s16_allocated = fields.Float(string='G1-S16 Allocated', digits=(12, 2))
    g2_allocated = fields.Float(string='G2 Allocated', digits=(12, 2))
    g3_allocated = fields.Float(string='G3 Allocated', digits=(12, 2))

    faq_allocated_not_out = fields.Float(string='FAQ Tobe Ship', digits=(12, 2))
    g1_s18_allocated_not_out = fields.Float(string='G1-S18 Tobe Ship', digits=(12, 2))
    g1_s16_allocated_not_out = fields.Float(string='G1-S16 Tobe Ship', digits=(12, 2))
    g2_allocated_not_out = fields.Float(string='G2 Tobe Ship', digits=(12, 2))
    g3_allocated_not_out = fields.Float(string='G3 Tobe Ship', digits=(12, 2))

    faq_allocated_out = fields.Float(string='FAQ Shipped', digits=(12, 2))
    g1_s18_allocated_out = fields.Float(string='G1-S18 Shipped', digits=(12, 2))
    g1_s16_allocated_out = fields.Float(string='G1-S16 Shipped', digits=(12, 2))
    g2_allocated_out = fields.Float(string='G2 Shipped', digits=(12, 2))
    g3_allocated_out = fields.Float(string='G3 Shipped', digits=(12, 2))

    faq_unallocated = fields.Float(string='FAQ Un Allocate', digits=(12, 2))
    g1_s18_unallocated = fields.Float(string='G1-S18 Un Allocate', digits=(12, 2))
    g1_s16_unallocated = fields.Float(string='G1-S16 Un Allocate', digits=(12, 2))
    g2_unallocated = fields.Float(string='G2 Un Allocate', digits=(12, 2))
    g3_unallocated = fields.Float(string='G3 Un Allocate', digits=(12, 2))

    faq_balance = fields.Float(string='FAQ Balance', digits=(12, 2))
    g1_s18_balance = fields.Float(string='G1-S18 Balance', digits=(12, 2))
    g1_s16_balance = fields.Float(string='G1-S16 Balance', digits=(12, 2))
    g2_balance = fields.Float(string='G2 Balance', digits=(12, 2))
    g3_balance = fields.Float(string='G3 Balance', digits=(12, 2))

    final_balance = fields.Float(string='Final Balance', digits=(12, 2))

    faq_position = fields.Float(string='FAQ Position', digits=(12, 2))
    g1_s18_position = fields.Float(string='G1-S18 Position', digits=(12, 2))
    g1_s16_position = fields.Float(string='G1-S16 Position', digits=(12, 2))
    g2_position = fields.Float(string='G2 Position', digits=(12, 2))
    g3_position = fields.Float(string='G3 Position', digits=(12, 2))

    total_position = fields.Float(string='Total Position', digits=(12, 2))

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_sd_certificate_license_detail')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW public.v_sd_certificate_license_detail AS
            SELECT row_number() OVER (ORDER BY ncl.expired_date DESC) AS id, cert.name cert_name, ncl.name license_number, ncl.type, ncl.expired_date, ncl.state,
                    swh.code warehouse_name, rp.display_name partner_name,
                    license.*, license.faq_balance + license.g1_s18_balance + license.g1_s16_balance + license.g2_balance + license.g3_balance AS final_balance,
                    license.faq_balance + license.faq_tobe_received AS faq_position,
                    license.g1_s18_balance + license.g1_s18_tobe_received AS g1_s18_position,
                    license.g1_s16_balance + license.g1_s16_tobe_received AS g1_s16_position,
                    license.g2_balance + license.g2_tobe_received AS g2_position,
                    license.g3_balance AS g3_position,
                    (license.faq_balance + license.faq_tobe_received) + (license.g1_s18_balance + license.g1_s18_tobe_received) + 
                    (license.g1_s16_balance + license.g1_s16_tobe_received) + (license.g2_balance + license.g2_tobe_received) +
                    license.g3_balance AS total_position
                FROM (SELECT *,
                        -- Derivable
                        COALESCE(lsa.faq_purchase, 0::numeric) - COALESCE(s_license_alc.faq_allocated, 0::numeric) AS faq_derivable,
                        COALESCE(COALESCE(lsa.g1_s18_purchase, 0::int) + ((COALESCE(lsa.faq_purchase, 0::numeric) - COALESCE(s_license_alc.faq_allocated, 0::numeric)) * 25 / 100), 0::int) AS g1_s18_derivable,
                        COALESCE(COALESCE(lsa.g1_s16_purchase, 0::int) + ((COALESCE(lsa.faq_purchase, 0::numeric) - COALESCE(s_license_alc.faq_allocated, 0::numeric)) * 33 / 100), 0::int) AS g1_s16_derivable,
                        COALESCE(COALESCE(lsa.g2_purchase, 0::int) + ((COALESCE(lsa.faq_purchase, 0::numeric) - COALESCE(s_license_alc.faq_allocated, 0::numeric)) * 40 / 100), 0::int) AS g2_derivable,
                        0 AS g3_derivable,
                        -- Unallocated
                        0 AS faq_unallocated,
                        COALESCE(COALESCE(lsa.g1_s18_purchase, 0::int) + ((COALESCE(lsa.faq_purchase, 0::numeric) - COALESCE(s_license_alc.faq_allocated, 0::numeric)) * 25 / 100), 0::int) - COALESCE(s_license_alc.g1_s18_allocated, 0::int) AS g1_s18_unallocated,
                        COALESCE(COALESCE(lsa.g1_s16_purchase, 0::int) + ((COALESCE(lsa.faq_purchase, 0::numeric) - COALESCE(s_license_alc.faq_allocated, 0::numeric)) * 33 / 100), 0::int) - COALESCE(s_license_alc.g1_s16_allocated, 0::int) AS g1_s16_unallocated,
                        COALESCE(COALESCE(lsa.g2_purchase, 0::int) + ((COALESCE(lsa.faq_purchase, 0::numeric) - COALESCE(s_license_alc.faq_allocated, 0::numeric)) * 40 / 100), 0::int) - COALESCE(s_license_alc.g2_allocated, 0::int) AS g2_unallocated,
                        0 - COALESCE(s_license_alc.g3_allocated, 0::int) AS g3_unallocated,
                        -- Balance
                        0 AS faq_balance,
                        COALESCE(COALESCE(lsa.g1_s18_purchase, 0::int) + ((COALESCE(lsa.faq_purchase, 0::numeric) - COALESCE(s_license_alc.faq_allocated, 0::numeric)) * 25 / 100), 0::int) - COALESCE(s_license_alc.g1_s18_allocated_out, 0::int) AS g1_s18_balance,
                        COALESCE(COALESCE(lsa.g1_s16_purchase, 0::int) + ((COALESCE(lsa.faq_purchase, 0::numeric) - COALESCE(s_license_alc.faq_allocated, 0::numeric)) * 33 / 100), 0::int) - COALESCE(s_license_alc.g1_s16_allocated_out, 0::int) AS g1_s16_balance,
                        COALESCE(COALESCE(lsa.g2_purchase, 0::int) + ((COALESCE(lsa.faq_purchase, 0::numeric) - COALESCE(s_license_alc.faq_allocated, 0::numeric)) * 40 / 100), 0::int) - COALESCE(s_license_alc.g2_allocated_out, 0::int) AS g2_balance,
                        0 - COALESCE(s_license_alc.g3_allocated_out, 0::int) AS g3_balance,
                        -- Allocated not out
                        COALESCE(s_license_alc.faq_allocated, 0::int) - COALESCE(s_license_alc.faq_allocated_out, 0::int) AS faq_allocated_not_out,
                        COALESCE(s_license_alc.g1_s18_allocated, 0::int) - COALESCE(s_license_alc.g1_s18_allocated_out, 0::int) AS g1_s18_allocated_not_out,
                        COALESCE(s_license_alc.g1_s16_allocated, 0::int) - COALESCE(s_license_alc.g1_s16_allocated_out, 0::int) AS g1_s16_allocated_not_out,
                        COALESCE(s_license_alc.g2_allocated, 0::int) - COALESCE(s_license_alc.g2_allocated_out, 0::int) AS g2_allocated_not_out,
                        COALESCE(s_license_alc.g3_allocated, 0::int) - COALESCE(s_license_alc.g3_allocated_out, 0::int) AS g3_allocated_not_out
                        FROM (SELECT sal.license_id, sal.warehouse_id, sal.partner_id,
                                sum(CASE WHEN pc.name = 'FAQ' THEN sal.qty_allocation ELSE 0 END) AS faq_purchase,
                                sum(CASE WHEN pc.name = 'G1-S18' THEN sal.qty_allocation ELSE 0 END) AS g1_s18_purchase,
                                sum(CASE WHEN pc.name = 'G1-S16' THEN sal.qty_allocation ELSE 0 END) AS g1_s16_purchase,
                                sum(CASE WHEN pc.name = 'G2' THEN sal.qty_allocation ELSE 0 END) AS g2_purchase
                            FROM stock_allocation sal
                            JOIN product_category pc ON pc.id=sal.grade_id
                            WHERE sal.state='approved'
                            -- and sal.license_id in (185,136,123)
                            GROUP BY sal.license_id, sal.warehouse_id, sal.partner_id) lsa
                        
                        LEFT JOIN (SELECT pur_c.license_id, pur_c.warehouse_id,
                                sum(CASE WHEN pc.name = 'FAQ' THEN pur_c.qty_unreceived ELSE 0 END) AS faq_tobe_received,
                                sum(CASE WHEN pc.name = 'G1-S18' THEN pur_c.qty_unreceived ELSE 0 END) AS g1_s18_tobe_received,
                                sum(CASE WHEN pc.name = 'G1-S16' THEN pur_c.qty_unreceived ELSE 0 END) AS g1_s16_tobe_received,
                                sum(CASE WHEN pc.name = 'G2' THEN pur_c.qty_unreceived ELSE 0 END) AS g2_tobe_received
                            FROM purchase_contract pur_c
                            JOIN product_category pc ON pc.id=pur_c.grade_id
                            -- WHERE pur_c.license_id in (185,136,123)
                            GROUP BY pur_c.license_id, pur_c.warehouse_id) lpc USING (license_id, warehouse_id)
                        
                        LEFT JOIN (SELECT sila1.license_id, sila1.warehouse_id, 
                                COALESCE(sila1.faq_allocated, 0::numeric) + COALESCE((scla1.s_faq_allocated), 0::numeric) AS faq_allocated,
                                COALESCE(sila1.g1_s18_allocated, 0::numeric) + COALESCE((scla1.s_g1_s18_allocated), 0::numeric) AS g1_s18_allocated,
                                COALESCE(sila1.g1_s16_allocated, 0::numeric) + COALESCE((scla1.s_g1_s16_allocated), 0::numeric) AS g1_s16_allocated,
                                COALESCE(sila1.g2_allocated, 0::numeric) + COALESCE((scla1.s_g2_allocated), 0::numeric) AS g2_allocated, sila1.g3_allocated,
                                COALESCE(sila1.faq_allocated_out, 0::numeric) + COALESCE((scla1.s_faq_allocated), 0::numeric) AS faq_allocated_out,
                                COALESCE(sila1.g1_s18_allocated_out, 0::numeric) + COALESCE((scla1.s_g1_s18_allocated), 0::numeric) AS g1_s18_allocated_out,
                                COALESCE(sila1.g1_s16_allocated_out, 0::numeric) + COALESCE((scla1.s_g1_s16_allocated), 0::numeric) AS g1_s16_allocated_out,
                                COALESCE(sila1.g2_allocated_out, 0::numeric) + COALESCE((scla1.s_g2_allocated), 0::numeric) AS g2_allocated_out,
                                COALESCE(sila1.g3_allocated_out, 0::numeric) + COALESCE((scla1.s_g3_allocated), 0::numeric) AS g3_allocated_out
                                FROM (SELECT sila.license_id, sila.warehouse_id,
                                        sum(CASE WHEN pc.name = 'FAQ' THEN sila.allocation_qty ELSE 0 END) AS faq_allocated,
                                        sum(CASE WHEN pc.name = 'G1-S18' THEN sila.allocation_qty ELSE 0 END) AS g1_s18_allocated,
                                        sum(CASE WHEN pc.name = 'G1-S16' THEN sila.allocation_qty ELSE 0 END) AS g1_s16_allocated,
                                        sum(CASE WHEN pc.name = 'G2' THEN sila.allocation_qty ELSE 0 END) AS g2_allocated,
                                        sum(CASE WHEN pc.name = 'FAQ' and sila.state='done' THEN sila.allocation_qty ELSE 0 END) AS faq_allocated_out,
                                        sum(CASE WHEN pc.name = 'G1-S18' and sila.state='done' THEN sila.allocation_qty ELSE 0 END) AS g1_s18_allocated_out,
                                        sum(CASE WHEN pc.name = 'G1-S16' and sila.state='done' THEN sila.allocation_qty ELSE 0 END) AS g1_s16_allocated_out,
                                        sum(CASE WHEN pc.name = 'G2' and sila.state='done' THEN sila.allocation_qty ELSE 0 END) AS g2_allocated_out,
                                        sum(CASE WHEN pc.name = 'G3' THEN sila.allocation_qty ELSE 0 END) AS g3_allocated,
                                        sum(CASE WHEN pc.name = 'G3' and sila.state='done' THEN sila.allocation_qty ELSE 0 END) AS g3_allocated_out
                                    FROM shipping_instruction_license_allocation sila
                                    JOIN product_category pc ON pc.id=sila.grade_id
                                    WHERE sila.warehouse_id>0
                                    -- and sila.license_id in (185,136,123)
                                    GROUP BY sila.license_id, sila.warehouse_id) sila1
                            
                                    LEFT JOIN (SELECT scla.license_id,
                                        sum(CASE WHEN pc.name = 'FAQ' THEN scla.allocation_qty ELSE 0 END) AS s_faq_allocated,
                                        sum(CASE WHEN pc.name = 'G1-S18' THEN scla.allocation_qty ELSE 0 END) AS s_g1_s18_allocated,
                                        sum(CASE WHEN pc.name = 'G1-S16' THEN scla.allocation_qty ELSE 0 END) AS s_g1_s16_allocated,
                                        sum(CASE WHEN pc.name = 'G2' THEN scla.allocation_qty ELSE 0 END) AS s_g2_allocated,
                                        sum(CASE WHEN pc.name = 'G3' THEN scla.allocation_qty ELSE 0 END) AS s_g3_allocated
                                    FROM s_contract_license_allocation scla
                                    JOIN product_category pc ON pc.id=scla.grade_id
                                    -- WHERE scla.license_id in (185,136,123)
                                    GROUP BY scla.license_id) scla1 USING (license_id)) s_license_alc
                        USING (license_id, warehouse_id)) AS license

                JOIN stock_warehouse swh ON swh.id=license.warehouse_id
                JOIN res_partner rp ON rp.id=license.partner_id
                JOIN ned_certificate_license ncl ON ncl.id=license.license_id
                JOIN ned_certificate cert ON cert.id=ncl.certificate_id;
            """)
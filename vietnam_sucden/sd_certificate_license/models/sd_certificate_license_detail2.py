# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"

class CertificateLicenseDetail(models.Model):
    _name = 'v.sd.certificate.license.detail2'
    _description = 'Certificate License Detail 2'
    _auto = False
    _order = 'expired_date desc'
    
    license_id = fields.Many2one('ned.certificate.license', string='License')
    type = fields.Selection([('sucden_coffee_license', 'Sucden Coffee License'),
                               ('independent_license', '3rd Party License'),
                               ], string='Type') # Guatemala
    partner_id = fields.Many2one('res.partner', string = 'Supplier')
    state_id = fields.Many2one('res.country.state', string='Province')
    expired_date = fields.Date('Expired Date')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('active', 'Active'),
         ('expired', 'Expired'),
         ('deactive', 'Deactive')],
        string="Status", default='draft')
    warehouse_id = fields.Many2one('stock.warehouse', string = 'Warehouse')
    
    col_4c = fields.Boolean(string='4C', default=False)
    col_4c_fc = fields.Boolean(string='4C FC', default=False)
    col_ra = fields.Boolean(string='RA', default=False)
    col_scv = fields.Boolean(string='SCV', default=False)
    col_eudr = fields.Boolean(string='EUDR', default=False)
    col_utz_certified = fields.Boolean(string='UTZ Certified', default=False)
    col_optional_utz_4c = fields.Boolean(string='Optional UTZ & 4C', default=False)
    
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

    def func_certificate_license_temp(self):
        tools.drop_view_if_exists(self.env.cr, 'public.v_sd_certificate_license_temp')
        tools.drop_view_if_exists(self.env.cr, 'public.v_sd_certificate_license_pivot')
        sql ="""
                CREATE OR REPLACE VIEW public.v_sd_certificate_license_temp AS
                SELECT row_number() OVER (ORDER BY license.cert_id, license.warehouse_id, license.partner_id DESC) AS id, cert.name cert_name,
                        CASE WHEN license.cert_id IS NULL THEN false ELSE true END AS cert_check,
                        license.*
                    FROM (SELECT *
                            FROM (SELECT sal.license_id, sal.warehouse_id, sal.partner_id, rel.ned_certificate_id AS cert_id
                                FROM stock_allocation sal
                                JOIN product_category pc ON pc.id=sal.grade_id
                                JOIN purchase_contract pur_c ON pur_c.id=sal.contract_id
                                JOIN ned_certificate_purchase_contract_rel AS rel ON pur_c.id = rel.purchase_contract_id
                                WHERE sal.state='approved'
                                -- and sal.license_id in (185,79)
                                GROUP BY sal.license_id, sal.warehouse_id, sal.partner_id, rel.ned_certificate_id) lsa
                            
                            LEFT JOIN (SELECT pur_c.license_id, pur_c.warehouse_id, rel.ned_certificate_id AS cert_id
                                FROM purchase_contract pur_c
                                JOIN product_category pc ON pc.id=pur_c.grade_id
                                JOIN ned_certificate_purchase_contract_rel AS rel ON pur_c.id = rel.purchase_contract_id
                                -- WHERE pur_c.license_id in (185,79)
                                GROUP BY pur_c.license_id, pur_c.warehouse_id, rel.ned_certificate_id) lpc USING (license_id, warehouse_id,cert_id)
                            
                            LEFT JOIN (SELECT sila1.license_id, sila1.warehouse_id, sila1.cert_id
                                FROM (SELECT sila.license_id, sila.warehouse_id, shi.certificate_id AS cert_id
                                    FROM shipping_instruction_license_allocation sila
                                    JOIN product_category pc ON pc.id=sila.grade_id
                                    JOIN shipping_instruction si ON si.id=sila.shipping_id
                                    JOIN certificate_shipping_instruction shi ON shi.shipping_instruction_id=si.id
                                    WHERE sila.warehouse_id>0
                                    -- and sila.license_id in (185,79)
                                    GROUP BY sila.license_id, sila.warehouse_id, shi.certificate_id) sila1
                            
                                LEFT JOIN (SELECT scla.license_id, csc.certificate_id AS cert_id
                                FROM s_contract_license_allocation scla
                                JOIN product_category pc ON pc.id=scla.grade_id
                                JOIN s_contract sc ON sc.id=scla.s_contract_id
                                JOIN certificate_s_contract csc ON csc.s_contract_id=sc.id
                                -- WHERE scla.license_id in (185,79)
                                GROUP BY scla.license_id, csc.certificate_id) scla1 USING (license_id, cert_id)) s_license_alc
                            USING (license_id, warehouse_id,cert_id)) AS license

                    JOIN ned_certificate cert ON cert.id=license.cert_id;
             
            -- Create Pivot table: v_sd_certificate_license_pivot       
            DO $$ 
            DECLARE 
            cols text;
            query text;
            _cursor CONSTANT refcursor := '_cursor';
            BEGIN
            -- Dynamically generate the list of columns
            SELECT 'license_id int, warehouse_id int, partner_id int,'
                || string_agg(DISTINCT format('"%s" boolean', 'col_' || replace(replace(LOWER(cert_name), '''', ''),' ','_')), ', ') INTO cols
            FROM v_sd_certificate_license_temp;
            -- Construct the final crosstab query with proper escaping
            query := format(
                'SELECT * FROM crosstab(
                ''SELECT license_id, warehouse_id, partner_id, cert_name, cert_check
                FROM v_sd_certificate_license_temp
                ORDER BY 1,2'',
                ''SELECT DISTINCT cert_name 
                FROM v_sd_certificate_license_temp''
                -- ORDER BY contract_id
                ) AS ct(%s)', 
            cols
            );
            
            -- Execute the query
            EXECUTE ('CREATE OR REPLACE VIEW public.v_sd_certificate_license_pivot AS ' || query);
            END $$;
        """
        self.env.cr.execute(sql)

    def init(self):
        self.func_certificate_license_temp()
        tools.drop_view_if_exists(self.env.cr, 'v_sd_certificate_license_detail2')
        self.env.cr.execute("""
                CREATE OR REPLACE VIEW public.v_sd_certificate_license_detail2 AS
                SELECT row_number() OVER (ORDER BY license_id, warehouse_id, partner_id) AS id,* 
                FROM v_sd_certificate_license_pivot 
                JOIN (SELECT ncl.name license_number, ncl.type, ncl.expired_date, ncl.state,
                        swh.code warehouse_name, rp.display_name partner_name, rp.state_id,
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
                        0 AS faq_derivable,
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
                            JOIN purchase_contract pur_c ON pur_c.id=sal.contract_id
                            WHERE sal.state='approved'
                            -- and sal.license_id in (185,171)
                            -- and sal.license_id in (185,136,123)
                            GROUP BY sal.license_id, sal.warehouse_id, sal.partner_id) lsa
                        
                        LEFT JOIN (SELECT pur_c.license_id, pur_c.warehouse_id,
                                sum(CASE WHEN pc.name = 'FAQ' THEN pur_c.qty_unreceived ELSE 0 END) AS faq_tobe_received,
                                sum(CASE WHEN pc.name = 'G1-S18' THEN pur_c.qty_unreceived ELSE 0 END) AS g1_s18_tobe_received,
                                sum(CASE WHEN pc.name = 'G1-S16' THEN pur_c.qty_unreceived ELSE 0 END) AS g1_s16_tobe_received,
                                sum(CASE WHEN pc.name = 'G2' THEN pur_c.qty_unreceived ELSE 0 END) AS g2_tobe_received
                            FROM purchase_contract pur_c
                            JOIN product_category pc ON pc.id=pur_c.grade_id
                            -- WHERE pur_c.license_id in (185,171)
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
                                JOIN shipping_instruction si ON si.id=sila.shipping_id
                                WHERE sila.warehouse_id>0
                                -- and sila.license_id in (185,171)
                                GROUP BY sila.license_id, sila.warehouse_id) sila1
                        
                            LEFT JOIN (SELECT scla.license_id,
                                sum(CASE WHEN pc.name = 'FAQ' THEN scla.allocation_qty ELSE 0 END) AS s_faq_allocated,
                                sum(CASE WHEN pc.name = 'G1-S18' THEN scla.allocation_qty ELSE 0 END) AS s_g1_s18_allocated,
                                sum(CASE WHEN pc.name = 'G1-S16' THEN scla.allocation_qty ELSE 0 END) AS s_g1_s16_allocated,
                                sum(CASE WHEN pc.name = 'G2' THEN scla.allocation_qty ELSE 0 END) AS s_g2_allocated,
                                sum(CASE WHEN pc.name = 'G3' THEN scla.allocation_qty ELSE 0 END) AS s_g3_allocated
                            FROM s_contract_license_allocation scla
                            JOIN product_category pc ON pc.id=scla.grade_id
                            JOIN s_contract sc ON sc.id=scla.s_contract_id
                            -- WHERE scla.license_id in (185,171)
                            GROUP BY scla.license_id) scla1 USING (license_id)) s_license_alc
                        USING (license_id, warehouse_id)) AS license
                    JOIN stock_warehouse swh ON swh.id=license.warehouse_id
                    JOIN res_partner rp ON rp.id=license.partner_id
                    JOIN ned_certificate_license ncl ON ncl.id=license.license_id) AS lic_tbl
                    
                USING (license_id,warehouse_id,partner_id)
                ORDER BY license_id;
            """)
        
    # def func_sd_colpivot(self):
    #     sql ="""
    #         drop view if exists public.v_sd_certificate_license_detail2;
            
    #         CREATE OR REPLACE FUNCTION public.sd_colpivot(
    #             out_table varchar, in_query varchar,
    #             key_cols varchar[], class_cols varchar[],
    #             value_e varchar, col_order varchar
    #         ) returns void as $$
    #             declare
    #                 in_table varchar;
    #                 col varchar;
    #                 ali varchar;
    #                 on_e varchar;
    #                 i integer;
    #                 rec record;
    #                 query varchar;
    #                 -- This is actually an array of arrays but postgres does not support an array of arrays type so we flatten it.
    #                 -- We could theoretically use the matrix feature but it's extremly cancerogenous and we would have to involve
    #                 -- custom aggrigates. For most intents and purposes postgres does not have a multi-dimensional array type.
    #                 clsc_cols text[] := array[]::text[];
    #                 n_clsc_cols integer;
    #                 n_class_cols integer;
    #             begin
    #                 in_table := quote_ident('__' || out_table || '_in');
    #                 execute ('create table ' || in_table || ' as ' || in_query);
    #                 -- get ordered unique columns (column combinations)
    #                 query := 'select array[';
    #                 i := 0;
    #                 foreach col in array class_cols loop
    #                     if i > 0 then
    #                         query := query || ', ';
    #                     end if;
    #                     query := query || 'quote_literal(' || quote_ident(col) || ')';
    #                     i := i + 1;
    #                 end loop;
    #                 query := query || '] x from ' || in_table;
    #                 for j in 1..2 loop
    #                     if j = 1 then
    #                         query := query || ' group by ';
    #                     else
    #                         query := query || ' order by ';
    #                         if col_order is not null then
    #                             query := query || col_order || ' ';
    #                             exit;
    #                         end if;
    #                     end if;
    #                     i := 0;
    #                     foreach col in array class_cols loop
    #                         if i > 0 then
    #                             query := query || ', ';
    #                         end if;
    #                         query := query || quote_ident(col);
    #                         i := i + 1;
    #                     end loop;
    #                 end loop;
    #                 -- raise notice '%', query;
    #                 for rec in
    #                     execute query
    #                 loop
    #                     clsc_cols := array_cat(clsc_cols, rec.x);
    #                 end loop;
    #                 n_class_cols := array_length(class_cols, 1);
    #                 n_clsc_cols := array_length(clsc_cols, 1) / n_class_cols;
    #                 -- build target query
    #                 query := 'select ';
    #                 i := 0;
    #                 foreach col in array key_cols loop
    #                     if i > 0 then
    #                         query := query || ', ';
    #                     end if;
    #                     query := query || '_key.' || quote_ident(col) || ' ';
    #                     i := i + 1;
    #                 end loop;
    #                 for j in 1..n_clsc_cols loop
    #                     query := query || ', ';
    #                     col := '';
    #                     for k in 1..n_class_cols loop
    #                         if k > 1 then
    #                             col := col || ', ';
    #                         end if;
    #                         col := col || clsc_cols[(j - 1) * n_class_cols + k];
    #                     end loop;
    #                     ali := '_clsc_' || j::text;
    #                     query := query || '(' || replace(value_e, '#', ali) || ')' || ' as ' || 'col_' || replace(replace(LOWER(col), '''', ''),' ','_')::text || ' ';
    #                 end loop;
    #                 query := query || ' from (select distinct ';
    #                 i := 0;
    #                 foreach col in array key_cols loop
    #                     if i > 0 then
    #                         query := query || ', ';
    #                     end if;
    #                     query := query || quote_ident(col) || ' ';
    #                     i := i + 1;
    #                 end loop;
    #                 query := query || ' from ' || in_table || ') _key ';
    #                 for j in 1..n_clsc_cols loop
    #                     ali := '_clsc_' || j::text;
    #                     on_e := '';
    #                     i := 0;
    #                     foreach col in array key_cols loop
    #                         if i > 0 then
    #                             on_e := on_e || ' and ';
    #                         end if;
    #                         on_e := on_e || ali || '.' || quote_ident(col) || ' = _key.' || quote_ident(col) || ' ';
    #                         i := i + 1;
    #                     end loop;
    #                     for k in 1..n_class_cols loop
    #                         on_e := on_e || ' and ';
    #                         on_e := on_e || ali || '.' || quote_ident(class_cols[k]) || ' = ' || clsc_cols[(j - 1) * n_class_cols + k];
    #                     end loop;
    #                     query := query || 'left join ' || in_table || ' as ' || ali || ' on ' || on_e || ' ';
    #                 end loop;
    #                 -- raise notice '%', query;
    #                 execute ('create table ' || quote_ident(out_table) || ' as ' || query);
    #                 -- cleanup temporary in_table before we return
    #                 execute ('drop table ' || in_table)
    #                 return;
    #             end;
    #         $$ language plpgsql volatile;
    #         """
    #     self.env.cr.execute(sql)

    # def func_make_colpivot_tbl(self):
    #     sql ="""
    #         drop table IF EXISTS certificate_pivoted;
            
    #         SELECT sd_colpivot('certificate_pivoted', 'SELECT license_id, warehouse_id, partner_id, cert_id, cert_name, check_cert
    #         FROM (SELECT license_id, warehouse_id, partner_id, cert_id, cert_name,
    #                 CASE WHEN cert_id>0 THEN true ELSE false END AS check_cert
    #                 FROM v_sd_certificate_license_detail) tbl
    #         ORDER BY 1,2',
    #             array['license_id','warehouse_id','partner_id'], array['cert_name'], '#.check_cert', null);
    #     """
    #     self.env.cr.execute(sql)
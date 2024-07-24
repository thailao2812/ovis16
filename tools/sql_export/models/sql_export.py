# Copyright (C) 2015 Akretion (<http://www.akretion.com>)
# @author: Florian da Costa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models, _
from odoo.exceptions import UserError


class SqlExport(models.Model):
    _name = "sql.export"
    _inherit = ["sql.request.mixin"]
    _description = "SQL export"

    _sql_request_groups_relation = "groups_sqlquery_rel"

    _sql_request_users_relation = "users_sqlquery_rel"

    copy_options = fields.Char(required=False, default="CSV HEADER DELIMITER ';'")

    file_format = fields.Selection([("csv", "CSV")], default="csv", required=True)

    html = fields.Html(string='HTML')
    rowcount = fields.Text(string='Rowcount')

    field_ids = fields.Many2many(
        "ir.model.fields",
        "fields_sqlquery_rel",
        "sql_id",
        "field_id",
        "Parameters",
        domain=[("model", "=", "sql.file.wizard"), ("state", "=", "manual")],
        help="Before adding parameters, make sure you have created one that fill your "
        "need in the dedicated menu with the right type and label. \n"
        "Then, when you add a parameter here, you have to include it in the SQL "
        "query in order to have dynamic values depending on the user choice.\n"
        "The format of the parameters in the SQL query must be like this :"
        " %(parameter_field_name)s. \n"
        "Example : from the variable menu, create an variable with type 'char', "
        "having field name 'x_name' and field label : 'Name' \n"
        "Then, you can create a SQL query like this : "
        "SELECT * FROM res_partner WHERE name =  %(x_name)s the variable "
        "can be used in any number of different SQL queries. \n"
        "In the SQL query, you can also include these 2 special parameters "
        "%(user_id)s and %(company_id)s which will be replaced respectively by "
        "the user executing the query and the company of the user executing the"
        " query.",
    )

    encoding = fields.Selection(
        [
            ("utf-8", "utf-8"),
            ("utf-16", "utf-16"),
            ("windows-1252", "windows-1252"),
            ("latin1", "latin1"),
            ("latin2", "latin2"),
            ("big5", "big5"),
            ("gb18030", "gb18030"),
            ("shift_jis", "shift_jis"),
            ("windows-1251", "windows-1251"),
            ("koir8_r", "koir8_r"),
        ],
        required=True,
        default="utf-8",
    )

    def export_sql_query(self):
        self.ensure_one()
        # THANH 060423 - validate sql before export
        self.button_validate_sql_expression()

        wiz = self.env["sql.file.wizard"].create({"sql_export_id": self.id})
        # no variable input, we can return the file directly
        if not self.field_ids:
            return wiz.export_sql()
        else:
            return {
                "view_mode": "form",
                "res_model": "sql.file.wizard",
                "res_id": wiz.id,
                "type": "ir.actions.act_window",
                "target": "new",
                "context": self.env.context,
                "nodestroy": True,
            }

    # THANH - new function
    def button_preview_sql(self):
        self.button_validate_sql_expression()
        self = self.sudo()
        self.ensure_one()
        self.rowcount = ''
        self.html = '<br></br>'


        if self.query:
            headers = []
            datas = []

            try:
                self.env.cr.execute(self.query)
            except Exception as e:
                raise UserError(e)

            try:
                if self.env.cr.description:
                    headers = [d[0] for d in self.env.cr.description]
                    datas = self.env.cr.fetchall()
            except Exception as e:
                raise UserError(e)

            rowcount = self.env.cr.rowcount
            self.rowcount = _("{0} row{1} processed").format(rowcount, 's' if 1 < rowcount else '')

            if headers and datas:

                header_html = "<tr style='background-color: lightgrey'> <th style='background-color:white'/>"
                header_html += "".join(
                    ["<th style='border: 1px solid black'>" + str(header) + "</th>" for header in headers])
                header_html += "</tr>"

                body_html = ""
                i = 0
                for data in datas:
                    i += 1
                    body_line = "<tr style='background-color: {0}'> <td style='border-right: 3px double; border-bottom: 1px solid black; background-color: yellow'>{1}</td>".format(
                        'cyan' if i % 2 == 0 else 'white', i)
                    for value in data:
                        display_value = ''
                        if value is not None:
                            display_value = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">",
                                                                                                          "&gt;")
                        body_line += "<td style='border: 1px solid black'>{0}</td>".format(display_value)
                    body_line += "</tr>"
                    body_html += body_line

                self.html = """<table style="text-align: center">
                          <thead>
                            {0}
                          </thead>

                          <tbody>
                            {1}
                          </tbody>
                        </table>
                        """.format(header_html, body_html)

    def _get_file_extension(self):
        self.ensure_one()
        if self.file_format == "csv":
            return "csv"

    def csv_get_data_from_query(self, variable_dict):
        self.ensure_one()
        # Execute Request
        res = self._execute_sql_request(
            params=variable_dict, mode="stdout", copy_options=self.copy_options
        )
        if self.encoding:
            res = res.decode(self.encoding)
        return res

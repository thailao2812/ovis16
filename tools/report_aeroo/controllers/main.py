# -*- encoding: utf-8 -*-
import logging
import json

from odoo.addons.web.controllers import report
from odoo import http
from odoo.http import route, request, content_disposition, serialize_exception as _serialize_exception
from odoo.tools import html_escape
_logger = logging.getLogger(__name__)


class ReportController(report.ReportController):

    MIMETYPES = {
        'txt': 'text/plain',
        'html': 'text/html',
        'doc': 'application/vnd.ms-word',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'odt': 'application/vnd.oasis.opendocument.text',
        'ods': 'application/vnd.oasis.opendocument.spreadsheet',
        'pdf': 'application/pdf',
        'sxw': 'application/vnd.sun.xml.writer',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'zip': 'application/zip',
    }

    @http.route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter not in ['aeroo', 'qweb-aeroo']:
            if 'context' in data and data.get('context') and '{' not in data.get('context') and \
                    '}' not in data.get('context'):
                data.pop('context')
            return super(ReportController, self).report_routes(reportname, docids, converter, **data)

        context = dict(request.env.context)

        report = request.env['ir.actions.report']._get_report_from_name(
            reportname)
        context.update({'preview': 'ABC'})

        if docids:
            docids = [int(i) for i in docids.split(',')]
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            if data['context'].get('lang'):
                del data['context']['lang']
            context.update(data['context'])

        file_data, out_code, filename = report.with_context(
            context).render_aeroo(docids, data=data)
        httpheaders = [
            ('Content-Type', self.MIMETYPES.get(out_code, 'application/octet-stream')),
            ('Content-Length', len(file_data)),
            ('Content-Disposition', content_disposition(filename))]
        return request.make_response(file_data, headers=httpheaders)

    # THANH 20220501 - inherit
    @route()
    def report_download(self, data, context=None):
        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]
        if type not in ['aeroo', 'qweb-aeroo']:
            return super(ReportController, self).report_download(data=data, context=context)
        try:
            reportname = url.split('/report/aeroo/')[1].split('?')[0]
            reportname, docids = reportname.split('/')
            return self.report_routes(reportname=reportname, docids=docids, converter=type)
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))

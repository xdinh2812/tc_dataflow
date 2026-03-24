from odoo import http
from odoo.http import request


class TcDataflowReportController(http.Controller):

    @http.route('/import_data', type='http', auth='public', website=True)
    def import_data_page(self, **kwargs):
        return request.render('tc_dataflow_report.import_data_page')

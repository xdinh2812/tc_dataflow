from odoo import fields, models


class TcDailyCashflowLine(models.Model):
    _name = "tc.daily.cashflow.line"
    _description = "Du lieu dong tien bao cao ngay"
    _order = "date desc, id desc"

    upload_record_id = fields.Many2one("tc.daily.upload.file", "File tai len", ondelete="cascade", index=True)
    upload_file_id = fields.Char("Ma file tai len", required=True, index=True)
    upload_filename = fields.Char("Ten file", required=True)
    upload_version = fields.Integer("Phien ban", default=1)
    line_no = fields.Integer("Dong du lieu", default=1)

    record_code = fields.Char("Ma")
    date = fields.Date("Ngay")
    cash_source = fields.Char("Nguon tien")
    account = fields.Char("Tai khoan")

    currency_id = fields.Many2one("res.currency", "Tien te", default=lambda self: self.env.company.currency_id, required=True)
    inflow = fields.Monetary("Thu vao", currency_field="currency_id")
    outflow = fields.Monetary("Chi ra", currency_field="currency_id")

    approved_by_id = fields.Many2one("res.users", "Nguoi phe duyet", readonly=True)
    approved_at = fields.Datetime("Ngay phe duyet", readonly=True)
    company_id = fields.Many2one("res.company", "Cong ty", default=lambda self: self.env.company, required=True)

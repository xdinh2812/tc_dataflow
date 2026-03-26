from odoo import fields, models


class TcDailyAssetLine(models.Model):
    _name = "tc.daily.asset.line"
    _description = "Du lieu tai san bao cao ngay"
    _order = "asset_code, id desc"

    upload_record_id = fields.Many2one("tc.daily.upload.file", "File tai len", ondelete="cascade", index=True)
    upload_file_id = fields.Char("Ma file tai len", required=True, index=True)
    upload_filename = fields.Char("Ten file", required=True)
    upload_version = fields.Integer("Phien ban", default=1)
    line_no = fields.Integer("Dong du lieu", default=1)

    record_code = fields.Char("Ma")
    asset_code = fields.Char("Ma tai san")
    asset_name = fields.Char("Ten tai san")
    department = fields.Char("Bo phan")
    status_text = fields.Char("Trang thai")

    currency_id = fields.Many2one("res.currency", "Tien te", default=lambda self: self.env.company.currency_id, required=True)
    net_value = fields.Monetary("Gia tri thuan", currency_field="currency_id")

    approved_by_id = fields.Many2one("res.users", "Nguoi phe duyet", readonly=True)
    approved_at = fields.Datetime("Ngay phe duyet", readonly=True)
    company_id = fields.Many2one("res.company", "Cong ty", default=lambda self: self.env.company, required=True)

from odoo import fields, models


class TcDailyBusinessEffectivenessLine(models.Model):
    _name = "tc.daily.business.effectiveness.line"
    _description = "Du lieu hieu qua kinh doanh bao cao ngay"
    _order = "date desc, id desc"

    upload_record_id = fields.Many2one("tc.daily.upload.file", "File tai len", ondelete="cascade", index=True)
    upload_file_id = fields.Char("Ma file tai len", required=True, index=True)
    upload_filename = fields.Char("Ten file", required=True)
    upload_version = fields.Integer("Phien ban", default=1)
    line_no = fields.Integer("Dong du lieu", default=1)

    date = fields.Date("Ngay")
    business_segment = fields.Char("Mang kinh doanh")
    legal_entity = fields.Char("Phap nhan")
    cost_center = fields.Char("Cost center")
    analysis_dimension = fields.Char("Chieu phan tich")
    report_type = fields.Char("Loai")
    item = fields.Char("Khoan muc")
    sub_item = fields.Char("Tieu muc")
    content = fields.Char("Noi dung")
    in_system = fields.Char("Co hay khong tren he thong")
    accounting_account = fields.Char("Tai khoan hach toan")
    offset_account = fields.Char("Tai khoan doi ung")
    note = fields.Text("Ghi chu")
    performer = fields.Char("Nguoi thuc hien")

    currency_id = fields.Many2one(
        "res.currency",
        "Tien te",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    amount = fields.Monetary("So tien", currency_field="currency_id")

    approved_by_id = fields.Many2one("res.users", "Nguoi phe duyet", readonly=True)
    approved_at = fields.Datetime("Ngay phe duyet", readonly=True)
    company_id = fields.Many2one(
        "res.company",
        "Cong ty",
        default=lambda self: self.env.company,
        required=True,
    )

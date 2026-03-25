from odoo import fields, models


class BusinessSegment(models.Model):
    _name = "business.segment"
    _description = "Mảng kinh doanh"
    _order = "code, name"

    name = fields.Char('Tên mảng KD', required=True)
    code = fields.Char('Mã mảng KD', required=True)

    _check_code_uniq = models.Constraint(
        'unique(code)',
        'The code of the business segment must be unique!',
    )

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class AccountDimension(models.Model):
    _name = "account.dimension"

    name = fields.Char('Tên chiều PT', required=True)
    code = fields.Char('Mã chiều PT')
    company_id = fields.Many2one('res.company', 'Công ty áp dụng', required=True,
                                 default=lambda self: self.env.company)
    value_ids = fields.One2many('account.dimension.value', 'dimension_id', 'Giá trị')
    account_ids = fields.Many2many('account.account', 'dimension_account_rel',
                                   'dimension_id', 'account_id', 'Tài khoản áp dụng')

    _check_code_uniq = models.Constraint(
        'unique(code)',
        'The code of the dimension must be unique!',
    )


class AccountDimensionValue(models.Model):
    _name = "account.dimension.value"

    dimension_id = fields.Many2one('account.dimension', 'Thuộc chiều phân tích', ondelete='cascade')
    code = fields.Char('Mã')
    name = fields.Char('Tên giá trị', required=True)
    company_id = fields.Many2one(related='dimension_id.company_id', string='Công ty')

    def name_get(self):
        return [(dimension.id, f"{dimension.dimension_id.name} / {dimension.name}") for dimension in self]

    @api.constrains('code')
    def constrains_name_code(self):
        for rec in self:
            other_rec = self.search([('code', '!=', False), ('code', '=', rec.code), ('company_id', '=', rec.company_id.id)])
            if len(other_rec) > 1:
                raise ValidationError('Đã tồn tại mã chiều phân tích này!')

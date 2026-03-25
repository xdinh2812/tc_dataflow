from odoo import fields, models


class AccountFinancialSummary(models.Model):
    _name = "account.financial.summary"
    _description = "Tổng hợp dữ liệu tài chính"
    _order = "date desc, id desc"

    date = fields.Date('Ngày', default=fields.Date.context_today)
    business_segment_id = fields.Many2one('business.segment', 'Mảng kinh doanh')
    partner_id = fields.Many2one('res.partner', 'Pháp nhân')
    cost_center_id = fields.Many2one('account.analytic.account', 'Cost center')
    data_type = fields.Selection([
        ('revenue', 'Doanh thu'),
        ('expense', 'Chi phí'),
        ('business_result', 'Hiệu quả kinh doanh'),
        ('asset', 'Tài sản'),
        ('liability', 'Công nợ'),
        ('other', 'Khác'),
    ], string='Loại', default='revenue')
    dimension_id = fields.Many2one('account.dimension', 'Chiều phân tích')
    accounting_item = fields.Char('Khoản mục')
    sub_accounting_item = fields.Char('Tiểu mục')
    content = fields.Char('Nội dung')
    in_system = fields.Selection([
        ('yes', 'Có'),
        ('no', 'Không'),
    ], string='Có hay không trên hệ thống', default='yes')
    account_id = fields.Many2one('account.account', 'Tài khoản hạch toán')
    offset_account_id = fields.Many2one('account.account', 'Tài khoản đối ứng')
    note = fields.Text('Ghi chú')
    currency_id = fields.Many2one(
        'res.currency', 'Nguyên tệ',
        default=lambda self: self.env.company.currency_id,
    )
    amount = fields.Monetary('Số tiền', currency_field='currency_id')
    company_id = fields.Many2one('res.company', 'Công ty', default=lambda self: self.env.company)

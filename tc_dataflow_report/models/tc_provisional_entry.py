from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class TcProvisionalEntry(models.Model):
    _name = "tc.provisional.entry"
    _description = "Temporary Entry"
    _order = "write_date desc, id desc"

    name = fields.Char(string="Ten chi phi", required=True, default=lambda self: self._default_name())
    reference = fields.Char(string="Ma tham chieu", required=True, copy=False, default="New", index=True)
    company_id = fields.Many2one("res.company", string="Cong ty", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", store=True, readonly=True)
    business_segment_id = fields.Many2one("business.segment", string="Mang kinh doanh")
    partner_id = fields.Many2one("res.partner", string="Phap nhan / Cong ty")
    cost_center_id = fields.Many2one("account.analytic.account", string="Cost center")
    dimension_id = fields.Many2one("account.dimension", string="Chieu phan tich")
    estimate_type = fields.Selection(
        [
            ("auto", "Phân bổ tự động"),
            ("manual", "Nhập thủ công"),
            ("formula", "Phân bổ tự động (legacy)"),
            ("fixed", "Nhập thủ công (legacy)"),
        ],
        string="Loại phân bổ",
        required=True,
        default="auto",
    )
    cycle = fields.Selection(
        [
            ("day", "Ngay"),
            ("week", "Tuan"),
            ("month", "Thang"),
        ],
        string="Chu ky tao phieu",
        required=True,
        default="day",
    )
    start_date = fields.Date(string="Ngay bat dau", required=True, default=lambda self: self._default_start_date())
    end_date = fields.Date(string="Ngay ket thuc", required=True, default=lambda self: self._default_end_date())
    total_amount = fields.Monetary(string="Tong so tien", currency_field="currency_id", required=True, default=0.0)
    allocation_method = fields.Selection(
        [
            ("equal", "Phan bo deu"),
        ],
        string="Phuong thuc phan bo",
        required=True,
        default="equal",
    )
    journal_id = fields.Many2one("account.journal", string="Nhat ky", domain="[('type', '=', 'general')]")
    debit_account_id = fields.Many2one("account.account", string="Tai khoan no")
    credit_account_id = fields.Many2one("account.account", string="Tai khoan co")
    posting_date = fields.Date(string="Ngay hach toan", default=lambda self: fields.Date.context_today(self))
    move_label = fields.Char(string="Dien giai", default=lambda self: self._default_name())
    note = fields.Text(string="Ghi chu")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("calculated", "Calculated"),
            ("generated", "Generated"),
            ("posted", "Posted"),
        ],
        string="Trang thai",
        required=True,
        default="draft",
        copy=False,
    )
    line_ids = fields.One2many("tc.provisional.entry.line", "entry_id", string="Dong phan bo", copy=False)
    move_count = fields.Integer(string="So phieu", compute="_compute_document_counts")
    performance_count = fields.Integer(string="So dong hieu qua", compute="_compute_document_counts")

    @api.model
    def _default_start_date(self):
        current_date = fields.Date.context_today(self)
        current_date = fields.Date.to_date(current_date) if isinstance(current_date, str) else current_date
        return current_date.replace(day=1)

    @api.model
    def _default_end_date(self):
        start_date = self._default_start_date()
        return start_date + relativedelta(months=1, days=-1)

    @api.model
    def _default_name(self):
        start_date = self._default_start_date()
        return "Phân bổ chi phí tạm tính tháng %s" % start_date.strftime("%m/%Y")

    @api.depends("line_ids.move_id", "line_ids.performance_id")
    def _compute_document_counts(self):
        for record in self:
            record.move_count = len(record.line_ids.mapped("move_id"))
            record.performance_count = len(record.line_ids.mapped("performance_id"))

    @api.constrains("start_date", "end_date")
    def _check_date_range(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError("Ngay ket thuc phai lon hon hoac bang ngay bat dau.")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if not record.reference or record.reference == "New":
                record.reference = self.env["ir.sequence"].next_by_code("tc.provisional.entry") or ("TMP-%s" % record.id)
        return records

    def write(self, vals):
        protected_fields = {
            "business_segment_id",
            "partner_id",
            "cost_center_id",
            "dimension_id",
            "estimate_type",
            "cycle",
            "start_date",
            "end_date",
            "total_amount",
            "allocation_method",
            "posting_date",
            "journal_id",
            "debit_account_id",
            "credit_account_id",
            "move_label",
            "name",
            "note",
        }
        dirty_fields = {
            "cycle",
            "start_date",
            "end_date",
            "total_amount",
            "allocation_method",
            "posting_date",
            "name",
            "estimate_type",
        }
        for record in self:
            if record.state in {"generated", "posted"} and protected_fields.intersection(vals):
                raise UserError("Phieu da sinh but toan hoac ghi so, khong the sua thong tin thiet lap.")
            if record.state == "calculated" and dirty_fields.intersection(vals) and record.line_ids.filtered(
                lambda line: line.move_id or line.performance_id
            ):
                raise UserError("Khong the thay doi du lieu sau khi da sinh phieu.")

        result = super().write(vals)

        if dirty_fields.intersection(vals):
            for record in self.filtered(lambda item: item.state == "calculated"):
                record.line_ids.unlink()
                record.state = "draft"

        return result

    def unlink(self):
        for record in self:
            if any(line.move_id and line.move_id.state == "posted" for line in record.line_ids):
                raise UserError("Khong the xoa phieu da ghi so.")
        return super().unlink()

    def _get_allocation_type(self):
        self.ensure_one()
        return "manual" if self.estimate_type in {"manual", "fixed"} else "auto"

    def _get_schedule_dates(self):
        self.ensure_one()
        if self._get_allocation_type() == "manual":
            if not self.posting_date:
                raise UserError("Can chon ngay hach toan cho phan bo nhap thu cong.")
            return [self.posting_date]

        if not self.start_date or not self.end_date:
            return []
        if self.start_date > self.end_date:
            raise UserError("Ngay ket thuc phai lon hon hoac bang ngay bat dau.")

        schedule_dates = []
        current_date = self.start_date
        while current_date <= self.end_date:
            schedule_dates.append(current_date)
            current_date += relativedelta(days=1)
        return schedule_dates

    def _get_distribution_amounts(self, count):
        self.ensure_one()
        if count <= 0:
            return []

        rounded_total = self.currency_id.round(self.total_amount or 0.0)
        base_amount = self.currency_id.round(rounded_total / count)
        amounts = [base_amount for _index in range(count)]
        running_total = sum(amounts[:-1]) if count > 1 else 0.0
        amounts[-1] = self.currency_id.round(rounded_total - running_total)
        return amounts

    def _prepare_move_line_vals(self, amount, is_debit, line_description):
        self.ensure_one()
        move_line_vals = {
            "name": line_description,
            "account_id": self.debit_account_id.id if is_debit else self.credit_account_id.id,
            "partner_id": self.partner_id.id or False,
            "debit": amount if is_debit else 0.0,
            "credit": 0.0 if is_debit else amount,
        }
        if self.cost_center_id and "analytic_distribution" in self.env["account.move.line"]._fields:
            move_line_vals["analytic_distribution"] = {str(self.cost_center_id.id): 100}
        return move_line_vals

    def _prepare_performance_vals(self, line):
        self.ensure_one()
        return {
            "date": line.schedule_date,
            "business_segment_id": self.business_segment_id.id or False,
            "partner_id": self.partner_id.id or False,
            "cost_center_id": self.cost_center_id.id or False,
            "dimension_id": self.dimension_id.id or False,
            "data_type": "business_result",
            "accounting_item": self.name,
            "sub_accounting_item": self.reference,
            "content": line.description,
            "in_system": "yes",
            "account_id": self.debit_account_id.id or False,
            "offset_account_id": self.credit_account_id.id or False,
            "note": self.note or False,
            "amount": line.amount,
            "company_id": self.company_id.id,
        }

    def action_calculate(self):
        for record in self:
            if record.state in {"generated", "posted"}:
                raise UserError("Phieu da sinh but toan, khong the tinh toan lai.")
            if record.total_amount <= 0:
                raise UserError("Tong so tien phai lon hon 0 de co the tinh toan.")
            schedule_dates = record._get_schedule_dates()
            if not schedule_dates:
                raise UserError("Khong co ky phan bo hop le de tinh toan.")

            record.line_ids.unlink()
            distribution_amounts = record._get_distribution_amounts(len(schedule_dates))
            line_commands = []
            is_manual = record._get_allocation_type() == "manual"
            for index, schedule_date in enumerate(schedule_dates, start=1):
                line_commands.append(
                    (
                        0,
                        0,
                        {
                            "sequence": index,
                            "schedule_date": schedule_date,
                            "amount": distribution_amounts[index - 1],
                            "description": (
                                "%s - ngay hach toan %s" % (record.name, schedule_date.strftime("%d/%m/%Y"))
                                if is_manual
                                else "%s - ky %s" % (record.name, schedule_date.strftime("%d/%m/%Y"))
                            ),
                        },
                    )
                )
            record.write(
                {
                    "state": "calculated",
                    "line_ids": line_commands,
                }
            )
        return True

    def action_generate_documents(self):
        for record in self:
            if record.state not in {"calculated", "generated"}:
                raise UserError("Can tinh toan preview truoc khi sinh phieu.")
            if not record.line_ids:
                raise UserError("Chua co dong phan bo de sinh phieu.")
            if not record.journal_id or not record.debit_account_id or not record.credit_account_id:
                raise UserError("Can khai bao nhat ky, tai khoan no va tai khoan co trong tab ke toan.")

            for line in record.line_ids.sorted("sequence"):
                if not line.performance_id:
                    line.performance_id = self.env["account.business.performance"].create(record._prepare_performance_vals(line))

                if not line.move_id:
                    move = self.env["account.move"].create(
                        {
                            "move_type": "entry",
                            "journal_id": record.journal_id.id,
                            "date": line.schedule_date or record.posting_date,
                            "ref": "%s/%s" % (record.reference, str(line.sequence).zfill(2)),
                            "line_ids": [
                                (0, 0, record._prepare_move_line_vals(line.amount, True, line.description)),
                                (0, 0, record._prepare_move_line_vals(line.amount, False, line.description)),
                            ],
                        }
                    )
                    line.move_id = move.id
            record.state = "generated"
        return True

    def action_post_documents(self):
        for record in self:
            if record.state not in {"generated", "posted"}:
                raise UserError("Can sinh phieu truoc khi ghi so.")
            moves_to_post = record.line_ids.mapped("move_id").filtered(lambda move: move.state == "draft")
            if not moves_to_post and not record.line_ids.filtered(lambda line: line.move_id):
                raise UserError("Khong tim thay but toan nhap de ghi so.")
            if moves_to_post:
                moves_to_post.action_post()
            record.state = "posted"
        return True


class TcProvisionalEntryLine(models.Model):
    _name = "tc.provisional.entry.line"
    _description = "Temporary Entry Line"
    _order = "schedule_date asc, sequence asc, id asc"

    entry_id = fields.Many2one("tc.provisional.entry", string="Phieu tam tinh", required=True, ondelete="cascade")
    sequence = fields.Integer(string="STT", default=10)
    schedule_date = fields.Date(string="Ngay phan bo", required=True)
    description = fields.Char(string="Dien giai", required=True)
    currency_id = fields.Many2one("res.currency", related="entry_id.currency_id", store=True, readonly=True)
    amount = fields.Monetary(string="So tien", currency_field="currency_id", required=True)
    move_id = fields.Many2one("account.move", string="But toan", copy=False, ondelete="set null")
    performance_id = fields.Many2one("account.business.performance", string="Dong hieu qua", copy=False, ondelete="set null")
    state = fields.Selection(
        [
            ("calculated", "Calculated"),
            ("generated", "Generated"),
            ("posted", "Posted"),
        ],
        string="Trang thai",
        compute="_compute_state",
    )

    @api.depends("move_id.state")
    def _compute_state(self):
        for line in self:
            if line.move_id and line.move_id.state == "posted":
                line.state = "posted"
            elif line.move_id:
                line.state = "generated"
            else:
                line.state = "calculated"

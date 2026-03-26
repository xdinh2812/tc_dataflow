from odoo import fields, models


class TcDailyUploadFile(models.Model):
    _name = "tc.daily.upload.file"
    _description = "File tai len bao cao ngay"
    _order = "upload_date desc, id desc"

    name = fields.Char("Ten file", required=True)
    section_key = fields.Selection(
        selection=[
            ("doanh-thu", "Doanh thu"),
            ("dong-tien", "Dong tien"),
            ("phai-thu", "Phai thu"),
            ("phai-tra", "Phai tra"),
            ("hieu-qua-kinh-doanh", "Hieu qua kinh doanh"),
            ("tai-san", "Tai san"),
        ],
        string="Danh muc",
        required=True,
        index=True,
    )
    status = fields.Selection(
        selection=[
            ("checking", "Kiem tra"),
            ("pending_approval", "Cho phe duyet"),
            ("approved", "Da duyet"),
            ("rejected", "Tu choi"),
            ("error", "Loi du lieu"),
        ],
        string="Trang thai",
        default="checking",
        required=True,
        index=True,
    )
    version = fields.Integer("Phien ban", default=1, required=True)
    upload_date = fields.Datetime("Ngay tai len", default=fields.Datetime.now, required=True, index=True)
    upload_user_id = fields.Many2one("res.users", "Nguoi tai len", default=lambda self: self.env.user, required=True)
    file_size = fields.Integer("Dung luong (bytes)", default=0)
    file_size_display = fields.Char("Dung luong", compute="_compute_file_size_display")
    mimetype = fields.Char("MIME Type")
    attachment_id = fields.Many2one("ir.attachment", "Tep goc", readonly=True, ondelete="set null")
    approval_request_id = fields.Many2one("approval.request", "Yeu cau phe duyet", readonly=True, ondelete="set null")
    approval_request_status = fields.Selection(related="approval_request_id.request_status", string="Trang thai Approvals", readonly=True)
    approval_url = fields.Char("Link phe duyet", compute="_compute_approval_url")
    preview_columns = fields.Json("Cot preview", default=list)
    preview_rows = fields.Json("Dong preview", default=list)
    preview_row_count = fields.Integer("So dong preview", compute="_compute_preview_row_count", store=True)
    imported_row_count = fields.Integer("So dong da import", default=0)
    imported_at = fields.Datetime("Ngay import", readonly=True)
    approved_by_id = fields.Many2one("res.users", "Nguoi duyet", readonly=True)
    approved_at = fields.Datetime("Ngay duyet", readonly=True)
    rejected_by_id = fields.Many2one("res.users", "Nguoi tu choi", readonly=True)
    rejected_at = fields.Datetime("Ngay tu choi", readonly=True)
    status_message = fields.Text("Thong diep trang thai")
    company_id = fields.Many2one("res.company", "Cong ty", default=lambda self: self.env.company, required=True, index=True)

    revenue_line_ids = fields.One2many("tc.daily.revenue.line", "upload_record_id", string="Dong doanh thu")
    cashflow_line_ids = fields.One2many("tc.daily.cashflow.line", "upload_record_id", string="Dong dong tien")
    receivable_line_ids = fields.One2many("tc.daily.receivable.line", "upload_record_id", string="Dong phai thu")
    payable_line_ids = fields.One2many("tc.daily.payable.line", "upload_record_id", string="Dong phai tra")
    business_effectiveness_line_ids = fields.One2many("tc.daily.business.effectiveness.line", "upload_record_id", string="Dong hieu qua kinh doanh")
    asset_line_ids = fields.One2many("tc.daily.asset.line", "upload_record_id", string="Dong tai san")

    _sql_constraints = [
        (
            "tc_daily_upload_file_section_version_company_uniq",
            "unique(section_key, version, company_id)",
            "Phien ban file da ton tai trong danh muc nay.",
        ),
    ]

    def _compute_file_size_display(self):
        units = ["B", "KB", "MB", "GB"]
        for record in self:
            size = float(record.file_size or 0)
            unit_index = 0
            while size >= 1024 and unit_index < len(units) - 1:
                size /= 1024.0
                unit_index += 1
            if unit_index == 0:
                record.file_size_display = f"{int(size)} {units[unit_index]}"
            else:
                record.file_size_display = f"{size:.1f} {units[unit_index]}"

    def _compute_preview_row_count(self):
        for record in self:
            record.preview_row_count = len(record.preview_rows or [])

    def _compute_approval_url(self):
        for record in self:
            if record.approval_request_id:
                record.approval_url = f"/odoo/action-approvals.approval_request_action/{record.approval_request_id.id}"
            else:
                record.approval_url = False

    def _get_target_model_name(self):
        self.ensure_one()
        return {
            "doanh-thu": "tc.daily.revenue.line",
            "dong-tien": "tc.daily.cashflow.line",
            "phai-thu": "tc.daily.receivable.line",
            "phai-tra": "tc.daily.payable.line",
            "hieu-qua-kinh-doanh": "tc.daily.business.effectiveness.line",
            "tai-san": "tc.daily.asset.line",
        }.get(self.section_key)

    def _parse_date(self, value):
        if not value:
            return False
        if hasattr(value, "date"):
            try:
                return value.date()
            except Exception:
                pass
        raw_value = str(value).strip()
        if not raw_value:
            return False
        for date_format in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%y"):
            try:
                from datetime import datetime as py_datetime

                return py_datetime.strptime(raw_value, date_format).date()
            except Exception:
                continue
        try:
            return fields.Date.to_date(raw_value)
        except Exception:
            return False

    def _parse_amount(self, value):
        if value in (None, "", False):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)

        raw_value = str(value).strip().replace("\xa0", "").replace(" ", "")
        if not raw_value:
            return 0.0

        is_negative = False
        if raw_value.startswith("(") and raw_value.endswith(")"):
            raw_value = raw_value[1:-1]
            is_negative = True
        if raw_value.startswith("-"):
            raw_value = raw_value[1:]
            is_negative = True

        if "," in raw_value and "." in raw_value:
            if raw_value.rfind(",") > raw_value.rfind("."):
                normalized = raw_value.replace(".", "").replace(",", ".")
            else:
                normalized = raw_value.replace(",", "")
        elif raw_value.count(",") > 1:
            normalized = raw_value.replace(",", "")
        elif raw_value.count(".") > 1:
            normalized = raw_value.replace(".", "")
        elif "," in raw_value:
            integer_part, decimal_part = raw_value.rsplit(",", 1)
            normalized = f"{integer_part}.{decimal_part}" if len(decimal_part) in {1, 2} else f"{integer_part}{decimal_part}"
        elif "." in raw_value:
            integer_part, decimal_part = raw_value.rsplit(".", 1)
            normalized = raw_value if len(decimal_part) in {1, 2} else f"{integer_part}{decimal_part}"
        else:
            normalized = raw_value

        try:
            amount_value = float(normalized)
        except ValueError:
            return 0.0
        return -amount_value if is_negative else amount_value

    def _prepare_common_line_values(self, row, line_no):
        return {
            "upload_record_id": self.id,
            "upload_file_id": str(self.id),
            "upload_filename": self.name,
            "upload_version": self.version,
            "line_no": line_no,
            "approved_by_id": self.approved_by_id.id if self.approved_by_id else False,
            "approved_at": self.approved_at,
            "company_id": self.company_id.id,
            "currency_id": self.company_id.currency_id.id,
        }

    def _prepare_line_values(self, row, line_no):
        self.ensure_one()
        values = self._prepare_common_line_values(row, line_no)
        if self.section_key == "doanh-thu":
            values.update(
                {
                    "date": self._parse_date(row.get("date")),
                    "business_segment": row.get("business_segment"),
                    "legal_entity": row.get("legal_entity"),
                    "cost_center": row.get("cost_center"),
                    "analysis_dimension": row.get("analysis_dimension"),
                    "report_type": row.get("report_type"),
                    "item": row.get("item"),
                    "sub_item": row.get("sub_item"),
                    "content": row.get("content"),
                    "in_system": row.get("in_system"),
                    "accounting_account": row.get("accounting_account"),
                    "note": row.get("note"),
                    "performer": row.get("performer"),
                    "amount": self._parse_amount(row.get("amount")),
                }
            )
        elif self.section_key == "dong-tien":
            values.update(
                {
                    "record_code": row.get("id"),
                    "date": self._parse_date(row.get("date")),
                    "cash_source": row.get("cash_source"),
                    "account": row.get("account"),
                    "inflow": self._parse_amount(row.get("inflow")),
                    "outflow": self._parse_amount(row.get("outflow")),
                }
            )
        elif self.section_key == "phai-thu":
            values.update(
                {
                    "record_code": row.get("id"),
                    "customer": row.get("customer"),
                    "invoice": row.get("invoice"),
                    "due_date": self._parse_date(row.get("due_date")),
                    "outstanding": self._parse_amount(row.get("outstanding")),
                    "status_text": row.get("status"),
                }
            )
        elif self.section_key == "phai-tra":
            values.update(
                {
                    "record_code": row.get("id"),
                    "vendor": row.get("vendor"),
                    "bill": row.get("bill"),
                    "due_date": self._parse_date(row.get("due_date")),
                    "payable": self._parse_amount(row.get("payable")),
                    "status_text": row.get("status"),
                }
            )
        elif self.section_key == "hieu-qua-kinh-doanh":
            values.update(
                {
                    "date": self._parse_date(row.get("date")),
                    "business_segment": row.get("business_segment"),
                    "legal_entity": row.get("legal_entity"),
                    "cost_center": row.get("cost_center"),
                    "analysis_dimension": row.get("analysis_dimension"),
                    "report_type": row.get("report_type"),
                    "item": row.get("item"),
                    "sub_item": row.get("sub_item"),
                    "content": row.get("content"),
                    "in_system": row.get("in_system"),
                    "accounting_account": row.get("accounting_account"),
                    "offset_account": row.get("offset_account"),
                    "note": row.get("note"),
                    "performer": row.get("performer"),
                    "amount": self._parse_amount(row.get("amount")),
                }
            )
        elif self.section_key == "tai-san":
            values.update(
                {
                    "record_code": row.get("id"),
                    "asset_code": row.get("asset_code"),
                    "asset_name": row.get("asset_name"),
                    "department": row.get("department"),
                    "net_value": self._parse_amount(row.get("net_value")),
                    "status_text": row.get("status"),
                }
            )
        return values

    def _import_preview_rows(self):
        for record in self:
            if record.imported_at or record.status != "approved":
                continue
            model_name = record._get_target_model_name()
            preview_rows = list(record.preview_rows or [])
            if not model_name or not preview_rows:
                record.write(
                    {
                        "imported_row_count": len(preview_rows),
                        "imported_at": fields.Datetime.now(),
                    }
                )
                continue

            model = self.env[model_name].sudo()
            values_list = [record._prepare_line_values(row, line_no) for line_no, row in enumerate(preview_rows, 1)]
            model.create(values_list)
            record.write(
                {
                    "imported_row_count": len(values_list),
                    "imported_at": fields.Datetime.now(),
                }
            )

    def _sync_with_approval_request(self):
        for record in self:
            request = record.approval_request_id
            if not request or record.status == "error":
                continue

            if request.request_status == "approved":
                approver_user = request.write_uid or self.env.user
                vals = {
                    "status": "approved",
                    "approved_by_id": approver_user.id,
                    "approved_at": record.approved_at or fields.Datetime.now(),
                    "rejected_by_id": False,
                    "rejected_at": False,
                    "status_message": False,
                }
                if record.status != "approved":
                    record.write(vals)
                record._import_preview_rows()
            elif request.request_status == "refused":
                if record.status != "rejected":
                    record.write(
                        {
                            "status": "rejected",
                            "rejected_by_id": request.write_uid.id if request.write_uid else self.env.user.id,
                            "rejected_at": fields.Datetime.now(),
                            "status_message": "Yeu cau da bi tu choi trong Approvals.",
                        }
                    )
            elif request.request_status == "cancel":
                if record.status != "rejected":
                    record.write(
                        {
                            "status": "rejected",
                            "status_message": "Yeu cau phe duyet da bi huy.",
                        }
                    )
            elif request.request_status in {"new", "pending"}:
                if record.status not in {"pending_approval", "error"}:
                    record.write({"status": "pending_approval"})

    def can_user_review(self, user):
        self.ensure_one()
        if not self.approval_request_id or self.status != "pending_approval":
            return False
        request = self.approval_request_id.sudo()
        if user.has_group("approvals.group_approval_manager"):
            return True
        approver = request.approver_ids.filtered(lambda item: item.user_id == user)
        return bool(approver.filtered(lambda item: item.status == "pending"))

    def force_refuse(self):
        self.ensure_one()
        request = self.approval_request_id.sudo()
        approvers = request.approver_ids.filtered(lambda item: item.status in ("new", "pending", "waiting"))
        approvers.write({"status": "refused"})
        request._cancel_activities()
        request.message_post(body="The request has been refused by an Approval Officer")
        self._sync_with_approval_request()

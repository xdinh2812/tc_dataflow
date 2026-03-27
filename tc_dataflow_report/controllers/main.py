import base64
import io
import json
import mimetypes
import re
import unicodedata
import uuid
import zipfile
from datetime import date, datetime, timedelta
from xml.etree import ElementTree as ET

from odoo import fields, http
from odoo.http import request


class TcDataflowReportController(http.Controller):
    def _get_user_initials(self, user_name):
        parts = [part[0].upper() for part in (user_name or "").split() if part]
        if not parts:
            return "TC"
        return "".join(parts[:2])

    def _get_today(self):
        today_value = fields.Date.context_today(request.env.user)
        return fields.Date.to_date(today_value) if isinstance(today_value, str) else today_value

    def _get_daily_filter_date(self, raw_value=None):
        parsed_date = self._coerce_daily_date(raw_value) if raw_value else None
        return parsed_date or self._get_today()

    def _get_daily_datetime_range(self, filter_date):
        start_datetime = datetime.combine(filter_date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        return (
            fields.Datetime.to_string(start_datetime),
            fields.Datetime.to_string(end_datetime),
        )

    def _get_daily_upload_domain(self, section_key=None, filter_date=None):
        domain = [("company_id", "=", request.env.company.id)]
        if section_key:
            domain.append(("section_key", "=", section_key))
        if filter_date:
            start_datetime, end_datetime = self._get_daily_datetime_range(filter_date)
            domain.extend(
                [
                    ("upload_date", ">=", start_datetime),
                    ("upload_date", "<", end_datetime),
                ]
            )
        return domain

    def _build_recent_days(self, anchor_date):
        date_from = anchor_date - timedelta(days=4)
        start_datetime, _end_datetime = self._get_daily_datetime_range(date_from)
        _unused_start, end_datetime = self._get_daily_datetime_range(anchor_date)
        upload_records = self._get_daily_upload_model().search(
            [
                ("company_id", "=", request.env.company.id),
                ("upload_date", ">=", start_datetime),
                ("upload_date", "<", end_datetime),
            ],
            order="upload_date desc, id desc",
        )
        upload_records._sync_with_approval_request()

        records_by_day = {}
        for upload_record in upload_records:
            if not upload_record.upload_date:
                continue
            local_upload_date = fields.Datetime.context_timestamp(request.env.user, upload_record.upload_date).date()
            records_by_day.setdefault(local_upload_date, request.env["tc.daily.upload.file"])
            records_by_day[local_upload_date] |= upload_record

        recent_days = []
        for offset in range(5):
            current_day = anchor_date - timedelta(days=offset)
            day_records = records_by_day.get(current_day, request.env["tc.daily.upload.file"])
            total_count = len(day_records)
            rejected_count = len(day_records.filtered(lambda record: record.status in {"rejected", "error"}))
            approved_count = len(day_records.filtered(lambda record: record.status == "approved"))
            checking_count = len(day_records.filtered(lambda record: record.status == "checking"))
            pending_count = len(day_records.filtered(lambda record: record.status == "pending_approval"))

            if rejected_count:
                status = "CÓ LỖI"
                status_class = "is-error"
                note = f"{total_count} file | {rejected_count} file bị từ chối/lỗi"
            elif total_count and approved_count == total_count:
                status = "ĐÃ DUYỆT"
                status_class = "is-approved"
                note = f"{approved_count}/{total_count} file đã duyệt"
            elif total_count:
                status = "ĐÃ LÀM"
                status_class = "is-done"
                note_parts = [f"{total_count} file"]
                if checking_count:
                    note_parts.append(f"{checking_count} file kiểm tra")
                if pending_count:
                    note_parts.append(f"{pending_count} file chờ duyệt")
                note = " | ".join(note_parts)
            else:
                status = "CHƯA LÀM"
                status_class = "is-pending"
                note = "Chưa có file tải lên"

            recent_days.append(
                {
                    "date": current_day.strftime("%d/%m/%Y"),
                    "status": status,
                    "status_class": status_class,
                    "note": note,
                }
            )
        return recent_days

    def _build_daily_shared_context(self, filter_date):
        return {
            "selected_date_display": filter_date.strftime("%d/%m/%Y"),
            "selected_date_input": filter_date.isoformat(),
            "recent_days": self._build_recent_days(filter_date),
        }

    def _build_nav_items(self, current_view):
        return [
            {
                "label": "Báo cáo ngày",
                "icon": "edit_note",
                "active": current_view == "daily",
                "href": "/home",
            },
            {
                "label": "Tạm tính",
                "icon": "assessment",
                "active": current_view == "temporary",
                "href": "/home/tam-tinh",
            },
            {
                "label": "Kế hoạch",
                "icon": "dashboard",
                "active": current_view == "plan",
                "href": "/home/ke-hoach",
            },
            {
                "label": "Tổng hợp",
                "icon": "settings",
                "active": False,
                "href": "#",
            },
        ]

    def _build_base_context(self, current_view, filter_date=None):
        selected_date = filter_date or self._get_today()
        user = request.env.user
        titles = {
            "daily": "Báo cáo tài chính - Kế toán",
            "temporary": "Báo cáo tài chính - Tạm tính",
            "plan": "Kế hoạch kinh doanh",
        }

        context = {
            "page_title": titles[current_view],
            "brand_name": "THỊNH CƯỜNG",
            "current_view": current_view,
            "user_name": user.name,
            "user_role": "FINANCIAL DIRECTOR",
            "user_initials": self._get_user_initials(user.name),
            "nav_items": self._build_nav_items(current_view),
            "org_filters": [
                {"label": "Toàn công ty", "checked": True},
                {"label": "Cost Center 1", "checked": False},
                {"label": "Cost Center 2", "checked": False},
                {"label": "Chi nhánh HN", "checked": False},
            ],
            "sidebar_period_value": None,
        }
        context.update(self._build_daily_shared_context(selected_date))
        return context

    def _get_daily_section_definitions(self):
        return {
            "doanh-thu": {
                "label": "1. DOANH THU",
                "short_label": "Doanh thu",
                "fields": [
                    {"label": "Ngày", "field": "date", "aliases": ["ngày", "ngay", "date"], "required": True},
                    {"label": "Mảng kinh doanh", "field": "business_segment", "aliases": ["mảng kinh doanh", "mang kinh doanh", "business segment"], "required": True},
                    {"label": "Pháp nhân", "field": "legal_entity", "aliases": ["pháp nhân", "phap nhan", "legal entity"], "required": True},
                    {"label": "Cost center", "field": "cost_center", "aliases": ["cost center", "costcenter"], "required": True},
                    {"label": "Chiều phân tích", "field": "analysis_dimension", "aliases": ["chiều phân tích", "chieu phan tich", "chiều pt", "analysis"], "required": False},
                    {"label": "Loại", "field": "report_type", "aliases": ["loại", "loai", "type"], "required": True},
                    {"label": "Khoản mục", "field": "item", "aliases": ["khoản mục", "khoan muc", "item"], "required": True},
                    {"label": "Tiểu mục", "field": "sub_item", "aliases": ["tiểu mục", "tieu muc", "sub item"], "required": False},
                    {"label": "Nội dung", "field": "content", "aliases": ["nội dung", "noi dung", "content"], "required": False},
                    {"label": "Có hay không trên hệ thống", "field": "in_system", "aliases": ["có hay không trên hệ thống", "co hay khong tren he thong", "in system"], "required": False},
                    {"label": "Tài khoản hạch toán", "field": "accounting_account", "aliases": ["tài khoản hạch toán", "tai khoan hach toan", "tài khoản", "tai khoan"], "required": False},
                    {"label": "Ghi chú", "field": "note", "aliases": ["ghi chú", "ghi chu", "note"], "required": False},
                    {"label": "Người thực hiện", "field": "performer", "aliases": ["người thực hiện", "nguoi thuc hien", "performer"], "required": False},
                    {"label": "Số tiền", "field": "amount", "aliases": ["số tiền", "so tien", "amount"], "required": True, "header_class": "is-right", "cell_class": "is-right is-strong"},
                ],
            },
            "dong-tien": {
                "label": "2. DÒNG TIỀN",
                "short_label": "Dòng tiền",
                "fields": [
                    {"label": "Mã", "field": "id", "aliases": ["mã", "ma", "id", "code"], "required": False, "fallback": "sequence", "cell_class": "is-strong"},
                    {"label": "Ngày", "field": "date", "aliases": ["ngày", "ngay", "date"], "required": True},
                    {"label": "Nguồn tiền", "field": "cash_source", "aliases": ["nguồn tiền", "nguon tien", "cash source"], "required": True},
                    {"label": "Tài khoản", "field": "account", "aliases": ["tài khoản", "tai khoan", "account"], "required": True},
                    {"label": "Thu vào", "field": "inflow", "aliases": ["thu vào", "thu vao", "inflow"], "required": False, "header_class": "is-right", "cell_class": "is-right is-strong"},
                    {"label": "Chi ra", "field": "outflow", "aliases": ["chi ra", "outflow"], "required": False, "header_class": "is-right", "cell_class": "is-right"},
                ],
            },
            "phai-thu": {
                "label": "3. PHẢI THU",
                "short_label": "Phải thu",
                "fields": [
                    {"label": "Mã", "field": "id", "aliases": ["mã", "ma", "id", "code"], "required": False, "fallback": "sequence", "cell_class": "is-strong"},
                    {"label": "Khách hàng", "field": "customer", "aliases": ["khách hàng", "khach hang", "customer"], "required": True},
                    {"label": "Hóa đơn", "field": "invoice", "aliases": ["hóa đơn", "hoa don", "invoice", "bill"], "required": True},
                    {"label": "Ngày đến hạn", "field": "due_date", "aliases": ["ngày đến hạn", "ngay den han", "due date"], "required": False},
                    {"label": "Công nợ", "field": "outstanding", "aliases": ["công nợ", "cong no", "outstanding", "amount"], "required": True, "header_class": "is-right", "cell_class": "is-right is-strong"},
                    {"label": "Trạng thái", "field": "status", "aliases": ["trạng thái", "trang thai", "status"], "required": False},
                ],
            },
            "phai-tra": {
                "label": "4. PHẢI TRẢ",
                "short_label": "Phải trả",
                "fields": [
                    {"label": "Mã", "field": "id", "aliases": ["mã", "ma", "id", "code"], "required": False, "fallback": "sequence", "cell_class": "is-strong"},
                    {"label": "Nhà cung cấp", "field": "vendor", "aliases": ["nhà cung cấp", "nha cung cap", "vendor", "supplier"], "required": True},
                    {"label": "Hóa đơn", "field": "bill", "aliases": ["hóa đơn", "hoa don", "bill", "invoice"], "required": True},
                    {"label": "Ngày đến hạn", "field": "due_date", "aliases": ["ngày đến hạn", "ngay den han", "due date"], "required": False},
                    {"label": "Phải trả", "field": "payable", "aliases": ["phải trả", "phai tra", "payable", "amount"], "required": True, "header_class": "is-right", "cell_class": "is-right is-strong"},
                    {"label": "Trạng thái", "field": "status", "aliases": ["trạng thái", "trang thai", "status"], "required": False},
                ],
            },
            "hieu-qua-kinh-doanh": {
                "label": "5. HIỆU QUẢ KINH DOANH",
                "short_label": "Hiệu quả kinh doanh",
                "fields": [
                    {"label": "Ngày", "field": "date", "aliases": ["ngày", "ngay", "date"], "required": True},
                    {"label": "Mảng kinh doanh", "field": "business_segment", "aliases": ["mảng kinh doanh", "mang kinh doanh", "business segment"], "required": True},
                    {"label": "Pháp nhân", "field": "legal_entity", "aliases": ["pháp nhân", "phap nhan", "legal entity"], "required": True},
                    {"label": "Cost center", "field": "cost_center", "aliases": ["cost center", "costcenter"], "required": True},
                    {"label": "Chiều phân tích", "field": "analysis_dimension", "aliases": ["chiều phân tích", "chieu phan tich", "chiều pt", "analysis"], "required": False},
                    {"label": "Loại", "field": "report_type", "aliases": ["loại", "loai", "type"], "required": True},
                    {"label": "Khoản mục", "field": "item", "aliases": ["khoản mục", "khoan muc", "item"], "required": True},
                    {"label": "Tiểu mục", "field": "sub_item", "aliases": ["tiểu mục", "tieu muc", "sub item"], "required": False},
                    {"label": "Nội dung", "field": "content", "aliases": ["nội dung", "noi dung", "content"], "required": False},
                    {"label": "Có hay không trên hệ thống", "field": "in_system", "aliases": ["có hay không trên hệ thống", "co hay khong tren he thong", "in system"], "required": False},
                    {"label": "Tài khoản hạch toán", "field": "accounting_account", "aliases": ["tài khoản hạch toán", "tai khoan hach toan"], "required": False},
                    {"label": "Tài khoản đối ứng", "field": "offset_account", "aliases": ["tài khoản đối ứng", "tai khoan doi ung"], "required": False},
                    {"label": "Ghi chú", "field": "note", "aliases": ["ghi chú", "ghi chu", "note"], "required": False},
                    {"label": "Người thực hiện", "field": "performer", "aliases": ["người thực hiện", "nguoi thuc hien", "performer"], "required": False},
                    {"label": "Số tiền", "field": "amount", "aliases": ["số tiền", "so tien", "amount"], "required": True, "header_class": "is-right", "cell_class": "is-right is-strong"},
                ],
            },
            "tai-san": {
                "label": "6. TÀI SẢN",
                "short_label": "Tài sản",
                "fields": [
                    {"label": "Mã", "field": "id", "aliases": ["mã", "ma", "id", "code"], "required": False, "fallback": "sequence", "cell_class": "is-strong"},
                    {"label": "Mã tài sản", "field": "asset_code", "aliases": ["mã tài sản", "ma tai san", "asset code"], "required": True},
                    {"label": "Tên tài sản", "field": "asset_name", "aliases": ["tên tài sản", "ten tai san", "asset name"], "required": True},
                    {"label": "Bộ phận", "field": "department", "aliases": ["bộ phận", "bo phan", "department"], "required": False},
                    {"label": "Giá trị thuần", "field": "net_value", "aliases": ["giá trị thuần", "gia tri thuan", "net value"], "required": True, "header_class": "is-right", "cell_class": "is-right is-strong"},
                    {"label": "Trạng thái", "field": "status", "aliases": ["trạng thái", "trang thai", "status"], "required": False},
                ],
            },
        }

    def _get_daily_session_state(self):
        session_state = request.session.get("tc_daily_upload_state")
        return session_state if isinstance(session_state, dict) else {}

    def _set_daily_session_state(self, session_state):
        request.session["tc_daily_upload_state"] = session_state

    def _build_daily_status_config(self, status_code, status_message=None):
        if status_code == "checking":
            return {
                "status_code": "checking",
                "status": "Kiểm tra",
                "status_icon": "fact_check",
                "status_class": "is-done",
            }
        if status_code == "approved":
            return {
                "status_code": "approved",
                "status": "Đã duyệt",
                "status_icon": "check_circle",
                "status_class": "is-approved",
            }
        if status_code == "rejected":
            return {
                "status_code": "rejected",
                "status": "Từ chối",
                "status_icon": "cancel",
                "status_class": "is-error",
            }
        if status_code == "error":
            return {
                "status_code": "error",
                "status": status_message or "Lỗi dữ liệu",
                "status_icon": "warning",
                "status_class": "is-error",
            }
        return {
            "status_code": "pending_approval",
            "status": "Chờ phê duyệt",
            "status_icon": "schedule",
            "status_class": "is-pending",
        }

    def _get_daily_upload_model(self):
        return request.env["tc.daily.upload.file"].sudo()

    def _get_daily_approval_category(self):
        return request.env.ref("tc_dataflow_report.tc_approval_category_daily", raise_if_not_found=False)

    def _build_daily_file_actions(self, upload_record, current_file_id=None):
        actions = []
        is_open = str(current_file_id or "") == str(upload_record.id)
        can_review = upload_record.can_user_review(request.env.user)

        if upload_record.status == "checking":
            actions.append(
                {
                    "key": "submit",
                    "label": "Gửi phê duyệt",
                    "icon": "send",
                    "style": "primary",
                    "disabled": False,
                }
            )

        if upload_record.status == "pending_approval" and can_review:
            actions.append(
                {
                    "key": "approve",
                    "label": "Phê duyệt",
                    "icon": "task_alt",
                    "style": "primary",
                    "disabled": False,
                }
            )
            actions.append(
                {
                    "key": "reject",
                    "label": "Từ chối",
                    "icon": "close",
                    "style": "danger",
                    "disabled": False,
                }
            )

        if upload_record.preview_row_count:
            actions.append(
                {
                    "key": "toggle_detail",
                    "label": "Ẩn chi tiết" if is_open else "Xem chi tiết",
                    "icon": "visibility_off" if is_open else "visibility",
                    "style": "ghost",
                    "disabled": False,
                }
            )

        if not actions:
            actions.append(
                {
                    "key": "",
                    "label": "Không có thao tác",
                    "icon": "remove",
                    "style": "ghost",
                    "disabled": True,
                }
            )

        return actions

    def _build_daily_file_entry(self, upload_record, current_file_id=None):
        entry = {
            "id": str(upload_record.id),
            "name": upload_record.name,
            "version": str(upload_record.version),
            "uploaded_at": fields.Datetime.to_string(upload_record.upload_date) if upload_record.upload_date else "",
            "uploaded_at_display": fields.Datetime.context_timestamp(request.env.user, upload_record.upload_date).strftime("%d/%m/%Y %H:%M") if upload_record.upload_date else "",
            "size": upload_record.file_size,
            "size_display": upload_record.file_size_display,
            "status_message": upload_record.status_message or "",
            "approval_url": upload_record.approval_url or "",
        }
        entry.update(self._build_daily_status_config(upload_record.status, status_message=upload_record.status_message))
        entry["actions"] = self._build_daily_file_actions(upload_record, current_file_id=current_file_id)
        return entry

    def _get_daily_upload_records(self, section_key=None, limit=20, filter_date=None):
        domain = self._get_daily_upload_domain(section_key=section_key, filter_date=filter_date)
        records = self._get_daily_upload_model().search(domain, order="upload_date desc, id desc", limit=limit)
        records._sync_with_approval_request()
        return records

    def _get_daily_active_record(self, upload_records):
        return upload_records.filtered(lambda record: record.status != "rejected")[:1]

    def _get_daily_approved_record(self, upload_records):
        return upload_records.filtered(lambda record: record.status == "approved")[:1]

    def _get_daily_preview_record(self, upload_records, preview_file=None):
        if preview_file:
            return preview_file
        approved_record = self._get_daily_approved_record(upload_records)
        return approved_record if approved_record else self._get_daily_upload_model()

    def _build_daily_sections(self, filter_date=None):
        sections = {}
        for key, definition in self._get_daily_section_definitions().items():
            upload_records = self._get_daily_upload_records(key, filter_date=filter_date)
            active_record = self._get_daily_active_record(upload_records)
            approved_record = self._get_daily_approved_record(upload_records)
            preview_record = self._get_daily_preview_record(upload_records)
            preview_payload = self._build_daily_preview_payload(
                (preview_record.preview_columns if preview_record else []) or [],
                (preview_record.preview_rows if preview_record else []) or [],
                page=1,
            )
            sections[key] = {
                "label": definition["label"],
                "short_label": definition["short_label"],
                "uploaded_files_title": f"Danh sách file đã tải lên - {definition['short_label']}",
                "preview_title": f"Xem trước dữ liệu - {definition['short_label']}",
                "uploaded_files": [
                    self._build_daily_file_entry(record, current_file_id=preview_record.id if preview_record else None)
                    for record in upload_records
                ],
                "preview_columns": preview_payload["preview_columns"],
                "preview_rows": preview_payload["preview_rows"],
                "preview_pagination": preview_payload["preview_pagination"],
                "checking_count": len(upload_records.filtered(lambda record: record.status == "checking")),
                "hide_upload_zone": bool(active_record),
                "current_file_id": str(preview_record.id) if preview_record else "",
            }
        return sections

    def _make_daily_json_response(self, payload, status=200):
        response = request.make_response(
            json.dumps(payload, ensure_ascii=False),
            headers=[("Content-Type", "application/json; charset=utf-8")],
        )
        response.status_code = status
        return response

    def _xlsx_column_index(self, cell_reference):
        letters = "".join(char for char in (cell_reference or "") if char.isalpha()).upper()
        if not letters:
            return 0
        index = 0
        for letter in letters:
            index = (index * 26) + (ord(letter) - 64)
        return max(index - 1, 0)

    def _xlsx_read_shared_strings(self, archive):
        if "xl/sharedStrings.xml" not in archive.namelist():
            return []

        namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        values = []
        for item in shared_root.findall(f"{namespace}si"):
            texts = [node.text or "" for node in item.iterfind(f".//{namespace}t")]
            values.append("".join(texts))
        return values

    def _get_daily_preview_page_size(self):
        return 100

    def _coerce_positive_int(self, value, default=1):
        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            return default
        return parsed_value if parsed_value > 0 else default

    def _xlsx_is_date_format(self, format_code):
        if not format_code:
            return False

        normalized = re.sub(r'".*?"', "", str(format_code).lower())
        normalized = re.sub(r"\\.", "", normalized)
        normalized = re.sub(r"\[[^\]]+\]", "", normalized)
        normalized = normalized.replace("_", "").replace("*", "")
        if "general" in normalized:
            return False
        if "am/pm" in normalized or "a/p" in normalized:
            return True
        if any(token in normalized for token in ("yy", "dd", "hh", "ss")):
            return True
        return "m" in normalized and any(token in normalized for token in ("/", "-", "d", "y", "h", ":"))

    def _xlsx_read_date_style_ids(self, archive, namespaces):
        if "xl/styles.xml" not in archive.namelist():
            return set()

        built_in_date_format_ids = {14, 15, 16, 17, 18, 19, 20, 21, 22, 27, 30, 36, 45, 46, 47, 50, 57}
        styles_root = ET.fromstring(archive.read("xl/styles.xml"))
        custom_formats = {}
        num_formats = styles_root.find("main:numFmts", namespaces)
        if num_formats is not None:
            for num_format in num_formats.findall("main:numFmt", namespaces):
                try:
                    custom_formats[int(num_format.attrib.get("numFmtId"))] = num_format.attrib.get("formatCode")
                except (TypeError, ValueError):
                    continue

        date_style_ids = set()
        cell_xfs = styles_root.find("main:cellXfs", namespaces)
        if cell_xfs is None:
            return date_style_ids

        for style_index, style_node in enumerate(cell_xfs.findall("main:xf", namespaces)):
            try:
                num_format_id = int(style_node.attrib.get("numFmtId"))
            except (TypeError, ValueError):
                continue
            if num_format_id in built_in_date_format_ids or self._xlsx_is_date_format(custom_formats.get(num_format_id)):
                date_style_ids.add(style_index)
        return date_style_ids

    def _excel_serial_to_datetime(self, raw_value, use_1904=False):
        try:
            serial_value = float(raw_value)
        except (TypeError, ValueError):
            return None

        base_date = datetime(1904, 1, 1) if use_1904 else datetime(1899, 12, 30)
        return base_date + timedelta(days=serial_value)

    def _xlsx_cell_value(self, cell, shared_strings, date_style_ids, use_1904, namespaces):
        def build_cell_info(value="", display="", kind="text"):
            return {
                "value": value,
                "display": display,
                "kind": kind,
            }

        cell_type = cell.attrib.get("t")
        if cell_type == "inlineStr":
            text_value = "".join(node.text or "" for node in cell.findall(".//main:t", namespaces)).strip()
            return build_cell_info(text_value, text_value, "text")

        value_node = cell.find("main:v", namespaces)
        if value_node is None or value_node.text is None:
            return build_cell_info()

        raw_value = value_node.text.strip()
        if cell_type == "s":
            try:
                text_value = shared_strings[int(raw_value)]
            except (IndexError, ValueError):
                text_value = ""
            return build_cell_info(text_value, text_value, "text")

        if cell_type == "b":
            return build_cell_info(raw_value == "1", "TRUE" if raw_value == "1" else "FALSE", "boolean")

        if cell_type == "d":
            date_value = self._coerce_daily_date(raw_value)
            if date_value:
                return build_cell_info(date_value, date_value.strftime("%d/%m/%Y"), "date")
            return build_cell_info(raw_value, raw_value, "text")

        if cell_type == "str":
            return build_cell_info(raw_value, raw_value, "text")

        try:
            style_id = int(cell.attrib.get("s") or 0)
        except (TypeError, ValueError):
            style_id = 0

        if style_id in date_style_ids:
            date_value = self._excel_serial_to_datetime(raw_value, use_1904=use_1904)
            if date_value:
                return build_cell_info(date_value, date_value.strftime("%d/%m/%Y"), "date")

        try:
            numeric_value = float(raw_value)
        except ValueError:
            return build_cell_info(raw_value, raw_value, "text")

        if numeric_value.is_integer():
            numeric_value = int(numeric_value)
        return build_cell_info(numeric_value, raw_value, "number")

    def _read_xlsx_rows(self, file_content):
        namespaces = {
            "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
            "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
            "doc_rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        }

        with zipfile.ZipFile(io.BytesIO(file_content)) as archive:
            workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
            workbook_rels_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
            workbook_properties = workbook_root.find("main:workbookPr", namespaces)
            use_1904_date_system = bool(workbook_properties is not None and workbook_properties.attrib.get("date1904") in {"1", "true", "True"})

            first_sheet = workbook_root.find("main:sheets/main:sheet", namespaces)
            if first_sheet is None:
                raise ValueError("File Excel không có sheet dữ liệu.")

            relation_id = first_sheet.attrib.get(f"{{{namespaces['doc_rel']}}}id")
            if not relation_id:
                raise ValueError("Không tìm thấy sheet dữ liệu trong file Excel.")

            sheet_target = None
            for relation in workbook_rels_root.findall("rel:Relationship", namespaces):
                if relation.attrib.get("Id") == relation_id:
                    sheet_target = relation.attrib.get("Target")
                    break

            if not sheet_target:
                raise ValueError("Không xác định được sheet cần đọc.")

            sheet_path = sheet_target.lstrip("/")
            if not sheet_path.startswith("xl/"):
                sheet_path = f"xl/{sheet_path}"

            shared_strings = self._xlsx_read_shared_strings(archive)
            date_style_ids = self._xlsx_read_date_style_ids(archive, namespaces)
            sheet_root = ET.fromstring(archive.read(sheet_path))
            rows = []
            for row in sheet_root.findall("main:sheetData/main:row", namespaces):
                row_values = {}
                max_index = -1
                for cell in row.findall("main:c", namespaces):
                    column_index = self._xlsx_column_index(cell.attrib.get("r"))
                    row_values[column_index] = self._xlsx_cell_value(
                        cell,
                        shared_strings,
                        date_style_ids,
                        use_1904_date_system,
                        namespaces,
                    )
                    max_index = max(max_index, column_index)
                if max_index < 0:
                    rows.append([])
                    continue
                rows.append([row_values.get(index) for index in range(max_index + 1)])
            return rows

    def _normalize_header_key(self, value):
        normalized = unicodedata.normalize("NFKD", (value or "").strip().lower())
        stripped = "".join(char for char in normalized if not unicodedata.combining(char))
        return "".join(char for char in stripped if char.isalnum())

    def _excel_cell_display_value(self, cell_info):
        if not isinstance(cell_info, dict):
            return str(cell_info or "").strip()
        return str(cell_info.get("display") or "").strip()

    def _daily_field_type(self, field_definition):
        explicit_type = field_definition.get("field_type")
        if explicit_type:
            return explicit_type

        field_name = field_definition.get("field")
        if field_name in {"date", "due_date"}:
            return "date"
        if field_name in {"amount", "inflow", "outflow", "outstanding", "payable", "net_value"}:
            return "amount"
        return "text"

    def _build_daily_preview_payload(self, preview_columns, preview_rows, page=1):
        columns = list(preview_columns or [])
        rows = list(preview_rows or [])
        page_size = self._get_daily_preview_page_size()
        total_rows = len(rows)
        total_pages = max((total_rows + page_size - 1) // page_size, 1)
        current_page = min(self._coerce_positive_int(page, default=1), total_pages)
        start_index = (current_page - 1) * page_size
        end_index = start_index + page_size
        page_rows = rows[start_index:end_index]
        range_start = start_index + 1 if total_rows else 0
        range_end = min(end_index, total_rows)

        return {
            "preview_columns": columns,
            "preview_rows": page_rows,
            "preview_pagination": {
                "page": current_page,
                "page_size": page_size,
                "total_rows": total_rows,
                "total_pages": total_pages,
                "has_prev": bool(columns) and current_page > 1,
                "has_next": bool(columns) and current_page < total_pages,
                "range_start": range_start,
                "range_end": range_end,
                "summary": f"Hiển thị {range_start}-{range_end} trên {total_rows} dòng dữ liệu." if total_rows else "Chưa có dòng dữ liệu nào.",
            },
        }

    def _get_daily_upload_record(self, section_key, file_id):
        if not file_id:
            return self._get_daily_upload_model()
        try:
            record_id = int(file_id)
        except (TypeError, ValueError):
            return self._get_daily_upload_model()
        record = self._get_daily_upload_model().search(
            [
                ("id", "=", record_id),
                ("section_key", "=", section_key),
                ("company_id", "=", request.env.company.id),
            ],
            limit=1,
        )
        record._sync_with_approval_request()
        return record

    def _build_daily_section_response(self, section_key, preview_file=None, page=1, filter_date=None):
        upload_records = self._get_daily_upload_records(section_key, filter_date=filter_date)
        preview_record = self._get_daily_preview_record(upload_records, preview_file=preview_file)
        active_record = self._get_daily_active_record(upload_records)
        preview_payload = self._build_daily_preview_payload(
            (preview_record.preview_columns if preview_record else []) or [],
            (preview_record.preview_rows if preview_record else []) or [],
            page=page,
        )
        response_payload = {
            "uploaded_files": [
                self._build_daily_file_entry(record, current_file_id=preview_record.id if preview_record else None)
                for record in upload_records
            ],
            "current_file_id": str(preview_record.id) if preview_record else "",
            "checking_count": len(upload_records.filtered(lambda record: record.status == "checking")),
            "hide_upload_zone": bool(active_record),
        }
        response_payload.update(preview_payload)
        return response_payload

    def _format_daily_preview_date(self, value):
        date_value = self._coerce_daily_date(value)
        if not date_value:
            return str(value or "").strip()
        return date_value.strftime("%d/%m/%Y")

    def _coerce_daily_amount(self, value):
        if value in (None, "", False):
            return None
        if isinstance(value, (int, float)):
            return float(value)

        raw_value = str(value).strip().replace("\xa0", "").replace(" ", "")
        if not raw_value:
            return None

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
            return None
        return -amount_value if is_negative else amount_value

    def _format_daily_preview_amount(self, value):
        amount_value = self._coerce_daily_amount(value)
        if amount_value is None:
            return str(value or "").strip()

        rounded_value = round(amount_value)
        if abs(amount_value - rounded_value) < 1e-9:
            return f"{int(rounded_value):,}"
        return f"{amount_value:,.2f}".rstrip("0").rstrip(".")

    def _format_daily_preview_value(self, field_definition, cell_info):
        field_type = self._daily_field_type(field_definition)
        if field_type == "date":
            raw_value = cell_info.get("value") if isinstance(cell_info, dict) and cell_info.get("kind") == "date" else self._excel_cell_display_value(cell_info)
            return self._format_daily_preview_date(raw_value)

        if field_type == "amount":
            raw_value = cell_info.get("value") if isinstance(cell_info, dict) and cell_info.get("kind") == "number" else self._excel_cell_display_value(cell_info)
            return self._format_daily_preview_amount(raw_value)

        return self._excel_cell_display_value(cell_info)

    def _build_preview_from_excel(self, section_key, file_content):
        try:
            rows = self._read_xlsx_rows(file_content)
        except ValueError:
            raise
        except (KeyError, ET.ParseError, zipfile.BadZipFile) as exc:
            raise ValueError("Không đọc được file Excel. Vui lòng dùng file .xlsx hoặc .xlsm hợp lệ.") from exc

        display_rows = [[self._excel_cell_display_value(cell) for cell in row] for row in rows]
        meaningful_row_indexes = [index for index, row in enumerate(display_rows) if any(cell for cell in row)]
        if not meaningful_row_indexes:
            raise ValueError("File Excel chưa có dữ liệu để preview.")

        header_row_index = meaningful_row_indexes[0]
        header_row = display_rows[header_row_index]
        data_rows = [rows[index] for index in meaningful_row_indexes[1:]]
        field_definitions = self._get_daily_section_definitions()[section_key]["fields"]

        header_lookup = {}
        for index, header_value in enumerate(header_row):
            normalized_key = self._normalize_header_key(header_value)
            if normalized_key and normalized_key not in header_lookup:
                header_lookup[normalized_key] = index

        mapped_fields = []
        missing_columns = []
        for field_definition in field_definitions:
            matched_index = None
            for alias in field_definition.get("aliases", []):
                alias_key = self._normalize_header_key(alias)
                if alias_key in header_lookup:
                    matched_index = header_lookup[alias_key]
                    break
            if matched_index is None and field_definition.get("required"):
                missing_columns.append(field_definition["label"])
            mapped_fields.append((field_definition, matched_index))

        if missing_columns:
            raise ValueError(f"Thiếu cột bắt buộc: {', '.join(missing_columns)}.")

        preview_columns = [
            {
                "label": field_definition["label"],
                "field": field_definition["field"],
                "header_class": field_definition.get("header_class"),
                "cell_class": field_definition.get("cell_class"),
            }
            for field_definition, _matched_index in mapped_fields
        ]

        preview_rows = []
        for row in data_rows:
            row_values = {}
            has_data = False
            for field_definition, matched_index in mapped_fields:
                value = ""
                if matched_index is not None and matched_index < len(row):
                    value = self._format_daily_preview_value(field_definition, row[matched_index])
                elif field_definition.get("fallback") == "sequence":
                    value = str(len(preview_rows) + 1)

                if value:
                    has_data = True
                row_values[field_definition["field"]] = value
            if not has_data:
                continue
            preview_rows.append(row_values)

        return preview_columns, preview_rows

    def _parse_daily_date(self, value):
        date_value = self._coerce_daily_date(value)
        return date_value or False

    def _coerce_daily_date(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, (int, float)):
            date_value = self._excel_serial_to_datetime(value)
            return date_value.date() if date_value else None

        raw_value = str(value).strip()
        if not raw_value:
            return None

        for date_format in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(raw_value, date_format).date()
            except Exception:
                continue
        try:
            return fields.Date.to_date(raw_value)
        except Exception:
            return None

    def _parse_daily_amount(self, value):
        amount_value = self._coerce_daily_amount(value)
        return amount_value if amount_value is not None else 0.0

    def _get_daily_model_name(self, section_key):
        model_names = {
            "doanh-thu": "tc.daily.revenue.line",
            "hieu-qua-kinh-doanh": "tc.daily.business.effectiveness.line",
        }
        return model_names.get(section_key)

    def _create_daily_records(self, section_key, file_entry, preview_rows):
        model_name = self._get_daily_model_name(section_key)
        if not model_name:
            return 0

        model = request.env[model_name]
        common_vals = {
            "upload_file_id": file_entry["id"],
            "upload_filename": file_entry["name"],
            "upload_version": int(file_entry["version"]),
            "approved_by_id": request.env.user.id,
            "approved_at": fields.Datetime.now(),
            "company_id": request.env.company.id,
            "currency_id": request.env.company.currency_id.id,
        }
        records_to_create = []
        for line_no, row in enumerate(preview_rows or [], 1):
            values = dict(common_vals)
            values.update(
                {
                    "line_no": line_no,
                    "date": self._parse_daily_date(row.get("date")),
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
                    "amount": self._parse_daily_amount(row.get("amount")),
                }
            )
            if section_key == "hieu-qua-kinh-doanh":
                values["offset_account"] = row.get("offset_account")
            records_to_create.append(values)

        if not records_to_create:
            return 0
        model.create(records_to_create)
        return len(records_to_create)

    def _build_daily_view_context(self, selected_section_key, filter_date):
        sections = self._build_daily_sections(filter_date=filter_date)
        current_section_key = selected_section_key if selected_section_key in sections else "doanh-thu"
        tabs = []
        daily_sections = []

        for key, section in sections.items():
            is_active = key == current_section_key
            tabs.append({"key": key, "label": section["label"], "active": is_active})
            daily_sections.append(
                {
                    "key": key,
                    "label": section["label"],
                    "short_label": section["short_label"],
                    "active": is_active,
                    "uploaded_files_title": section["uploaded_files_title"],
                    "uploaded_files": section["uploaded_files"],
                    "preview_title": section["preview_title"],
                    "preview_columns": section["preview_columns"],
                    "preview_rows": section["preview_rows"],
                    "preview_pagination": section["preview_pagination"],
                    "checking_count": section["checking_count"],
                    "hide_upload_zone": section["hide_upload_zone"],
                    "current_file_id": section["current_file_id"],
                }
            )

        return {
            "report_title": "BÁO CÁO TÀI CHÍNH - KẾ TOÁN",
            "daily_current_section_key": current_section_key,
            "tabs": tabs,
            "daily_sections": daily_sections,
            "notes": [
                {"label": "Preview đọc toàn bộ file Excel nhưng chỉ hiển thị các cột đã map", "link_text": "Cấu hình sẽ mở rộng sau"},
                {"label": "File upload vào trạng thái kiểm tra, bấm Gửi phê duyệt để tạo yêu cầu Approvals", "link_text": "Dữ liệu chỉ đẩy DB sau khi được duyệt"},
                {"label": "Dữ liệu dài sẽ được phân trang 100 dòng mỗi lần xem", "link_text": "Chuyển trang ngay trên preview"},
            ],
        }

    def _build_daily_action_response(self, section_key, filter_date, preview_file=None, page=1):
        response_payload = self._build_daily_shared_context(filter_date)
        response_payload.update(
            self._build_daily_section_response(
                section_key,
                preview_file=preview_file,
                page=page,
                filter_date=filter_date,
            )
        )
        return response_payload

    def _build_daily_filter_response(self, filter_date):
        response_payload = self._build_daily_shared_context(filter_date)
        response_payload["sections"] = {
            section_key: self._build_daily_section_response(section_key, filter_date=filter_date)
            for section_key in self._get_daily_section_definitions()
        }
        return response_payload

    def _create_daily_upload_attachment(self, upload_record, filename, file_content):
        mimetype, _encoding = mimetypes.guess_type(filename or "")
        attachment = request.env["ir.attachment"].sudo().create(
            {
                "name": filename,
                "datas": base64.b64encode(file_content),
                "res_model": "tc.daily.upload.file",
                "res_id": upload_record.id,
                "type": "binary",
                "mimetype": mimetype or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
        )
        upload_record.sudo().write(
            {
                "attachment_id": attachment.id,
                "mimetype": attachment.mimetype,
            }
        )

    def _attach_daily_upload_to_approval(self, approval_request, upload_record):
        if not upload_record.attachment_id:
            return
        upload_record.attachment_id.sudo().write(
            {
                "res_model": "approval.request",
                "res_id": approval_request.id,
            }
        )

    def _create_daily_approval_request(self, upload_record, section_definition):
        category = self._get_daily_approval_category()
        if not category:
            raise ValueError("Chưa cấu hình loại phê duyệt cho danh mục này.")
        approver_commands = []
        for approver in category.approver_ids:
            approver_commands.append(
                (
                    0,
                    0,
                    {
                        "user_id": approver.user_id.id,
                        "required": approver.required,
                        "sequence": approver.sequence,
                    },
                )
            )
        if not approver_commands:
            raise ValueError("Loại phê duyệt chưa có người duyệt mặc định.")

        approval_request = request.env["approval.request"].sudo().create(
            {
                "category_id": category.id,
                "request_owner_id": request.env.user.id,
                "name": f"{section_definition['short_label']} - {upload_record.name}",
                "reference": upload_record.name,
                "date": fields.Datetime.now(),
                "reason": (
                    f"<p><strong>Danh mục:</strong> {section_definition['label']}</p>"
                    f"<p><strong>Phiên bản:</strong> V{upload_record.version}</p>"
                    f"<p><strong>Dung lượng:</strong> {upload_record.file_size_display}</p>"
                    f"<p><strong>Số dòng preview:</strong> {upload_record.preview_row_count}</p>"
                ),
                "approver_ids": approver_commands,
            }
        )
        self._attach_daily_upload_to_approval(approval_request, upload_record)
        approval_request.sudo().action_confirm()
        upload_record.sudo().write(
            {
                "approval_request_id": approval_request.id,
                "status": "pending_approval",
                "status_message": False,
            }
        )
        return approval_request

    def _build_provisional_list_groups(self):
        return [
            {
                "name": "NHÓM 1: DOANH THU",
                "icon": "folder_open",
                "rows": [
                    {
                        "id": "PE-202603-001",
                        "debit": "111",
                        "credit": "511",
                        "amount": "10,000,000",
                        "description": "Doanh thu bán hàng A",
                        "version": "V1",
                        "due_date": "31/03/2026",
                        "action_label": "Chi tiết",
                    },
                    {
                        "id": "PE-202603-002",
                        "debit": "112",
                        "credit": "511",
                        "amount": "5,000,000",
                        "description": "Doanh thu bán hàng B",
                        "version": "V1",
                        "due_date": "31/03/2026",
                        "action_label": "Chi tiết",
                    },
                ],
            },
            {
                "name": "NHÓM 2: DÒNG TIỀN",
                "icon": "folder",
                "rows": [
                    {
                        "id": "PE-202603-003",
                        "debit": "111",
                        "credit": "511",
                        "amount": "2,000,000",
                        "description": "Tiền mặt",
                        "version": "V1",
                        "due_date": "31/03/2026",
                        "action_label": "Chi tiết",
                    },
                ],
            },
        ]

    def _build_provisional_view_context(self, provisional_tab):
        today = date.today()
        return {
            "provisional_tab": provisional_tab,
            "report_title": "BÁO CÁO TÀI CHÍNH - TẠM TÍNH",
            "report_subtitle": f"Bút toán tạm tính - Kế toán | Tháng {today.strftime('%m/%Y')}",
            "temporary_tabs": [
                {
                    "label": "Bảng danh sách",
                    "href": "/home/tam-tinh?tab=list",
                    "active": provisional_tab == "list",
                },
                {
                    "label": "Tải lên",
                    "href": "/home/tam-tinh?tab=upload",
                    "active": provisional_tab == "upload",
                },
            ],
            "temporary_search_placeholder": "Tìm kiếm...",
            "temporary_submit_label": "Gửi số liệu tạm tính",
            "temporary_groups": self._build_provisional_list_groups(),
            "temporary_total": "17,000,000",
            "temporary_total_records": "Hiển thị 3 trên 3 bản ghi",
            "temporary_upload_hint": [
                "Vui lòng sử dụng đúng biểu mẫu quy định của tập đoàn để tránh lỗi trong quá trình xử lý dữ liệu.",
                "Các trường có dấu (*) là bắt buộc.",
            ],
            "temporary_upload_links": [
                {"label": "Tải file biểu mẫu (.xlsx)", "icon": "download"},
                {"label": "Xem tài liệu hướng dẫn", "icon": "help"},
            ],
            "temporary_preview_columns": ["ID", "Ngày", "Sản phẩm", "Doanh thu", "Lợi nhuận"],
        }

    def _build_plan_rows(self):
        return [
            {
                "is_group": True,
                "label": "1. DOANH THU & THU NHẬP",
                "accounts": ["511", "515", "711"],
                "target": "25.400.000.000",
                "completed": "18.237.200.000",
                "progress": 71.8,
                "version": "V2.0",
                "updated_at": "01/03/2026",
                "action_label": "Chi tiết",
            },
            {
                "is_group": False,
                "label": "Doanh thu bán hàng",
                "accounts": ["5111"],
                "target": "22.000.000.000",
                "completed": "16.500.000.000",
                "progress": 75.0,
                "version": "V2.0",
                "updated_at": "01/03/2026",
                "action_label": "Cập nhật",
            },
            {
                "is_group": False,
                "label": "Doanh thu tài chính",
                "accounts": ["515"],
                "target": "3.400.000.000",
                "completed": "1.737.200.000",
                "progress": 51.1,
                "version": "V2.0",
                "updated_at": "01/03/2026",
                "action_label": "Cập nhật",
            },
            {
                "is_group": True,
                "label": "2. GIÁ VỐN HÀNG BÁN",
                "accounts": ["632"],
                "target": "15.200.000.000",
                "completed": "11.400.000.000",
                "progress": 75.0,
                "version": "V2.0",
                "updated_at": "01/03/2026",
                "action_label": "Chi tiết",
            },
            {
                "is_group": False,
                "label": "Giá vốn nguyên vật liệu",
                "accounts": ["6321"],
                "target": "9.800.000.000",
                "completed": "7.420.000.000",
                "progress": 75.7,
                "version": "V2.0",
                "updated_at": "01/03/2026",
                "action_label": "Cập nhật",
            },
            {
                "is_group": False,
                "label": "Giá vốn vận hành",
                "accounts": ["6328"],
                "target": "5.400.000.000",
                "completed": "3.980.000.000",
                "progress": 73.7,
                "version": "V2.0",
                "updated_at": "01/03/2026",
                "action_label": "Cập nhật",
            },
        ]

    def _build_plan_view_context(self):
        today = date.today()
        return {
            "report_title": "KẾ HOẠCH KINH DOANH",
            "report_version_text": f"PHIÊN BẢN HIỆU LỰC: V2 | THÁNG {today.strftime('%m/%Y')}",
            "sidebar_period_value": f"Tháng {today.strftime('%m/%Y')}",
            "plan_rows": self._build_plan_rows(),
        }

    @http.route("/", type="http", auth="public", website=True, sitemap=False)
    def thinh_cuong_root_redirect(self, **kwargs):
        if request.env.user._is_public():
            return request.redirect("/web/login?redirect=/home")
        return request.redirect("/home")

    @http.route("/home", type="http", auth="user")
    def thinh_cuong_home_report(self, **kwargs):
        filter_date = self._get_daily_filter_date(kwargs.get("filter_date"))
        context = self._build_base_context("daily", filter_date=filter_date)
        context.update(self._build_daily_view_context(kwargs.get("section"), filter_date))
        return request.render("tc_dataflow_report.thinh_cuong_home_report", context)

    @http.route("/home/daily/filter", type="http", auth="user", methods=["GET"], csrf=False)
    def thinh_cuong_daily_filter(self, **kwargs):
        filter_date = self._get_daily_filter_date(request.params.get("filter_date"))
        response_payload = {"success": True}
        response_payload.update(self._build_daily_filter_response(filter_date))
        return self._make_daily_json_response(response_payload)

    @http.route("/home/daily/preview", type="http", auth="user", methods=["GET"], csrf=False)
    def thinh_cuong_daily_preview(self, **kwargs):
        section_key = (request.params.get("section") or "").strip()
        filter_date = self._get_daily_filter_date(request.params.get("filter_date"))
        if section_key not in self._get_daily_section_definitions():
            return self._make_daily_json_response(
                {"success": False, "message": "Danh mục báo cáo không hợp lệ."},
                status=400,
            )

        file_id = (request.params.get("file_id") or "").strip()
        preview_file = self._get_daily_upload_record(section_key, file_id) if file_id else self._get_daily_upload_model()
        if file_id and not preview_file:
            return self._make_daily_json_response(
                {"success": False, "message": "Không tìm thấy file cần xem chi tiết."},
                status=404,
            )
        response_payload = {"success": True}
        response_payload.update(
            self._build_daily_action_response(
                section_key,
                filter_date=filter_date,
                preview_file=preview_file,
                page=request.params.get("page"),
            )
        )
        return self._make_daily_json_response(response_payload)

    @http.route("/home/daily/upload", type="http", auth="user", methods=["POST"], csrf=False)
    def thinh_cuong_daily_upload(self, **kwargs):
        section_key = (request.httprequest.form.get("section") or "").strip()
        filter_date = self._get_daily_filter_date(request.httprequest.form.get("filter_date"))
        file_storage = request.httprequest.files.get("file")
        section_definitions = self._get_daily_section_definitions()
        if section_key not in section_definitions:
            return self._make_daily_json_response(
                {"success": False, "message": "Danh mục báo cáo không hợp lệ."},
                status=400,
            )

        active_record = self._get_daily_active_record(
            self._get_daily_upload_records(section_key, limit=None, filter_date=filter_date)
        )
        if active_record:
            response_payload = {
                "success": False,
                "message": "Danh mục này đã có file đang xử lý. Chỉ khi file bị từ chối mới được tải file khác.",
            }
            response_payload.update(self._build_daily_action_response(section_key, filter_date, preview_file=active_record))
            return self._make_daily_json_response(response_payload, status=400)

        if not file_storage or not file_storage.filename:
            response_payload = {
                "success": False,
                "message": "Bạn chưa chọn file Excel.",
            }
            response_payload.update(self._build_daily_action_response(section_key, filter_date))
            return self._make_daily_json_response(
                response_payload,
                status=400,
            )

        filename = (file_storage.filename or "").split("\\")[-1].split("/")[-1]
        upload_model = self._get_daily_upload_model()
        next_version = upload_model.search_count(
            [
                ("section_key", "=", section_key),
                ("company_id", "=", request.env.company.id),
            ]
        ) + 1
        upload_record = upload_model

        try:
            if not filename.lower().endswith((".xlsx", ".xlsm")):
                raise ValueError("Hiện tại chỉ hỗ trợ file Excel dạng .xlsx hoặc .xlsm.")

            file_content = file_storage.read()
            if not file_content:
                raise ValueError("File Excel đang rỗng.")
            if len(file_content) > 10 * 1024 * 1024:
                raise ValueError("File vượt quá dung lượng 10MB.")

            preview_columns, preview_rows = self._build_preview_from_excel(section_key, file_content)
            upload_record = upload_model.create(
                {
                    "name": filename,
                    "section_key": section_key,
                    "status": "checking",
                    "version": next_version,
                    "upload_user_id": request.env.user.id,
                    "file_size": len(file_content),
                    "preview_columns": preview_columns,
                    "preview_rows": preview_rows,
                    "company_id": request.env.company.id,
                }
            )
            self._create_daily_upload_attachment(upload_record, filename, file_content)
            response_payload = {
                "success": True,
                "message": f"Đã tải lên file {filename}. File đang ở trạng thái kiểm tra, bấm Gửi phê duyệt để chuyển sang Approvals.",
            }
            response_payload.update(self._build_daily_action_response(section_key, filter_date, preview_file=upload_record))
            return self._make_daily_json_response(response_payload)
        except ValueError as exc:
            error_message = str(exc)
        except Exception:
            error_message = "Hệ thống không thể xử lý file này."

        if upload_record:
            upload_record.sudo().write(
                {
                    "status": "error",
                    "status_message": error_message,
                    "file_size": len(file_content) if "file_content" in locals() and file_content else upload_record.file_size,
                }
            )
        else:
            upload_record = upload_model.create(
                {
                    "name": filename,
                    "section_key": section_key,
                    "status": "error",
                    "version": next_version,
                    "upload_user_id": request.env.user.id,
                    "file_size": len(file_content) if "file_content" in locals() and file_content else 0,
                    "status_message": error_message,
                    "company_id": request.env.company.id,
                }
            )
        response_payload = {
            "success": False,
            "message": error_message,
        }
        response_payload.update(self._build_daily_action_response(section_key, filter_date, preview_file=upload_record))
        return self._make_daily_json_response(
            response_payload,
            status=400,
        )

    @http.route("/home/daily/submit", type="http", auth="user", methods=["POST"], csrf=False)
    def thinh_cuong_daily_submit(self, **kwargs):
        section_key = (request.httprequest.form.get("section") or "").strip()
        file_id = (request.httprequest.form.get("file_id") or "").strip()
        filter_date = self._get_daily_filter_date(request.httprequest.form.get("filter_date"))
        section_definitions = self._get_daily_section_definitions()
        if section_key not in section_definitions:
            return self._make_daily_json_response(
                {"success": False, "message": "Danh mục báo cáo không hợp lệ."},
                status=400,
            )

        upload_records = self._get_daily_upload_records(section_key, limit=None, filter_date=filter_date)
        active_record = self._get_daily_active_record(upload_records)
        approved_record = self._get_daily_approved_record(upload_records)
        if approved_record:
            response_payload = {
                "success": False,
                "message": "Danh mục này đã có file được duyệt. Không thể gửi phê duyệt thêm.",
            }
            response_payload.update(self._build_daily_action_response(section_key, filter_date, preview_file=approved_record))
            return self._make_daily_json_response(response_payload, status=400)

        if file_id:
            selected_record = self._get_daily_upload_record(section_key, file_id)
            if not selected_record:
                return self._make_daily_json_response(
                    {"success": False, "message": "Không tìm thấy file cần gửi phê duyệt."},
                    status=404,
                )
            if selected_record.status != "checking":
                response_payload = {
                    "success": False,
                    "message": "Chỉ file ở trạng thái kiểm tra mới được gửi phê duyệt.",
                }
                response_payload.update(self._build_daily_action_response(section_key, filter_date, preview_file=selected_record))
                return self._make_daily_json_response(response_payload, status=400)
            checking_records = selected_record
        else:
            checking_records = upload_records.filtered(lambda record: record.status == "checking")

        if not checking_records:
            response_payload = {
                "success": False,
                "message": "Không có file nào đang ở trạng thái kiểm tra để gửi phê duyệt trong ngày đã chọn.",
            }
            response_payload.update(self._build_daily_action_response(section_key, filter_date))
            return self._make_daily_json_response(response_payload, status=400)

        submitted_count = 0
        failed_files = []
        configuration_error = None
        for upload_record in checking_records:
            try:
                self._create_daily_approval_request(upload_record, section_definitions[section_key])
                submitted_count += 1
            except ValueError as exc:
                configuration_error = str(exc)
                break
            except Exception:
                failed_files.append(upload_record.name)

        if configuration_error:
            response_payload = {
                "success": False,
                "message": configuration_error,
            }
            response_payload.update(self._build_daily_action_response(section_key, filter_date))
            return self._make_daily_json_response(response_payload, status=400)

        if not submitted_count:
            response_payload = {
                "success": False,
                "message": "Hệ thống chưa thể tạo yêu cầu phê duyệt cho các file đang kiểm tra.",
            }
            response_payload.update(self._build_daily_action_response(section_key, filter_date))
            return self._make_daily_json_response(response_payload, status=400)

        message = f"Đã gửi {submitted_count} file sang Approvals từ tab {section_definitions[section_key]['short_label']}."
        if failed_files:
            message = f"{message} Không gửi được {len(failed_files)} file: {', '.join(failed_files)}."
        response_payload = {
            "success": True,
            "message": message,
        }
        response_payload.update(
            self._build_daily_action_response(
                section_key,
                filter_date,
                preview_file=checking_records[:1] if checking_records else active_record,
            )
        )
        return self._make_daily_json_response(response_payload)

    @http.route("/home/daily/approve", type="http", auth="user", methods=["POST"], csrf=False)
    def thinh_cuong_daily_approve(self, **kwargs):
        section_key = (request.httprequest.form.get("section") or "").strip()
        file_id = (request.httprequest.form.get("file_id") or "").strip()
        filter_date = self._get_daily_filter_date(request.httprequest.form.get("filter_date"))
        if section_key not in self._get_daily_section_definitions() or not file_id:
            return self._make_daily_json_response(
                {"success": False, "message": "Thông tin phê duyệt không hợp lệ."},
                status=400,
            )

        upload_record = self._get_daily_upload_record(section_key, file_id)
        if not upload_record:
            return self._make_daily_json_response(
                {"success": False, "message": "Không tìm thấy file cần phê duyệt."},
                status=404,
            )

        if upload_record.status == "error":
            response_payload = {
                "success": False,
                "message": "File lỗi dữ liệu nên không thể phê duyệt.",
            }
            response_payload.update(self._build_daily_action_response(section_key, filter_date, preview_file=upload_record))
            return self._make_daily_json_response(
                response_payload,
                status=400,
            )

        if upload_record.status != "pending_approval" or not upload_record.approval_request_id:
            response_payload = {
                "success": False,
                "message": "File này chưa được gửi phê duyệt.",
            }
            response_payload.update(self._build_daily_action_response(section_key, filter_date, preview_file=upload_record))
            return self._make_daily_json_response(
                response_payload,
                status=400,
            )

        approval_request = upload_record.approval_request_id.sudo()
        approver = approval_request.approver_ids.filtered(
            lambda item: item.user_id.id == request.env.user.id and item.status == "pending"
        )[:1]
        is_manager = request.env.user.has_group("approvals.group_approval_manager")
        if not approver and not is_manager:
            response_payload = {
                "success": False,
                "message": "Bạn không có quyền phê duyệt file này.",
            }
            response_payload.update(self._build_daily_action_response(section_key, filter_date, preview_file=upload_record))
            return self._make_daily_json_response(
                response_payload,
                status=403,
            )

        if approver:
            approver.sudo().action_approve()
        else:
            approval_request._action_force_approval()
        upload_record.sudo()._sync_with_approval_request()
        upload_record = self._get_daily_upload_record(section_key, file_id)
        response_payload = {
            "success": True,
            "message": (
                f"Đã phê duyệt file {upload_record.name} và ghi {upload_record.imported_row_count} dòng dữ liệu."
                if upload_record.status == "approved"
                else f"Đã ghi nhận phê duyệt file {upload_record.name}. Yêu cầu vẫn chờ các bước duyệt còn lại."
            ),
        }
        response_payload.update(self._build_daily_action_response(section_key, filter_date, preview_file=upload_record))
        return self._make_daily_json_response(response_payload)

    @http.route("/home/daily/reject", type="http", auth="user", methods=["POST"], csrf=False)
    def thinh_cuong_daily_reject(self, **kwargs):
        section_key = (request.httprequest.form.get("section") or "").strip()
        file_id = (request.httprequest.form.get("file_id") or "").strip()
        filter_date = self._get_daily_filter_date(request.httprequest.form.get("filter_date"))
        if section_key not in self._get_daily_section_definitions() or not file_id:
            return self._make_daily_json_response(
                {"success": False, "message": "Thông tin từ chối không hợp lệ."},
                status=400,
            )

        upload_record = self._get_daily_upload_record(section_key, file_id)
        if not upload_record:
            return self._make_daily_json_response(
                {"success": False, "message": "Không tìm thấy file cần từ chối."},
                status=404,
            )

        if upload_record.status != "pending_approval" or not upload_record.approval_request_id:
            response_payload = {
                "success": False,
                "message": "File này chưa được gửi phê duyệt.",
            }
            response_payload.update(self._build_daily_action_response(section_key, filter_date, preview_file=upload_record))
            return self._make_daily_json_response(
                response_payload,
                status=400,
            )

        approval_request = upload_record.approval_request_id.sudo()
        approver = approval_request.approver_ids.filtered(
            lambda item: item.user_id.id == request.env.user.id and item.status == "pending"
        )[:1]
        is_manager = request.env.user.has_group("approvals.group_approval_manager")
        if not approver and not is_manager:
            response_payload = {
                "success": False,
                "message": "Bạn không có quyền từ chối file này.",
            }
            response_payload.update(self._build_daily_action_response(section_key, filter_date, preview_file=upload_record))
            return self._make_daily_json_response(
                response_payload,
                status=403,
            )

        if approver:
            approver.sudo().action_refuse()
        else:
            upload_record.sudo().force_refuse()
        upload_record.sudo()._sync_with_approval_request()
        upload_record = self._get_daily_upload_record(section_key, file_id)
        response_payload = {
            "success": True,
            "message": f"Đã từ chối file {upload_record.name}. Dữ liệu không được đẩy vào database.",
        }
        response_payload.update(self._build_daily_action_response(section_key, filter_date, preview_file=upload_record))
        return self._make_daily_json_response(response_payload)

    @http.route("/home/tam-tinh", type="http", auth="user")
    def thinh_cuong_temporary_report(self, **kwargs):
        provisional_tab = "upload" if kwargs.get("tab") == "upload" else "list"
        context = self._build_base_context("temporary")
        context.update(self._build_provisional_view_context(provisional_tab))
        return request.render("tc_dataflow_report.thinh_cuong_temporary_report", context)

    @http.route("/home/ke-hoach", type="http", auth="user")
    def thinh_cuong_plan_report(self, **kwargs):
        context = self._build_base_context("plan")
        context.update(self._build_plan_view_context())
        return request.render("tc_dataflow_report.thinh_cuong_plan_report", context)

from datetime import date, timedelta

from odoo import http
from odoo.http import request


class TcDataflowReportController(http.Controller):

    def _get_user_initials(self, user_name):
        parts = [part[0].upper() for part in (user_name or "").split() if part]
        if not parts:
            return "TC"
        return "".join(parts[:2])

    def _build_recent_days(self, today):
        return [
            {
                "date": today.strftime("%d/%m/%Y"),
                "status": "CHƯA LÀM",
                "status_class": "is-pending",
                "note": "Kế hoạch định kỳ",
            },
            {
                "date": (today - timedelta(days=1)).strftime("%d/%m/%Y"),
                "status": "ĐÃ LÀM",
                "status_class": "is-done",
                "note": "Báo cáo dòng tiền",
            },
            {
                "date": (today - timedelta(days=2)).strftime("%d/%m/%Y"),
                "status": "CHƯA LÀM",
                "status_class": "is-pending",
                "note": "Chi phí vận hành",
            },
            {
                "date": (today - timedelta(days=3)).strftime("%d/%m/%Y"),
                "status": "ĐÃ DUYỆT",
                "status_class": "is-approved",
                "note": "Kế hoạch nhân sự",
            },
            {
                "date": (today - timedelta(days=4)).strftime("%d/%m/%Y"),
                "status": "ĐÃ DUYỆT",
                "status_class": "is-approved",
                "note": "Dự toán dự án",
            },
        ]

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
                "active": False,
                "href": "#",
            },
            {
                "label": "Tổng hợp",
                "icon": "settings",
                "active": False,
                "href": "#",
            },
        ]

    def _build_base_context(self, current_view):
        today = date.today()
        user = request.env.user

        titles = {
            "daily": "Báo cáo tài chính - Kế toán",
            "temporary": "Báo cáo tài chính - Tạm tính",
        }

        return {
            "page_title": titles[current_view],
            "brand_name": "THỊNH CƯỜNG",
            "current_view": current_view,
            "user_name": user.name,
            "user_role": "QUẢN TRỊ VIÊN HỆ THỐNG",
            "user_initials": self._get_user_initials(user.name),
            "selected_date_display": today.strftime("%d/%m/%Y"),
            "selected_date_input": today.isoformat(),
            "nav_items": self._build_nav_items(current_view),
            "org_filters": [
                {"label": "Toàn công ty", "checked": True},
                {"label": "Cost Center 1", "checked": False},
                {"label": "Cost Center 2", "checked": False},
                {"label": "Chi nhánh HN", "checked": False},
            ],
            "recent_days": self._build_recent_days(today),
        }

    def _build_daily_view_context(self):
        return {
            "report_title": "BÁO CÁO TÀI CHÍNH - KẾ TOÁN",
            "tabs": [
                {"label": "1. DOANH THU", "active": True},
                {"label": "2. DÒNG TIỀN", "active": False},
                {"label": "3. PHẢI THU", "active": False},
                {"label": "4. PHẢI TRẢ", "active": False},
                {"label": "5. HIỆU QUẢ KINH DOANH", "active": False},
                {"label": "6. TÀI SẢN", "active": False},
            ],
            "uploaded_files": [
                {
                    "name": "DT_2203.xlsx",
                    "version": "1",
                    "status": "Sai mẫu",
                    "status_icon": "warning",
                    "status_class": "is-error",
                    "action_label": "Xem chi tiết",
                },
                {
                    "name": "DT_2204.xlsx",
                    "version": "1",
                    "status": "Đã duyệt",
                    "status_icon": "check_circle",
                    "status_class": "is-approved",
                    "action_label": "Xem chi tiết",
                },
            ],
            "preview_rows": [
                {
                    "id": "01",
                    "date": "10/06/2023",
                    "product": "Product 1",
                    "region": "North",
                    "sales": "267,000",
                    "profit": "33,500",
                },
                {
                    "id": "02",
                    "date": "10/07/2023",
                    "product": "Product 2",
                    "region": "Spain",
                    "sales": "105,000",
                    "profit": "11,000",
                },
                {
                    "id": "03",
                    "date": "10/07/2023",
                    "product": "Product 3",
                    "region": "Spain",
                    "sales": "65,000",
                    "profit": "26,200",
                },
                {
                    "id": "04",
                    "date": "10/09/2023",
                    "product": "Product 4",
                    "region": "North",
                    "sales": "31,500",
                    "profit": "12,300",
                },
            ],
            "notes": [
                {"label": "File biểu mẫu Link tải", "link_text": "ở đây"},
                {
                    "label": "Các lưu ý về đầu tài khoản cần lấy:",
                    "link_text": "Xem hướng dẫn ở đây",
                },
            ],
        }

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
            "temporary_preview_columns": [
                "ID",
                "Ngày",
                "Sản phẩm",
                "Doanh thu",
                "Lợi nhuận",
            ],
        }

    @http.route("/", type="http", auth="public", website=True, sitemap=False)
    def thinh_cuong_root_redirect(self, **kwargs):
        if request.env.user._is_public():
            return request.redirect("/web/login?redirect=/home")
        return request.redirect("/home")

    @http.route("/home", type="http", auth="user")
    def thinh_cuong_home_report(self, **kwargs):
        context = self._build_base_context("daily")
        context.update(self._build_daily_view_context())
        return request.render("tc_dataflow_report.thinh_cuong_home_report", context)

    @http.route("/home/tam-tinh", type="http", auth="user")
    def thinh_cuong_temporary_report(self, **kwargs):
        provisional_tab = "upload" if kwargs.get("tab") == "upload" else "list"

        context = self._build_base_context("temporary")
        context.update(self._build_provisional_view_context(provisional_tab))
        return request.render("tc_dataflow_report.thinh_cuong_temporary_report", context)

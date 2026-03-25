from datetime import date, timedelta

from odoo import http
from odoo.http import request


class TcDataflowReportController(http.Controller):

    def _get_user_initials(self, user_name):
        parts = [part[0].upper() for part in (user_name or "").split() if part]
        if not parts:
            return "TC"
        return "".join(parts[:2])

    def _build_import_data_context(self):
        today = date.today()
        user = request.env.user

        recent_days = [
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

        return {
            "page_title": "Báo cáo tài chính - kế toán",
            "brand_name": "THỊNH CƯỜNG",
            "report_title": "BÁO CÁO TÀI CHÍNH - KẾ TOÁN",
            "user_name": user.name,
            "user_role": "KẾ TOÁN CHUYÊN QUẢN THỊNH CƯỜNG",
            "user_initials": self._get_user_initials(user.name),
            "selected_date_display": today.strftime("%d/%m/%Y"),
            "selected_date_input": today.isoformat(),
            "nav_items": [
                {"label": "Báo cáo ngày", "icon": "edit_note", "active": True},
                {"label": "Tạm tính", "icon": "assessment", "active": False},
                {"label": "Kế hoạch", "icon": "dashboard", "active": False},
                {"label": "Tổng hợp", "icon": "settings", "active": False},
            ],
            "org_filters": [
                {"label": "Toàn công ty", "checked": True},
                {"label": "Cost Center 1", "checked": False},
                {"label": "Cost Center 2", "checked": False},
                {"label": "Chi nhánh HN", "checked": False},
            ],
            "recent_days": recent_days,
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
                {"id": "01", "date": "10/06/2023", "product": "Product 1", "region": "North", "sales": "267,000", "profit": "33,500"},
                {"id": "02", "date": "10/07/2023", "product": "Product 2", "region": "Spain", "sales": "105,000", "profit": "11,000"},
                {"id": "03", "date": "10/07/2023", "product": "Product 3", "region": "Spain", "sales": "65,000", "profit": "26,200"},
                {"id": "04", "date": "10/09/2023", "product": "Product 4", "region": "North", "sales": "31,500", "profit": "12,300"},
            ],
            "notes": [
                {"label": "File biểu mẫu Link tải", "link_text": "ở đây"},
                {"label": "Các lưu ý về đầu tài khoản cần lấy:", "link_text": "Xem hướng dẫn ở đây"},
            ],
        }

    @http.route("/thinhcuong/home/report", type="http", auth="user")
    def thinh_cuong_home_report(self, **kwargs):
        return request.render(
            "tc_dataflow_report.thinh_cuong_home_report",
            self._build_import_data_context(),
        )

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
                "status": "ĐÃ DUYỆT",
                "status_class": "is-approved",
                "note": "Chi phí vận hành",
            },
            {
                "date": (today - timedelta(days=3)).strftime("%d/%m/%Y"),
                "status": "ĐÃ LÀM",
                "status_class": "is-done",
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

    def _build_base_context(self, current_view):
        today = date.today()
        user = request.env.user
        titles = {
            "daily": "Báo cáo tài chính - Kế toán",
            "temporary": "Báo cáo tài chính - Tạm tính",
            "plan": "Kế hoạch kinh doanh",
        }

        return {
            "page_title": titles[current_view],
            "brand_name": "THỊNH CƯỜNG",
            "current_view": current_view,
            "user_name": user.name,
            "user_role": "FINANCIAL DIRECTOR",
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
            "sidebar_period_value": None,
        }

    def _build_daily_sections(self):
        return {
            "doanh-thu": {
                "label": "1. DOANH THU",
                "short_label": "Doanh thu",
                "uploaded_files_title": "Uploaded Files List - Doanh thu",
                "preview_title": "Data Preview - Doanh thu",
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
                        "version": "2",
                        "status": "Đã duyệt",
                        "status_icon": "check_circle",
                        "status_class": "is-approved",
                        "action_label": "Xem chi tiết",
                    },
                ],
                "preview_columns": [
                    {"label": "ID", "field": "id", "cell_class": "is-strong"},
                    {"label": "Date", "field": "date"},
                    {"label": "Product", "field": "product"},
                    {"label": "Region", "field": "region"},
                    {"label": "Sales", "field": "sales", "header_class": "is-right", "cell_class": "is-right is-strong"},
                    {"label": "Profit", "field": "profit", "header_class": "is-right", "cell_class": "is-right is-profit"},
                ],
                "preview_rows": [
                    {"id": "DT-01", "date": "10/06/2023", "product": "Product 1", "region": "North", "sales": "267,000", "profit": "33,500"},
                    {"id": "DT-02", "date": "10/07/2023", "product": "Product 2", "region": "Spain", "sales": "105,000", "profit": "11,000"},
                    {"id": "DT-03", "date": "10/07/2023", "product": "Product 3", "region": "Spain", "sales": "65,000", "profit": "26,200"},
                    {"id": "DT-04", "date": "10/09/2023", "product": "Product 4", "region": "North", "sales": "31,500", "profit": "12,300"},
                ],
            },
            "dong-tien": {
                "label": "2. DÒNG TIỀN",
                "short_label": "Dòng tiền",
                "uploaded_files_title": "Uploaded Files List - Dòng tiền",
                "preview_title": "Data Preview - Dòng tiền",
                "uploaded_files": [
                    {
                        "name": "CF_0326_v1.xlsx",
                        "version": "1",
                        "status": "Chờ kiểm tra",
                        "status_icon": "schedule",
                        "status_class": "is-pending",
                        "action_label": "Kiểm tra",
                    },
                    {
                        "name": "CF_0326_v2.xlsx",
                        "version": "2",
                        "status": "Đã duyệt",
                        "status_icon": "check_circle",
                        "status_class": "is-approved",
                        "action_label": "Xem chi tiết",
                    },
                ],
                "preview_columns": [
                    {"label": "ID", "field": "id", "cell_class": "is-strong"},
                    {"label": "Date", "field": "date"},
                    {"label": "Cash Source", "field": "cash_source"},
                    {"label": "Account", "field": "account"},
                    {"label": "Inflow", "field": "inflow", "header_class": "is-right", "cell_class": "is-right is-strong"},
                    {"label": "Outflow", "field": "outflow", "header_class": "is-right", "cell_class": "is-right"},
                ],
                "preview_rows": [
                    {"id": "CF-01", "date": "25/03/2026", "cash_source": "Thu bán hàng", "account": "111", "inflow": "890,000", "outflow": "0"},
                    {"id": "CF-02", "date": "25/03/2026", "cash_source": "Thanh toán NCC", "account": "112", "inflow": "0", "outflow": "310,000"},
                    {"id": "CF-03", "date": "26/03/2026", "cash_source": "Chi phí vận hành", "account": "112", "inflow": "0", "outflow": "120,000"},
                ],
            },
            "phai-thu": {
                "label": "3. PHẢI THU",
                "short_label": "Phải thu",
                "uploaded_files_title": "Uploaded Files List - Phải thu",
                "preview_title": "Data Preview - Phải thu",
                "uploaded_files": [
                    {
                        "name": "AR_customer_march.xlsx",
                        "version": "3",
                        "status": "Đã duyệt",
                        "status_icon": "check_circle",
                        "status_class": "is-approved",
                        "action_label": "Xem chi tiết",
                    },
                    {
                        "name": "AR_adjustment.xlsx",
                        "version": "1",
                        "status": "Sai mẫu",
                        "status_icon": "warning",
                        "status_class": "is-error",
                        "action_label": "Xem lỗi",
                    },
                ],
                "preview_columns": [
                    {"label": "ID", "field": "id", "cell_class": "is-strong"},
                    {"label": "Customer", "field": "customer"},
                    {"label": "Invoice", "field": "invoice"},
                    {"label": "Due Date", "field": "due_date"},
                    {"label": "Outstanding", "field": "outstanding", "header_class": "is-right", "cell_class": "is-right is-strong"},
                    {"label": "Status", "field": "status"},
                ],
                "preview_rows": [
                    {"id": "AR-01", "customer": "Công ty A", "invoice": "INV-2301", "due_date": "30/03/2026", "outstanding": "450,000", "status": "Quá hạn 3 ngày"},
                    {"id": "AR-02", "customer": "Công ty B", "invoice": "INV-2305", "due_date": "02/04/2026", "outstanding": "820,000", "status": "Đến hạn"},
                    {"id": "AR-03", "customer": "Công ty C", "invoice": "INV-2308", "due_date": "15/04/2026", "outstanding": "265,000", "status": "Trong hạn"},
                ],
            },
            "phai-tra": {
                "label": "4. PHẢI TRẢ",
                "short_label": "Phải trả",
                "uploaded_files_title": "Uploaded Files List - Phải trả",
                "preview_title": "Data Preview - Phải trả",
                "uploaded_files": [
                    {
                        "name": "AP_vendor_master.xlsx",
                        "version": "2",
                        "status": "Đã duyệt",
                        "status_icon": "check_circle",
                        "status_class": "is-approved",
                        "action_label": "Xem chi tiết",
                    },
                    {
                        "name": "AP_due_list.xlsx",
                        "version": "1",
                        "status": "Chờ kiểm tra",
                        "status_icon": "schedule",
                        "status_class": "is-pending",
                        "action_label": "Kiểm tra",
                    },
                ],
                "preview_columns": [
                    {"label": "ID", "field": "id", "cell_class": "is-strong"},
                    {"label": "Vendor", "field": "vendor"},
                    {"label": "Bill", "field": "bill"},
                    {"label": "Due Date", "field": "due_date"},
                    {"label": "Payable", "field": "payable", "header_class": "is-right", "cell_class": "is-right is-strong"},
                    {"label": "Status", "field": "status"},
                ],
                "preview_rows": [
                    {"id": "AP-01", "vendor": "Nhà cung cấp A", "bill": "BILL-101", "due_date": "28/03/2026", "payable": "380,000", "status": "Đang chờ thanh toán"},
                    {"id": "AP-02", "vendor": "Nhà cung cấp B", "bill": "BILL-102", "due_date": "01/04/2026", "payable": "1,120,000", "status": "Đến hạn"},
                    {"id": "AP-03", "vendor": "Nhà cung cấp C", "bill": "BILL-103", "due_date": "09/04/2026", "payable": "240,000", "status": "Trong hạn"},
                ],
            },
            "hieu-qua-kinh-doanh": {
                "label": "5. HIỆU QUẢ KINH DOANH",
                "short_label": "Hiệu quả kinh doanh",
                "uploaded_files_title": "Uploaded Files List - Hiệu quả kinh doanh",
                "preview_title": "Data Preview - Hiệu quả kinh doanh",
                "uploaded_files": [
                    {
                        "name": "PBI_margin_report.xlsx",
                        "version": "4",
                        "status": "Đã duyệt",
                        "status_icon": "check_circle",
                        "status_class": "is-approved",
                        "action_label": "Xem chi tiết",
                    },
                    {
                        "name": "ROI_segment.xlsx",
                        "version": "1",
                        "status": "Sai mẫu",
                        "status_icon": "warning",
                        "status_class": "is-error",
                        "action_label": "Xem lỗi",
                    },
                ],
                "preview_columns": [
                    {"label": "ID", "field": "id", "cell_class": "is-strong"},
                    {"label": "Segment", "field": "segment"},
                    {"label": "Revenue", "field": "revenue", "header_class": "is-right", "cell_class": "is-right is-strong"},
                    {"label": "Cost", "field": "cost", "header_class": "is-right", "cell_class": "is-right"},
                    {"label": "Margin", "field": "margin", "header_class": "is-right", "cell_class": "is-right is-profit"},
                    {"label": "ROI", "field": "roi", "header_class": "is-right", "cell_class": "is-right"},
                ],
                "preview_rows": [
                    {"id": "BE-01", "segment": "North Retail", "revenue": "2,650,000", "cost": "1,940,000", "margin": "710,000", "roi": "36.6%"},
                    {"id": "BE-02", "segment": "South Wholesale", "revenue": "1,980,000", "cost": "1,455,000", "margin": "525,000", "roi": "36.1%"},
                    {"id": "BE-03", "segment": "Export", "revenue": "3,240,000", "cost": "2,610,000", "margin": "630,000", "roi": "24.1%"},
                ],
            },
            "tai-san": {
                "label": "6. TÀI SẢN",
                "short_label": "Tài sản",
                "uploaded_files_title": "Uploaded Files List - Tài sản",
                "preview_title": "Data Preview - Tài sản",
                "uploaded_files": [
                    {
                        "name": "FA_register_march.xlsx",
                        "version": "2",
                        "status": "Đã duyệt",
                        "status_icon": "check_circle",
                        "status_class": "is-approved",
                        "action_label": "Xem chi tiết",
                    },
                    {
                        "name": "Asset_movement.xlsx",
                        "version": "1",
                        "status": "Chờ kiểm tra",
                        "status_icon": "schedule",
                        "status_class": "is-pending",
                        "action_label": "Kiểm tra",
                    },
                ],
                "preview_columns": [
                    {"label": "ID", "field": "id", "cell_class": "is-strong"},
                    {"label": "Asset Code", "field": "asset_code"},
                    {"label": "Asset Name", "field": "asset_name"},
                    {"label": "Department", "field": "department"},
                    {"label": "Net Value", "field": "net_value", "header_class": "is-right", "cell_class": "is-right is-strong"},
                    {"label": "Status", "field": "status"},
                ],
                "preview_rows": [
                    {"id": "FA-01", "asset_code": "TS-001", "asset_name": "Xe tải 2T", "department": "Logistics", "net_value": "1,250,000", "status": "Đang sử dụng"},
                    {"id": "FA-02", "asset_code": "TS-017", "asset_name": "Máy đóng gói", "department": "Factory", "net_value": "845,000", "status": "Bảo trì định kỳ"},
                    {"id": "FA-03", "asset_code": "TS-021", "asset_name": "Hệ thống lạnh", "department": "Warehouse", "net_value": "1,720,000", "status": "Đang sử dụng"},
                ],
            },
        }

    def _build_daily_view_context(self, selected_section_key):
        sections = self._build_daily_sections()
        current_section_key = selected_section_key if selected_section_key in sections else "doanh-thu"
        tabs = []
        daily_sections = []
        for key, section in sections.items():
            is_active = key == current_section_key
            tabs.append(
                {
                    "key": key,
                    "label": section["label"],
                    "active": is_active,
                }
            )
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
                }
            )

        return {
            "report_title": "BÁO CÁO TÀI CHÍNH - KẾ TOÁN",
            "daily_current_section_key": current_section_key,
            "tabs": tabs,
            "daily_sections": daily_sections,
            "notes": [
                {"label": "File biểu mẫu Link tải", "link_text": "ở đây"},
                {"label": "Các lưu ý về đầu tài khoản cần lấy:", "link_text": "Xem hướng dẫn ở đây"},
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
        context = self._build_base_context("daily")
        context.update(self._build_daily_view_context(kwargs.get("section")))
        return request.render("tc_dataflow_report.thinh_cuong_home_report", context)

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

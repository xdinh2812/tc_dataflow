{
    'name': 'Tc Dataflow Report',
    'summary': "Thịnh Cường Dataflow",
    'version': '1.0',
    'depends': ['base', 'web', 'website', 'account', 'analytic', 'approvals'],
    'data': [
        "security/ir.model.access.csv",
        "data/tc_daily_approval_categories.xml",
        'views/account_dimension_views.xml',
        'views/business_segment_views.xml',
        'views/account_business_performance_views.xml',
        'views/login_templates.xml',
        'views/thinh_cuong_home_templates.xml',
        'views/thinh_cuong_temporary_templates.xml',
        'views/thinh_cuong_plan_templates.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'tc_dataflow_report/static/src/css/import_data.css',
            'tc_dataflow_report/static/src/css/login.css',
        ],
        'website.assets_frontend': [
            'tc_dataflow_report/static/src/css/import_data.css',
        ],
    },
    'installable': True,
}

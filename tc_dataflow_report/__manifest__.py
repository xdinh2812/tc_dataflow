{
    'name': 'Tc Dataflow Report',
    'summary': "Thịnh Cường Dataflow",
    'version': '1.0',
    'depends': ['base', 'website', 'account'],
    'data': [
        "security/ir.model.access.csv",
        'views/account_dimension_views.xml',
        'views/business_segment_views.xml',
        'views/import_data_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'tc_dataflow_report/static/src/css/import_data.css',
        ],
    },
    'installable': True,
}
{
    'name': 'Tc Dataflow Report',
    'summary': "Thịnh Cường Dataflow",
    'version': '1.0',
    'depends': ['base', 'website'],
    'data': [
        'views/import_data_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'tc_dataflow_report/static/src/css/import_data.css',
        ],
    },
    'installable': True,
}
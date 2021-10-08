{
    'name': 'jibarito venta de lotes',
    'summary': 'jibarito venta de lotes',
    'version': '13.0.1',
    'category': 'Sales',
    'description': """
        Ocultar campos inesesarios y calculos de moratorios
    """,
    'author': "Ogum",
    'depends': ['web'],
    'data': [
        'views/sales.xml',
        'views/client.xml',
        'views/warehouse.xml',
    #    'security/view_dynamic_security.xml',
    #    'security/ir.model.access.csv',
    ],
    #'qweb': [
    #    'static/src/xml/form_edit.xml',
    #    'static/src/xml/base.xml',
    #    'static/src/xml/form_fields.xml',
    #    'static/src/xml/kanban_template.xml',
    #],
    'installable': True,
    'auto_install': False,
    'application': False,
    
}

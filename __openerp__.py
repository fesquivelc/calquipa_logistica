{
    'name': "CALIDRA Logística",

    'summary': u"""
        Datos de logística como las rutas, tarifa de transporte, tipo de transporte, etc""",

    'description': """
        Long description of module's purpose
    """,

    'author': "ITGrupo",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'kardex', 'sale_stock', 'purchase', 'account', 'calquipa_personalizacion_it',
                'stock_picking_partner'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/logistica_menu.xml',
        'views/logistica_ruta.xml',
        'views/logistica_transporte_tarifa.xml',
        'views/logistica_transporte_tipo.xml',
        'views/sale_order.xml',
        'views/res_partner.xml',
        'views/stock_picking.xml',
        'views/logistica_pedidos.xml',
        'wizard/purchase_wizard.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
# -*- coding: utf-8 -*-

{
    'name': 'Purchase Margin Calculator',
    'version': '18.0.1.0.0',
    'summary': 'Track last purchase cost, UoM conversion, and real margin on products',
    'description': 'Calculates real purchase margin with UoM conversion, POS price detection, '
                   'price history tracking, and configurable margin alerts. '
                   'Does NOT overwrite standard_price.',
    'author': 'NeuroDev',
    'website': 'https://github.com/neurodev-apps',
    'license': 'OPL-1',
    'price': 29.00,
    'currency': 'EUR',
    'category': 'Inventory/Purchase',
    'depends': ['product', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'security/purchase_price_history_rule.xml',
        'data/ir_cron.xml',
        'views/res_config_settings_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': '_post_init_populate_history',
}

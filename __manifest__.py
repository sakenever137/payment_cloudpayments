{
    'name': 'CloudPayments Payment',
    'version': '1.0',
    'summary': 'Integration with CloudPayments',
    'category': 'Accounting/Payment Providers',
    'author': 'Saken Serdaly',
    'depends': ['payment'],
    'data': [
        'views/payment_cloudpayments_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_cloudpayments.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_cloudpayments/static/src/js/payment_extension.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',

}

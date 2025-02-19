from odoo import _

SUPPORTED_CURRENCIES = [
    'KZT',
    'USD',
]

LANGUAGE_CODES_MAPPING = {
    'en_US': 'en-US',
    'kz_KZ': 'kk-KZ',
    'ru_RU': 'ru-RU',
}

DEFAULT_PAYMENT_METHODS_CODES = [
    # Primary payment methods.
    'card',
    # Brand payment methods.
    'visa',
    'mastercard',
    'maestro'
]
RESULT_CODES_MAPPING = {
    'done': 'Completed',
}
PAYMENT_METHODS_MAPPING = {
    'visa': 'Visa',
    'mastercard': 'MasterCard',
    'maestro': 'Maestro'
}
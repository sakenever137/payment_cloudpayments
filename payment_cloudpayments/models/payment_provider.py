import base64
import hashlib
import hmac

from odoo import models, fields

from .. import const, utils


class PaymentProviderCloudPayments(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[
        ('cloudpayments', 'CloudPayments')
    ], ondelete={'cloudpayments': 'set default'})
    cloudpayments_public_id = fields.Char(string="CloudPayments Public ID", required_if_provider='cloudpayments')
    cloudpayments_secret_key = fields.Char(string="CloudPayments Secret Key", required_if_provider='cloudpayments')

    def _cloudpayments_calculate_signature(self, message):
        """ See: https://developers.cloudpayments.kz/#proverka-uvedomleniy.

        :param str message: сообщением является тело запроса
        :return: expected_signature 
        """
        api_key = self.cloudpayments_secret_key
        expected_signature = base64.b64encode(
            hmac.new(api_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
        ).decode('utf-8')
        
        return expected_signature

    def _get_supported_currencies(self):
        """ Override of `payment` to return the supported currencies. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'cloudpayments':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies
    
    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'cloudpayments':
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES
    
    def _cloudpayments_get_publishable_key(self):
        """ Return the publishable key of the provider.

        This getter allows fetching the publishable key from a QWeb template and through Cloudpayments's
        utils.

        Note: `self.ensure_one()

        :return: The publishable key.
        :rtype: str
        """
        self.ensure_one()

        return utils.get_publishable_key(self.sudo())
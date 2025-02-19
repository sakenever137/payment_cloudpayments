# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils
from .. import const


class PaymentTransactionCloudPayments(models.Model):
    _inherit = 'payment.transaction'
    

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator='-', **kwargs):
        """ Override of payment to ensure that CloudPayments requirements for references are satisfied.

        CloudPaymentsrequirements for transaction are as follows:
        - References must be unique at provider level for a given merchant account.
          This is satisfied by singularizing the prefix with the current datetime. If two
          transactions are created simultaneously, `_compute_reference` ensures the uniqueness of
          references by suffixing a sequence number.

        :param str provider_code: The code of the provider handling the transaction
        :param str prefix: The custom prefix used to compute the full reference
        :param str separator: The custom separator used to separate the prefix from the suffix
        :return: The unique reference for the transaction
        :rtype: str
        """
        if provider_code == 'cloudpayments':
            if not prefix:
                # If no prefix is provided, it could mean that a module has passed a kwarg intended
                # for the `_compute_reference_prefix` method, as it is only called if the prefix is
                # empty. We call it manually here because singularizing the prefix would generate a
                # default value if it was empty, hence preventing the method from ever being called
                # and the transaction from received a reference named after the related document.
                prefix = self.sudo()._compute_reference_prefix(
                    provider_code, separator, **kwargs
                ) or None
            prefix = payment_utils.singularize_reference_prefix(prefix=prefix, separator=separator)
        return super()._compute_reference(
            provider_code, prefix=prefix, separator=separator, **kwargs
        )
    
    def _get_specific_processing_values(self, processing_values):
        """ Override of `payment` to return CloudPayments processing values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the
                                       transaction.
        :return: The provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != 'cloudpayments':
            return res
        
        lang = const.LANGUAGE_CODES_MAPPING.get(self._context.get("lang"))

        return {
            "reference_id": self.id,
            "language": lang,
            'cloudpayments_public_id': self.provider_id._cloudpayments_get_publishable_key(),
            'currency_name': self.currency_id.name,
            'email': self.partner_id.email,
            'payer': {
                'firstName': self.partner_id.name,
                'address': self.partner_id.street,
                'street': self.partner_id.street2,
                'city': self.partner_id.city,
                'country': self.partner_id.country_id.name,
                'phone': self.partner_id.phone,
                'postcode': self.partner_id.zip,
            }
        }
    
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on CloudPayments data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'cloudpayments' or len(tx) == 1:
            return tx

        reference = notification_data.get('InvoiceId')
        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'cloudpayments')])
        if not tx:
            raise ValidationError(
                "CloudPayments: " + _("No transaction found matching reference %s.", reference)
            )

        return tx
    
    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on CloudPayments data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'cloudpayments':
            return

        # Update the provider reference.
        self.provider_reference = notification_data.get('TransactionId')

        # Update the payment method
        payment_method_type = notification_data.get('CardType', '')
        payment_method = self.env['payment.method']._get_from_code(
            payment_method_type, mapping=const.PAYMENT_METHODS_MAPPING
            )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        status = notification_data.get('Status')
        if status and status == const.RESULT_CODES_MAPPING.get('done'):
            self._set_done()
        else:  # 'failure'
            # See https://developers.cloudpayments.kz/#fail
            error_code = notification_data.get('ReasonCode')
            self._set_error(
                "CloudPayments: " + _("The payment encountered an error with code %s", error_code)
            )
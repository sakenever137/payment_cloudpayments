import logging
import hmac
import json
import pprint

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

from .. import utils


_logger = logging.getLogger(__name__)


class CloudpaymentController(http.Controller):
    _webhook_url = '/payment/cloudpayments/webhook'
    _return_url = '/payment/cloudpayments/return'
    
    @http.route(_return_url, type='http', auth='public', methods=['GET'])
    def cloudpayments_return_from_checkout(self, **data):
        """ Processes notification data sent by CloudPayments after redirect.  
        
        :param dict data: Notification
        """
        # Не обрабатываем данные уведомления, так как они не содержат полезной информации.
        return request.redirect('/payment/status')


    @http.route('/payment/cloudpayments/check', type='http', auth='public', methods=['GET','POST'], csrf=False)
    def cloudpayments_check(self, **kwargs):
        """
        Handle the 'check' request from CloudPayments.

        :param kwargs: Parameters sent from CloudPayments
        :return: JSON response
        """
        _logger.info("Received check request: %s", kwargs)

        # Проверяем наличие обязательных параметров
        required_params = ['InvoiceId', 'Amount']
        for param in required_params:
            if param not in kwargs:
                _logger.error("Missing required parameter: %s", param)
                return json.dumps({
                    "code": 13,  # Код ошибки: обязательный параметр не передан
                })

        try:
            # Извлекаем параметры
            invoice_id = kwargs.get('InvoiceId')
            amount = float(kwargs.get('Amount'))

            # Проверка существования транзакции
            tx_sudo = request.env['payment.transaction'].sudo().search([('reference', '=', invoice_id)], limit=1)
            if not tx_sudo:
                _logger.error("Transaction not found for InvoiceId: %s", invoice_id)
                return json.dumps({
                    "code": 10,  # Код ошибки: Транзакция не найдена
                })
            
            # Проверка соответствия суммы
            if tx_sudo.amount != amount:
                _logger.error("Amount mismatch: expected %s, got %s", tx_sudo.amount, amount)
                return json.dumps({
                    "code": 11,  # Код ошибки: Сумма не совпадает
                })
            
            headers_and_body = {
                "headers": {k: v for k, v in request.httprequest.headers.items()},
                "raw_body": request.httprequest.get_data(as_text=True) if request.httprequest.method == 'POST' else request.httprequest.query_string.decode('utf-8'),
            }
            self._verify_notification_signature(headers_and_body, tx_sudo)
            # Если все проверки прошли успешно
            tx_sudo._set_pending()
            _logger.info("Check successful for InvoiceId: %s", invoice_id)
            return json.dumps({
                "code": 0,  # Код успешного выполнения
            })

        except Exception as e:
            _logger.exception("Error during payment check: %s", str(e))
            return json.dumps({
                "code": 20,  # Код ошибки: Внутренняя ошибка сервера
            })
        
    @http.route(_webhook_url, type='http', auth='public', methods=['GET','POST'], csrf=False)
    def cloudpayments_webhook(self, **data):
        """ Process the notification data sent by CloudPayments to the webhook.

        See https://developers.cloudpayments.kz/#uvedomleniya.

        :param dict data: The notification data.
        :return: The '{"code":0}' string to acknowledge the notification
        :rtype: str
        """
        _logger.info("Notification received from CloudPayments with data:\n%s", pprint.pformat(data))
        try:
            # Check the integrity of the notification.
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'cloudpayments', data
            )
            
            headers_and_body = {
                "headers": {k: v for k, v in request.httprequest.headers.items()},
                "raw_body": request.httprequest.get_data(as_text=True) if request.httprequest.method == 'POST' else request.httprequest.query_string.decode('utf-8'),
            }
            _logger.info("Notification received from CloudPayments with headers_and_body:\n%s", headers_and_body)

            self._verify_notification_signature(headers_and_body, tx_sudo)

            tx_sudo._handle_notification_data('cloudpayments', data)
        except ValidationError:  # Acknowledge the notification to avoid getting spammed.
            _logger.exception("Unable to handle the notification data; skipping to acknowledge.")

        return json.dumps({
                "code": 0,  
            })

    @staticmethod
    def _verify_notification_signature(headers_and_body, tx_sudo):
        """ Verify if the received signature matches the expected one.
        :param dict headers_and_body: Notification data containing the received signature
        :param str tx_sudo: payment.transaction sudo record
        :return: None
        :raise: :class:`werkzeug.exceptions.Forbidden` if the signatures do not match
        """

        received_signature = headers_and_body.get('headers', {}).get('Content-Hmac')
        if not received_signature:
            _logger.warning("Получено уведомление без подписи")
            raise Forbidden("Missing signature in notification")
        
        message = headers_and_body.get('raw_body', '')

        expected_signature = tx_sudo.provider_id._cloudpayments_calculate_signature(message)
        _logger.info("Notification received from CloudPayments with expected_signature:\n%s", expected_signature)

        if not hmac.compare_digest(received_signature, expected_signature):
            _logger.warning("Получено уведомление с недействительной подписью")
            raise Forbidden("Invalid signature in notification")
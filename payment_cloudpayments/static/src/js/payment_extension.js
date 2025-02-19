    /** @odoo-module **/
    /* global CloudPayment */

    import { _t } from "@web/core/l10n/translation";
    import { loadJS } from "@web/core/assets";

    import paymentForm from '@payment/js/payment_form';
    import { ConfirmationDialog } from '@web/core/confirmation_dialog/confirmation_dialog';

    paymentForm.include({
            /**
             * Display an error dialog.
             *
             * @private
             * @param {string} title - The title of the dialog.
             * @param {string} errorMessage - The error message.
             * @return {void}
             */
            _displayErrorDialog(title, errorMessage = '') {
                this.call('dialog', 'add', ConfirmationDialog, { title: title, body: errorMessage || "" });
            },

            /**
             * Update the payment context to set the flow to 'direct'.
             *
             * @override method from @payment/js/payment_form
             * @private
             * @param {number} providerId - The id of the selected payment option's provider.
             * @param {string} providerCode - The code of the selected payment option's provider.
             * @param {number} paymentOptionId - The id of the selected payment option
             * @param {string} paymentMethodCode - The code of the selected payment method, if any.
             * @param {string} flow - The online payment flow of the selected payment option.
             * @return {void}
             */ 
            async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
                if (providerCode !== 'cloudpayments') {
                    this._super(...arguments);
                    return;
                }

                if (flow === 'token') {
                    return; // No need to update the flow for tokens.
                }

                // Overwrite the flow of the select payment method.
                this._setPaymentFlow('direct');
            },

            async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
                if (providerCode !== 'cloudpayments') {
                    this._super(...arguments);
                    return;
                }
                await loadJS('https://widget.tiptoppay.kz/bundles/widget.js');
                const widget = new tiptop.Widget({
                    language: processingValues.language, 
                });
                widget.pay('charge', 
                    {
                        publicId: processingValues.cloudpayments_public_id,
                        amount: processingValues.amount,
                        currency:  processingValues.currency_name,
                        accountId: processingValues.partner_id,
                        invoiceId: processingValues.reference,
                        email: processingValues.email,
                        requireEmail: true,
                        description: `Номер платежа ${processingValues.reference}` ,
                        payer: processingValues.payer,
                    }, {
                        onComplete: async function (paymentResult) {
                            window.location = '/payment/cloudpayments/return';
                        },

                        onFail: async (paymentResult) => {
                            this._displayErrorDialog(_t("Payment processing failed"), paymentResult);
                            this._enableButton();
                        },
                        
                    }
                );
            },
        }
    );

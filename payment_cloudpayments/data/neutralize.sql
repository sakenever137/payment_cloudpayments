-- disable payumoney payment provider
UPDATE payment_provider
   SET cloudpayments_public_id = NULL,
       cloudpayments_secret_key = NULL;

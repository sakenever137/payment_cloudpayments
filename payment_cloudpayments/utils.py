
def get_publishable_key(provider_sudo):
    """ Return the publishable key for CloudPayments.

    :param recordset provider_sudo: The provider on which the key should be read, as a sudoed
                                    `payment.provider` record.
    :return: The publishable key
    :rtype: str
    """
    return provider_sudo.cloudpayments_public_id

def get_secret_key(provider_sudo):
    """ Return the secret key for CloudPayments.

    :param recordset provider_sudo: The provider on which the key should be read, as a sudoed
                                    `payment.provider` record.
    :return: The secret key
    :rtype: str
    """
    return provider_sudo.cloudpayments_secret_key

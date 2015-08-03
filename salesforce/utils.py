# django-salesforce

"""
A set of tools to deal with Salesforce actions that
cannot or can hardly be implemented using the generic
relational database abstraction.

The Salesforce REST API is missing a few endpoints that
are available in the SOAP API. We are using `beatbox` as
a workaround for those specific actions (such as Lead-Contact
conversion).
"""

from django.conf import settings

from salesforce import auth

try:
    import beatbox
except ImportError:
    beatbox = None


def convert_lead(lead, converted_status="Qualified - converted"):
    """
    Convert `lead` using the `convertLead()` endpoint exposed
    by the SOAP API.

    The parameter `lead` is expected to be a Lead object that
    has not been converted yet.

    -- BEWARE --
    The current implementation won't work in case your `Contact`,
    `Account` or `Opportunity` objects have some custom **and**
    required fields. This arises from the fact that `convertLead()`
    is only meant to deal with standard Salesforce fields, so it does
    not really care about populating custom fields at insert time.
    """
    if not beatbox:
        raise RuntimeError("To use convert_lead, you'll need to install the Beatbox library.")

    soap_client = beatbox.PythonClient()
    settings_dict = settings.DATABASES['salesforce']

    # By default `beatbox` will assume we are trying to log in with a
    # production account (i.e., using login.salesforce.com). If we want
    # to use a sandbox, then we need to explicitly set the login url of
    # our `beatbox` client.
    if "test.salesforce.com" in settings_dict['HOST']:
        soap_client.serverUrl = 'https://test.salesforce.com/services/Soap/u/33.0'
    if settings_dict['USER'] == 'auth token':
        auth_data = auth.authenticate()
        soap_url = str(auth_data['instance_url']) + settings_dict["SOAP_URL"]
        soap_client.useSession(auth_data['access_token'], soap_url)
    else:
        soap_client.login(settings_dict['USER'], settings_dict['PASSWORD'])

    response = soap_client.convertLead({
        'leadId': lead.pk,
        'convertedStatus': converted_status,
        'doNotCreateOpportunity': True,
        'ownerId': settings.SALESFORCE_OWNER_ID,
    })

    if "Exception" in str(response):
        raise RuntimeError("The Lead conversion failed: {}".format(str(response)))

    return response

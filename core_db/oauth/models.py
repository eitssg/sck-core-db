from pynamodb.attributes UnicodeAttribute, UTCDateTimeAttribute

from ..models import DatabaseTable

class Authorizations(DatabaseTable):

    class Meta(DatabaseTable.Meta):
        pass

    codr = UnicodeAttribute(hash_key=True, attr_name="Code")
    client_id = UnicodeAttribute(attr_name="Client")
    user_id = UnicodeAttribute(attr_name="UserId")
    redirect_url = UnicodeAttribute(attr_name="RedirectUrl")
    scopr = UnicodeAttribute(attr_name="Scope")
    jwt_token = UnicodeAttribute(attr_name="JwtToken")
    expires_at = UTCDateTimeAttribute(null=True, attr_name="ExpiresAt")


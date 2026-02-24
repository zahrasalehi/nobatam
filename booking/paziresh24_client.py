"""Paziresh24 API client using Bearer token (OAuth access_token)."""
import requests


class Paziresh24APIError(Exception):
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


def get_api_client(request):
    """Return a client that uses the session access_token."""
    from django.conf import settings as django_settings
    token = request.session.get('paziresh24_access_token')
    if not token:
        raise Paziresh24APIError('Not authenticated', status_code=401)
    return Paziresh24Client(
        base_url=getattr(django_settings, 'PAZIRESH24_API_BASE', 'https://apigw.paziresh24.com'),
        access_token=token,
    )


class Paziresh24Client:
    """Minimal client for apigw.paziresh24.com with Bearer auth."""

    def __init__(self, base_url=None, access_token=None):
        from django.conf import settings as django_settings
        self.base_url = (base_url or getattr(django_settings, 'PAZIRESH24_API_BASE', 'https://apigw.paziresh24.com')).rstrip('/')
        self.access_token = access_token
        self._session = requests.Session()
        self._session.headers['Authorization'] = f'Bearer {access_token}'
        self._session.headers['Accept'] = 'application/json'
        self._session.headers['Content-Type'] = 'application/json'

    def _request(self, method, path, params=None, json=None, timeout=30):
        url = f"{self.base_url}{path}"
        try:
            resp = self._session.request(method, url, params=params, json=json, timeout=timeout)
        except requests.RequestException as e:
            raise Paziresh24APIError(str(e))
        if resp.status_code >= 400:
            raise Paziresh24APIError(
                resp.text or f"HTTP {resp.status_code}",
                status_code=resp.status_code,
                response=resp,
            )
        if not resp.content:
            return None
        return resp.json()

    def search(self, text, center=None, result_type=None, expertise=None):
        """GET /v1/search - search doctors/providers."""
        params = {'text': text}
        if center is not None:
            params['center'] = center
        if result_type:
            params['result_type'] = result_type
        if expertise:
            params['expertise'] = expertise
        return self._request('GET', '/v1/search', params=params)

    def get_memberships(self, provider_id):
        """GET /v1/memberships?provider_id=... - list doctor's centers."""
        return self._request('GET', '/v1/memberships', params={'provider_id': provider_id})

    def get_services(self, membership_id):
        """GET /v1/services?membership_id=... - list services for a membership."""
        return self._request('GET', '/v1/services', params={'membership_id': membership_id})

    def get_availability(self, service_id, membership_id, start_time=None, end_time=None, timezone=None):
        """GET /v1/availability - list available slots."""
        params = {
            'service_id': service_id,
            'membership_id': membership_id,
        }
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        if timezone:
            params['timezone'] = timezone
        return self._request('GET', '/v1/availability', params=params)

    def create_appointment(self, membership_id, service_id, time=None, reserve_id=None, sub_user=None):
        """POST /v1/appointments - create appointment (time or reserve_id required)."""
        body = {
            'membership_id': membership_id,
            'service_id': service_id,
        }
        if time:
            body['time'] = time
        if reserve_id:
            body['reserve_id'] = reserve_id
        if sub_user is not None:
            body['sub_user'] = sub_user
        return self._request('POST', '/v1/appointments', json=body)

    def reserve_slot(self, membership_id, service_id, time):
        """POST /v1/reserve - hold a slot for 5 minutes."""
        return self._request('POST', '/v1/reserve', json={
            'membership_id': membership_id,
            'service_id': service_id,
            'time': time,
        })

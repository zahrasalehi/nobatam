"""Business logic: book first available slot for a provider."""
from datetime import datetime, timedelta, timezone

from .paziresh24_client import Paziresh24APIError


def book_first_available(client, provider_id, days_ahead=30):
    """
    For the given provider_id: get first membership, first service,
    fetch availability for the next days_ahead days, pick first slot, create appointment.
    Returns the appointment object from the API.
    """
    memberships_resp = client.get_memberships(provider_id)
    memberships = (memberships_resp or {}).get('memberships') or []
    if not memberships:
        raise Paziresh24APIError('هیچ مرکزی برای این پزشک یافت نشد.', status_code=404)

    membership = memberships[0]
    membership_id = membership.get('id')
    if not membership_id:
        raise Paziresh24APIError('شناسه membership نامعتبر.', status_code=502)

    services = client.get_services(membership_id)
    if isinstance(services, list):
        service_list = services
    else:
        service_list = (services or [])
    if not service_list:
        raise Paziresh24APIError('هیچ سرویسی برای این مرکز یافت نشد.', status_code=404)

    service = service_list[0]
    service_id = service.get('id') if isinstance(service, dict) else None
    if not service_id:
        raise Paziresh24APIError('شناسه service نامعتبر.', status_code=502)

    now = datetime.now(timezone.utc)
    start_time = now.isoformat()
    end_time = (now + timedelta(days=days_ahead)).isoformat()

    availability = client.get_availability(
        service_id=service_id,
        membership_id=membership_id,
        start_time=start_time,
        end_time=end_time,
    )

    first_slot_time = _extract_first_slot(availability)
    if not first_slot_time:
        raise Paziresh24APIError('در بازه زمانی انتخاب شده نوبت خالی یافت نشد.', status_code=404)

    appointment = client.create_appointment(
        membership_id=membership_id,
        service_id=service_id,
        time=first_slot_time,
    )
    return appointment


def _extract_first_slot(availability):
    """From API response (list of {date, slots: [{time}]}), return earliest slot time as ISO string."""
    if not availability or not isinstance(availability, list):
        return None
    all_times = []
    for day in availability:
        slots = (day or {}).get('slots') or []
        for slot in slots:
            t = (slot or {}).get('time')
            if t:
                all_times.append(t)
    if not all_times:
        return None
    all_times.sort()
    return all_times[0]

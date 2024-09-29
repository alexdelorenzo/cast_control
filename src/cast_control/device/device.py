from __future__ import annotations

from typing import NamedTuple
from uuid import UUID

from pychromecast import get_chromecast_from_host, get_chromecasts, get_listed_chromecasts

from ..base import DEFAULT_DEVICE_NAME, DEFAULT_RETRY_WAIT, Device, NO_PORT, NO_STR, Seconds


class Host(NamedTuple):
  host: str
  port: int | None = NO_PORT
  uuid: str = NO_STR
  model_name: str = NO_STR
  friendly_name: str = DEFAULT_DEVICE_NAME


def get_device_via_host(
  host: str,
  name: str | None = DEFAULT_DEVICE_NAME,
  retry_wait: Seconds | float | None = DEFAULT_RETRY_WAIT,
) -> Device | None:
  name = name or DEFAULT_DEVICE_NAME
  info = Host(host, friendly_name=name)

  if device := get_chromecast_from_host(info, retry_wait=float(retry_wait)):
    device.wait()
    return device

  return None  # explicit


def get_devices(retry_wait: Seconds | float | None = DEFAULT_RETRY_WAIT) -> list[Device]:
  devices, service_browser = get_chromecasts(retry_wait=float(retry_wait))
  service_browser.stop_discovery()

  return devices


def get_listed_devices(
  name: str | None = None,
  uuid: UUID | str | None = None,
  retry_wait: Seconds | float | None = DEFAULT_RETRY_WAIT,
) -> list[Device]:
  devices, service_browser = get_listed_chromecasts(
    friendly_names=[name],
    uuids=[uuid],
    retry_wait=float(retry_wait),
  )
  service_browser.stop_discovery()

  return devices


def get_first(devices: list[Device]) -> Device | None:
  if not devices:
    return None

  first, *_ = devices
  first.wait()

  return first


def get_device_via_uuid(
  uuid: UUID | str | None = None,
  retry_wait: Seconds | float | None = DEFAULT_RETRY_WAIT,
) -> Device | None:
  devices = get_devices(retry_wait)

  if not uuid:
    return get_first(devices)

  uuid = UUID(uuid)

  for device in devices:
    if device.uuid == uuid:
      device.wait()

      return device

  if devices := get_listed_devices(uuid=uuid, retry_wait=retry_wait):
    return get_first(devices)

  return None


def get_device(
  name: str | None = None,
  retry_wait: Seconds | float | None = DEFAULT_RETRY_WAIT,
) -> Device | None:
  devices = get_devices(retry_wait)

  if not name:
    return get_first(devices)

  devices += get_listed_devices(name, retry_wait=retry_wait)

  name = name.casefold()

  for device in devices:
    if device.name.casefold() == name:
      device.wait()

      return device

  return None


def find_device(
  name: str | None = DEFAULT_DEVICE_NAME,
  host: str | None = None,
  uuid: UUID | str | None = None,
  retry_wait: Seconds | float | None = DEFAULT_RETRY_WAIT,
) -> Device | None:
  device: Device | None = None

  if host:
    device = get_device_via_host(host, name, retry_wait)

  if uuid and not device:
    device = get_device_via_uuid(uuid, retry_wait)

  if name and not device:
    device = get_device(name, retry_wait)

  no_identifiers = not (host or name or uuid)

  if no_identifiers:
    device = get_device(retry_wait=retry_wait)

  return device

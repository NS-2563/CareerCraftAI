import socket
import ipaddress
from urllib.parse import urlparse
from typing import Optional


PRIVATE_NETWORKS = [
    "127.0.0.0/8",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "::1/128",
    "fc00::/7",
    "fe80::/10",
]


def is_private_ip(hostname: str) -> bool:
    try:
        ip = ipaddress.ip_address(hostname)
        for network_cidr in PRIVATE_NETWORKS:
            if ip in ipaddress.ip_network(network_cidr, strict=False):
                return True
        return False
    except ValueError:
        return False


def resolve_host(hostname: str) -> Optional[str]:
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


def validate_url(url: str, allowed_domains: Optional[list] = None) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    if allowed_domains:
        if not any(hostname == domain or hostname.endswith("." + domain) for domain in allowed_domains):
            return False
    if is_private_ip(hostname):
        return False
    resolved = resolve_host(hostname)
    if resolved and is_private_ip(resolved):
        return False
    return True

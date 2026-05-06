from __future__ import annotations


def build_sip_uri(
    user: str,
    domain: str,
    port: int | None = None,
    transport: str | None = None,
) -> str:
    uri = f"sip:{user}@{domain}"
    if port:
        uri = f"{uri}:{port}"
    if transport:
        uri = f"{uri};transport={transport}"
    return uri

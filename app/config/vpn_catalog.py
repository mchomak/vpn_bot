import json
from dataclasses import dataclass
from typing import Optional
from app.config.settings import settings


@dataclass
class Plan:
    key: str
    title: str
    price: int
    duration_days: int


@dataclass
class VpnServer:
    code: str
    title: str
    flag: str
    enabled: bool
    plans: list[Plan]

    def get_plan(self, plan_key: str) -> Optional[Plan]:
        for plan in self.plans:
            if plan.key == plan_key:
                return plan
        return None


class VpnCatalog:
    def __init__(self) -> None:
        self._servers: dict[str, VpnServer] = {}
        self._load()

    def _load(self) -> None:
        with open(settings.vpn_config_path, encoding="utf-8") as f:
            data = json.load(f)
        for code, srv in data["vpn_servers"].items():
            if not srv.get("enabled", False):
                continue
            self._servers[code] = VpnServer(
                code=code,
                title=srv["title"],
                flag=srv.get("flag", ""),
                enabled=srv["enabled"],
                plans=[Plan(**p) for p in srv["plans"]],
            )

    def servers(self) -> list[VpnServer]:
        return list(self._servers.values())

    def get_server(self, code: str) -> Optional[VpnServer]:
        return self._servers.get(code)


catalog = VpnCatalog()

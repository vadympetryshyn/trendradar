"""Admin server metrics route."""

import asyncio
import time
from typing import Annotated

import httpx
import psutil
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_admin_user
from app.models.user import User

router = APIRouter(prefix="/admin/metrics", tags=["admin-metrics"])

AdminUser = Annotated[User, Depends(get_admin_user)]


class CpuMetrics(BaseModel):
    percent: float
    count: int
    count_logical: int
    per_core_percent: list[float]


class MemoryMetrics(BaseModel):
    total_mb: float
    used_mb: float
    available_mb: float
    percent: float


class DiskMetrics(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float


class ContainerMetrics(BaseModel):
    name: str
    status: str
    cpu_percent: float
    memory_mb: float
    memory_limit_mb: float
    memory_percent: float


class ServerMetrics(BaseModel):
    cpu: CpuMetrics
    memory: MemoryMetrics
    disk: DiskMetrics
    containers: list[ContainerMetrics]
    uptime_seconds: float
    docker_available: bool


def _get_cpu() -> CpuMetrics:
    per_core = psutil.cpu_percent(interval=0.3, percpu=True)
    overall = sum(per_core) / len(per_core) if per_core else 0.0
    return CpuMetrics(
        percent=round(overall, 1),
        count=psutil.cpu_count(logical=False) or 1,
        count_logical=psutil.cpu_count(logical=True) or 1,
        per_core_percent=[round(v, 1) for v in per_core],
    )


def _get_memory() -> MemoryMetrics:
    m = psutil.virtual_memory()
    return MemoryMetrics(
        total_mb=round(m.total / 1024 / 1024, 1),
        used_mb=round(m.used / 1024 / 1024, 1),
        available_mb=round(m.available / 1024 / 1024, 1),
        percent=m.percent,
    )


def _get_disk() -> DiskMetrics:
    d = psutil.disk_usage("/")
    return DiskMetrics(
        total_gb=round(d.total / 1024 / 1024 / 1024, 2),
        used_gb=round(d.used / 1024 / 1024 / 1024, 2),
        free_gb=round(d.free / 1024 / 1024 / 1024, 2),
        percent=d.percent,
    )


def _get_uptime() -> float:
    return round(time.time() - psutil.boot_time(), 0)


def _parse_container_stats(c: dict, s: dict) -> ContainerMetrics:
    name = c["Names"][0].lstrip("/") if c.get("Names") else c["Id"][:12]

    try:
        cpu_delta = (
            s["cpu_stats"]["cpu_usage"]["total_usage"]
            - s["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_delta = s["cpu_stats"].get("system_cpu_usage", 0) - s["precpu_stats"].get(
            "system_cpu_usage", 0
        )
        num_cpus = s["cpu_stats"].get("online_cpus", 1)
        cpu_pct = (cpu_delta / system_delta * num_cpus * 100.0) if system_delta > 0 else 0.0
    except (KeyError, ZeroDivisionError):
        cpu_pct = 0.0

    try:
        mem_stats = s.get("memory_stats", {})
        mem_usage = mem_stats.get("usage", 0)
        mem_cache = mem_stats.get("stats", {}).get("cache", 0)
        mem_real = max(0, mem_usage - mem_cache)
        mem_limit = mem_stats.get("limit", 1) or 1
        mem_pct = mem_real / mem_limit * 100.0
    except (KeyError, ZeroDivisionError):
        mem_real = 0
        mem_limit = 1
        mem_pct = 0.0

    return ContainerMetrics(
        name=name,
        status=c.get("Status", "unknown"),
        cpu_percent=round(max(0.0, cpu_pct), 1),
        memory_mb=round(mem_real / 1024 / 1024, 1),
        memory_limit_mb=round(mem_limit / 1024 / 1024, 1),
        memory_percent=round(max(0.0, mem_pct), 1),
    )


async def _get_docker_containers() -> tuple[list[ContainerMetrics], bool]:
    try:
        transport = httpx.AsyncHTTPTransport(uds="/var/run/docker.sock")
        async with httpx.AsyncClient(
            transport=transport, base_url="http://docker", timeout=8.0
        ) as client:
            r = await client.get("/containers/json")
            if r.status_code != 200:
                return [], False
            containers = r.json()

            async def fetch_stats(c: dict) -> ContainerMetrics | None:
                try:
                    sr = await client.get(
                        f"/containers/{c['Id']}/stats?stream=0", timeout=8.0
                    )
                    return _parse_container_stats(c, sr.json())
                except Exception:
                    name = c["Names"][0].lstrip("/") if c.get("Names") else c["Id"][:12]
                    return ContainerMetrics(
                        name=name,
                        status=c.get("Status", "unknown"),
                        cpu_percent=0.0,
                        memory_mb=0.0,
                        memory_limit_mb=0.0,
                        memory_percent=0.0,
                    )

            results = await asyncio.gather(*[fetch_stats(c) for c in containers])
            return [r for r in results if r is not None], True
    except Exception:
        return [], False


@router.get("", response_model=ServerMetrics)
async def get_metrics(admin: AdminUser) -> ServerMetrics:
    loop = asyncio.get_event_loop()

    cpu_task = loop.run_in_executor(None, _get_cpu)
    memory_task = loop.run_in_executor(None, _get_memory)
    disk_task = loop.run_in_executor(None, _get_disk)
    uptime_task = loop.run_in_executor(None, _get_uptime)
    docker_task = _get_docker_containers()

    cpu, memory, disk, uptime, (containers, docker_available) = await asyncio.gather(
        cpu_task, memory_task, disk_task, uptime_task, docker_task
    )

    return ServerMetrics(
        cpu=cpu,
        memory=memory,
        disk=disk,
        containers=containers,
        uptime_seconds=uptime,
        docker_available=docker_available,
    )

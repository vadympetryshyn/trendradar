from app.schemas.niche import NicheResponse, NicheDetailResponse
from app.schemas.trend import (
    TrendListItem,
    TrendDetail,
    TrendListResponse,
    TrendSearchRequest,
    TrendSearchResult,
    TrendSearchResponse,
)
from app.schemas.admin import (
    NicheScheduleStatus,
    SchedulerStatusResponse,
    SchedulerStartRequest,
    SchedulerRunRequest,
    ManualTriggerResponse,
    DashboardStatsResponse,
    UpdateIntervalRequest,
)
from app.schemas.task import (
    CollectionTaskResponse,
    CollectionTaskListResponse,
)
from app.schemas.external import (
    ExternalTrendListItem,
    ExternalTrendDetail,
    ExternalTrendListResponse,
    ExternalTrendSearchResult,
    ExternalTrendSearchResponse,
    ExternalNicheResponse,
    VectorSearchRequest,
)

__all__ = [
    "NicheResponse",
    "NicheDetailResponse",
    "TrendListItem",
    "TrendDetail",
    "TrendListResponse",
    "TrendSearchRequest",
    "TrendSearchResult",
    "TrendSearchResponse",
    "NicheScheduleStatus",
    "SchedulerStatusResponse",
    "SchedulerStartRequest",
    "SchedulerRunRequest",
    "ManualTriggerResponse",
    "DashboardStatsResponse",
    "UpdateIntervalRequest",
    "CollectionTaskResponse",
    "CollectionTaskListResponse",
    "ExternalTrendListItem",
    "ExternalTrendDetail",
    "ExternalTrendListResponse",
    "ExternalTrendSearchResult",
    "ExternalTrendSearchResponse",
    "ExternalNicheResponse",
    "VectorSearchRequest",
]

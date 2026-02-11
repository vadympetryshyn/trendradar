from app.schemas.niche import NicheResponse
from app.schemas.trend import (
    TrendItemResponse,
    TrendAnalysisResponse,
    TrendAnalysisSummaryResponse,
    PaginatedHistoryResponse,
)
from app.schemas.schedule import ScheduleConfigCreate, ScheduleConfigResponse, ScheduleConfigUpdate
from app.schemas.admin import (
    ManualTriggerResponse,
    TaskStatusResponse,
    AnalysisListItem,
    PaginatedAnalysesResponse,
    TaskListItem,
    PaginatedTasksResponse,
)

__all__ = [
    "NicheResponse",
    "TrendItemResponse",
    "TrendAnalysisResponse",
    "TrendAnalysisSummaryResponse",
    "PaginatedHistoryResponse",
    "ScheduleConfigCreate",
    "ScheduleConfigResponse",
    "ScheduleConfigUpdate",
    "ManualTriggerResponse",
    "TaskStatusResponse",
    "AnalysisListItem",
    "PaginatedAnalysesResponse",
    "TaskListItem",
    "PaginatedTasksResponse",
]

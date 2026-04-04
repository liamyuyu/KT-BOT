"""
监控指标数据模型
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class SystemMetricsData(BaseModel):
    """系统资源指标数据"""
    cpu_percent: float = Field(..., description="CPU 使用率 (%)")
    memory_percent: float = Field(..., description="内存使用率 (%)")
    memory_available_gb: float = Field(..., description="可用内存 (GB)")
    memory_total_gb: float = Field(..., description="总内存 (GB)")
    disk_percent: float = Field(..., description="磁盘使用率 (%)")
    disk_free_gb: float = Field(..., description="可用磁盘空间 (GB)")
    disk_total_gb: float = Field(..., description="总磁盘空间 (GB)")
    timestamp: str = Field(..., description="时间戳")


class DatabaseMetricsData(BaseModel):
    """数据库连接池指标数据"""
    pool_size: int = Field(..., description="连接池大小")
    pool_checked_out: int = Field(..., description="已签出连接数")
    pool_overflow: int = Field(..., description="溢出连接数")
    pool_checked_in: int = Field(..., description="已签入连接数")
    pool_usage_percent: float = Field(..., description="连接池使用率 (%)")
    timestamp: str = Field(..., description="时间戳")


class APIStatisticsData(BaseModel):
    """API 性能统计数据"""
    total_requests: int = Field(..., description="总请求数")
    avg_response_time_ms: float = Field(..., description="平均响应时间 (ms)")
    p50_response_time_ms: float = Field(..., description="P50 响应时间 (ms)")
    p95_response_time_ms: float = Field(..., description="P95 响应时间 (ms)")
    p99_response_time_ms: float = Field(..., description="P99 响应时间 (ms)")
    slowest_endpoints: List[Dict[str, Any]] = Field(..., description="最慢端点列表")
    requests_per_minute: float = Field(..., description="每分钟请求数")
    timestamp: str = Field(..., description="时间戳")


class RetrievalMetricsData(BaseModel):
    """检索性能指标数据"""
    total_searches: int = Field(0, description="总搜索次数")
    avg_search_time_ms: float = Field(0.0, description="平均搜索时间 (ms)")
    p95_search_time_ms: float = Field(0.0, description="P95 搜索时间 (ms)")
    timestamp: str = Field(..., description="时间戳")


class SystemMetricsResponse(BaseModel):
    """系统指标响应"""
    success: bool = Field(True, description="是否成功")
    data: SystemMetricsData = Field(..., description="系统指标数据")


class DatabaseMetricsResponse(BaseModel):
    """数据库指标响应"""
    success: bool = Field(True, description="是否成功")
    data: DatabaseMetricsData = Field(..., description="数据库指标数据")


class APIMetricsResponse(BaseModel):
    """API 指标响应"""
    success: bool = Field(True, description="是否成功")
    data: APIStatisticsData = Field(..., description="API 统计数据")


class RetrievalMetricsResponse(BaseModel):
    """检索指标响应"""
    success: bool = Field(True, description="是否成功")
    data: RetrievalMetricsData = Field(..., description="检索指标数据")


class AllMetricsData(BaseModel):
    """所有指标数据"""
    system: SystemMetricsData = Field(..., description="系统指标")
    database: DatabaseMetricsData = Field(..., description="数据库指标")
    api: APIStatisticsData = Field(..., description="API 统计")
    retrieval: RetrievalMetricsData = Field(..., description="检索指标")


class AllMetricsResponse(BaseModel):
    """所有指标响应"""
    success: bool = Field(True, description="是否成功")
    data: AllMetricsData = Field(..., description="所有指标数据")

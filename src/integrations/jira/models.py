"""
Jira Data Models
Jira 数据模型定义（使用 Pydantic）
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class JiraUser(BaseModel):
    """Jira 用户模型"""
    account_id: str = Field(..., description="用户账号 ID")
    display_name: str = Field(..., description="显示名称")
    email_address: Optional[str] = Field(None, description="邮箱地址")
    avatar_url: Optional[str] = Field(None, description="头像 URL")


class JiraIssueType(BaseModel):
    """Issue 类型模型"""
    id: str = Field(..., description="类型 ID")
    name: str = Field(..., description="类型名称（如 Story, Bug, Task）")
    icon_url: Optional[str] = Field(None, description="图标 URL")


class JiraStatus(BaseModel):
    """Issue 状态模型"""
    id: str = Field(..., description="状态 ID")
    name: str = Field(..., description="状态名称（如 To Do, In Progress, Done）")
    status_category: Optional[str] = Field(None, description="状态分类")


class JiraPriority(BaseModel):
    """Issue 优先级模型"""
    id: str = Field(..., description="优先级 ID")
    name: str = Field(..., description="优先级名称（如 High, Medium, Low）")
    icon_url: Optional[str] = Field(None, description="图标 URL")


class JiraProject(BaseModel):
    """Jira 项目模型"""
    id: str = Field(..., description="项目 ID")
    key: str = Field(..., description="项目 KEY")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    lead: Optional[JiraUser] = Field(None, description="项目负责人")
    avatar_url: Optional[str] = Field(None, description="项目图标 URL")


class JiraComment(BaseModel):
    """Issue 评论模型"""
    id: str = Field(..., description="评论 ID")
    author: JiraUser = Field(..., description="评论作者")
    body: str = Field(..., description="评论内容")
    created: datetime = Field(..., description="创建时间")
    updated: datetime = Field(..., description="更新时间")


class JiraAttachment(BaseModel):
    """Issue 附件模型"""
    id: str = Field(..., description="附件 ID")
    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")
    mime_type: str = Field(..., description="MIME 类型")
    content_url: str = Field(..., description="附件下载 URL")
    created: datetime = Field(..., description="创建时间")
    author: Optional[JiraUser] = Field(None, description="上传者")


class JiraIssue(BaseModel):
    """
    Jira Issue 完整模型
    包含所有核心字段和关联数据
    """
    id: str = Field(..., description="Issue ID")
    key: str = Field(..., description="Issue KEY（如 PROJ-123）")
    summary: str = Field(..., description="Issue 标题")
    description: Optional[str] = Field(None, description="Issue 详细描述")

    # 关联信息
    issue_type: JiraIssueType = Field(..., description="Issue 类型")
    status: JiraStatus = Field(..., description="当前状态")
    priority: Optional[JiraPriority] = Field(None, description="优先级")
    project: JiraProject = Field(..., description="所属项目")

    # 人员信息
    reporter: Optional[JiraUser] = Field(None, description="报告人")
    assignee: Optional[JiraUser] = Field(None, description="经办人")

    # 时间信息
    created: datetime = Field(..., description="创建时间")
    updated: datetime = Field(..., description="更新时间")
    resolution_date: Optional[datetime] = Field(None, description="解决时间")
    due_date: Optional[datetime] = Field(None, description="截止日期")

    # 其他字段
    labels: List[str] = Field(default_factory=list, description="标签列表")
    components: List[str] = Field(default_factory=list, description="组件列表")
    fix_versions: List[str] = Field(default_factory=list, description="修复版本列表")

    # 关联数据
    comments: List[JiraComment] = Field(default_factory=list, description="评论列表")
    attachments: List[JiraAttachment] = Field(default_factory=list, description="附件列表")

    # 原始数据
    raw_data: Optional[Dict[str, Any]] = Field(None, description="完整的原始 JSON 数据")

    # Web URL
    url: Optional[str] = Field(None, description="Issue 的 Web 访问 URL")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class JiraIssuePage(BaseModel):
    """
    Jira Issue 分页查询结果
    """
    issues: List[JiraIssue] = Field(default_factory=list, description="Issue 列表")
    total: int = Field(..., description="总数量")
    start_at: int = Field(..., description="起始位置")
    max_results: int = Field(..., description="每页数量")
    is_last: bool = Field(..., description="是否是最后一页")


class JiraHealthStatus(BaseModel):
    """
    Jira 服务健康状态
    """
    is_connected: bool = Field(..., description="是否连接成功")
    server_info: Optional[Dict[str, Any]] = Field(None, description="服务器信息")
    accessible_projects: List[str] = Field(default_factory=list, description="可访问的项目列表")
    error_message: Optional[str] = Field(None, description="错误信息")
    checked_at: datetime = Field(default_factory=datetime.now, description="检查时间")

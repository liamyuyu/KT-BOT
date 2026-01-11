"""
Confluence Data Models
Confluence 数据模型定义（使用 Pydantic）
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ConfluenceUser(BaseModel):
    """Confluence 用户模型"""
    account_id: Optional[str] = Field(None, description="用户账号 ID（Cloud）")
    username: Optional[str] = Field(None, description="用户名（Server）")
    display_name: str = Field(..., description="显示名称")
    email: Optional[str] = Field(None, description="邮箱地址")
    avatar_url: Optional[str] = Field(None, description="头像 URL")


class ConfluenceSpace(BaseModel):
    """Confluence 空间模型"""
    id: str = Field(..., description="空间 ID")
    key: str = Field(..., description="空间 KEY")
    name: str = Field(..., description="空间名称")
    description: Optional[str] = Field(None, description="空间描述")
    type: str = Field(..., description="空间类型（global, personal）")
    status: Optional[str] = Field(None, description="空间状态")
    homepage_id: Optional[str] = Field(None, description="主页 ID")
    url: Optional[str] = Field(None, description="空间 URL")


class ConfluenceLabel(BaseModel):
    """Confluence 标签模型"""
    id: Optional[str] = Field(None, description="标签 ID")
    name: str = Field(..., description="标签名称")
    prefix: Optional[str] = Field(None, description="标签前缀（global, my, team）")


class ConfluenceAttachment(BaseModel):
    """Confluence 附件模型"""
    id: str = Field(..., description="附件 ID")
    title: str = Field(..., description="附件标题")
    filename: Optional[str] = Field(None, description="文件名")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    media_type: Optional[str] = Field(None, description="媒体类型")
    download_url: Optional[str] = Field(None, description="下载 URL")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    created_by: Optional[ConfluenceUser] = Field(None, description="创建者")


class ConfluenceVersion(BaseModel):
    """Confluence 版本模型"""
    number: int = Field(..., description="版本号")
    message: Optional[str] = Field(None, description="版本说明")
    minor_edit: bool = Field(default=False, description="是否为小版本编辑")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[ConfluenceUser] = Field(None, description="创建者")


class ConfluencePage(BaseModel):
    """
    Confluence 页面完整模型
    包含所有核心字段和关联数据
    """
    id: str = Field(..., description="页面 ID")
    title: str = Field(..., description="页面标题")
    type: str = Field(..., description="内容类型（page, blogpost, comment）")
    status: str = Field(..., description="状态（current, trashed, historical）")

    # 空间信息
    space: ConfluenceSpace = Field(..., description="所属空间")

    # 内容
    body_storage: Optional[str] = Field(None, description="存储格式内容（HTML）")
    body_view: Optional[str] = Field(None, description="视图格式内容")
    body_export_view: Optional[str] = Field(None, description="导出视图内容")
    plain_text: Optional[str] = Field(None, description="纯文本内容（解析后）")

    # 版本信息
    version: Optional[ConfluenceVersion] = Field(None, description="当前版本")

    # 层级关系
    parent_id: Optional[str] = Field(None, description="父页面 ID")
    ancestor_ids: List[str] = Field(default_factory=list, description="祖先页面 ID 列表")

    # 时间信息
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    # 作者信息
    created_by: Optional[ConfluenceUser] = Field(None, description="创建者")
    last_modified_by: Optional[ConfluenceUser] = Field(None, description="最后修改者")

    # 标签和附件
    labels: List[ConfluenceLabel] = Field(default_factory=list, description="标签列表")
    attachments: List[ConfluenceAttachment] = Field(default_factory=list, description="附件列表")

    # Web URL
    url: Optional[str] = Field(None, description="页面的 Web 访问 URL")

    # 原始数据
    raw_data: Optional[Dict[str, Any]] = Field(None, description="完整的原始 JSON 数据")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConfluencePagePage(BaseModel):
    """
    Confluence 页面分页查询结果
    """
    pages: List[ConfluencePage] = Field(default_factory=list, description="页面列表")
    total: int = Field(..., description="总数量")
    start: int = Field(..., description="起始位置")
    limit: int = Field(..., description="每页数量")
    size: int = Field(..., description="当前页实际数量")
    is_last: bool = Field(..., description="是否是最后一页")


class ConfluenceHealthStatus(BaseModel):
    """
    Confluence 服务健康状态
    """
    is_connected: bool = Field(..., description="是否连接成功")
    server_info: Optional[Dict[str, Any]] = Field(None, description="服务器信息")
    accessible_spaces: List[str] = Field(default_factory=list, description="可访问的空间列表")
    error_message: Optional[str] = Field(None, description="错误信息")
    checked_at: datetime = Field(default_factory=datetime.now, description="检查时间")

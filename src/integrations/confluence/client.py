"""
Confluence API Client
Confluence API 客户端实现，支持页面查询、空间管理、健康检查等功能
"""

import logging
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from html import unescape
from html.parser import HTMLParser

from atlassian import Confluence
from requests.exceptions import HTTPError, ConnectionError as RequestsConnectionError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from src.config import settings
from src.integrations.confluence.models import (
    ConfluencePage,
    ConfluencePagePage,
    ConfluenceUser,
    ConfluenceSpace,
    ConfluenceLabel,
    ConfluenceAttachment,
    ConfluenceVersion,
    ConfluenceHealthStatus
)
from src.integrations.confluence.exceptions import (
    ConfluenceAuthenticationError,
    ConfluenceConnectionError,
    ConfluenceAPIError,
    ConfluenceResourceNotFoundError,
    ConfluenceRateLimitError
)

logger = logging.getLogger(__name__)


class HTMLTextExtractor(HTMLParser):
    """HTML 文本提取器，将 HTML 转换为纯文本"""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.ignore_tags = {'script', 'style', 'meta', 'link'}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        # 为某些标签添加空格或换行
        if tag in {'p', 'div', 'br', 'tr'}:
            self.text_parts.append('\n')
        elif tag in {'td', 'th'}:
            self.text_parts.append(' ')

    def handle_endtag(self, tag):
        self.current_tag = None
        if tag in {'p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            self.text_parts.append('\n')

    def handle_data(self, data):
        if self.current_tag not in self.ignore_tags:
            text = data.strip()
            if text:
                self.text_parts.append(text)

    def get_text(self) -> str:
        """获取提取的纯文本"""
        text = ' '.join(self.text_parts)
        # 清理多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s+', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


class ConfluenceClient:
    """
    Confluence API 客户端
    提供 Confluence 数据访问的统一接口

    Features:
    - 页面查询和分页
    - 空间管理
    - CQL 查询支持
    - HTML 内容解析
    - 健康检查
    - 自动重试和错误处理
    """

    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = None,
        api_token: Optional[str] = None,
        timeout: Optional[int] = None,
        cloud: bool = True
    ):
        """
        初始化 Confluence 客户端

        Args:
            url: Confluence 实例 URL（默认从配置读取）
            username: 账号邮箱（Cloud）或用户名（Server）（默认从配置读取）
            api_token: API Token（默认从配置读取）
            timeout: 请求超时时间（秒）
            cloud: 是否为 Cloud 版本（默认 True）
        """
        self.url = url or settings.confluence_url
        self.username = username or settings.confluence_email
        self.api_token = api_token or settings.confluence_api_token
        self.timeout = timeout if timeout is not None else settings.confluence_timeout
        self.cloud = cloud

        # 验证必需配置
        if not self.url or not self.username or not self.api_token:
            raise ValueError(
                "Confluence 配置不完整，请设置 CONFLUENCE_URL, CONFLUENCE_EMAIL, "
                "CONFLUENCE_API_TOKEN 环境变量"
            )

        self._client: Optional[Confluence] = None
        self._is_connected = False

    @property
    def client(self) -> Confluence:
        """获取 Confluence 客户端实例（懒加载）"""
        if self._client is None:
            self._connect()
        return self._client

    def _connect(self) -> None:
        """建立 Confluence 连接"""
        try:
            logger.info(f"正在连接 Confluence: {self.url}")
            self._client = Confluence(
                url=self.url,
                username=self.username,
                password=self.api_token,
                timeout=self.timeout,
                cloud=self.cloud
            )
            # 测试连接
            self._client.get_all_spaces(limit=1)
            self._is_connected = True
            logger.info("Confluence 连接成功")
        except HTTPError as e:
            if e.response.status_code == 401:
                raise ConfluenceAuthenticationError(f"Confluence 认证失败: {e}")
            elif e.response.status_code == 403:
                raise ConfluenceAuthenticationError(f"Confluence 权限不足: {e}")
            else:
                raise ConfluenceConnectionError(f"Confluence 连接失败: {e}")
        except RequestsConnectionError as e:
            raise ConfluenceConnectionError(f"Confluence 网络连接失败: {e}")
        except Exception as e:
            raise ConfluenceConnectionError(f"Confluence 连接异常: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConfluenceAPIError, ConfluenceConnectionError))
    )
    async def health_check(self) -> ConfluenceHealthStatus:
        """
        健康检查

        Returns:
            ConfluenceHealthStatus: 健康状态信息
        """
        try:
            # 获取服务器信息
            try:
                # Cloud 版本可能不支持此 API
                server_info = {}
            except:
                server_info = {}

            # 获取可访问的空间列表（最多 10 个）
            spaces_result = self.client.get_all_spaces(limit=10)
            space_keys = []
            if 'results' in spaces_result:
                space_keys = [s['key'] for s in spaces_result['results']]

            return ConfluenceHealthStatus(
                is_connected=True,
                server_info=server_info,
                accessible_spaces=space_keys,
                error_message=None,
                checked_at=datetime.now()
            )
        except HTTPError as e:
            return ConfluenceHealthStatus(
                is_connected=False,
                server_info=None,
                accessible_spaces=[],
                error_message=f"Confluence API 错误: {e}",
                checked_at=datetime.now()
            )
        except Exception as e:
            return ConfluenceHealthStatus(
                is_connected=False,
                server_info=None,
                accessible_spaces=[],
                error_message=f"健康检查失败: {str(e)}",
                checked_at=datetime.now()
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ConfluenceAPIError)
    )
    def fetch_pages(
        self,
        space_key: Optional[str] = None,
        cql: Optional[str] = None,
        start: int = 0,
        limit: int = 25,
        expand: Optional[List[str]] = None
    ) -> ConfluencePagePage:
        """
        查询页面列表（支持分页）

        Args:
            space_key: 空间 KEY（可选，默认查询所有空间）
            cql: 自定义 CQL 查询语句（可选）
            start: 起始位置（分页）
            limit: 每页数量
            expand: 需要扩展的字段（如 body.storage, version, space）

        Returns:
            ConfluencePagePage: 分页查询结果
        """
        try:
            expand_fields = expand or ["body.storage", "version", "space", "history", "metadata.labels"]

            if cql:
                # 使用 CQL 查询
                logger.info(f"执行 CQL 查询: {cql}, start={start}, limit={limit}")
                result = self.client.cql(
                    cql=cql,
                    start=start,
                    limit=limit,
                    expand=",".join(expand_fields)
                )
            elif space_key:
                # 查询指定空间的页面
                logger.info(f"查询空间 {space_key} 的页面, start={start}, limit={limit}")
                result = self.client.get_all_pages_from_space(
                    space=space_key,
                    start=start,
                    limit=limit,
                    expand=",".join(expand_fields)
                )
            else:
                # 查询所有页面
                default_space = settings.confluence_space_key
                if default_space:
                    logger.info(f"查询默认空间 {default_space} 的页面")
                    result = self.client.get_all_pages_from_space(
                        space=default_space,
                        start=start,
                        limit=limit,
                        expand=",".join(expand_fields)
                    )
                else:
                    # 如果没有指定空间，使用 CQL 查询所有页面
                    logger.info("查询所有页面")
                    result = self.client.cql(
                        cql="type=page order by lastmodified desc",
                        start=start,
                        limit=limit,
                        expand=",".join(expand_fields)
                    )

            # 解析结果
            pages = []
            results = result.get('results', [])

            for page_data in results:
                try:
                    parsed = self._parse_page(page_data)
                    pages.append(parsed)
                except Exception as e:
                    page_id = page_data.get('id', 'UNKNOWN')
                    logger.warning(f"解析页面 {page_id} 失败: {e}")
                    continue

            total = result.get('totalSize', result.get('size', len(pages)))
            current_size = len(pages)

            return ConfluencePagePage(
                pages=pages,
                total=total,
                start=start,
                limit=limit,
                size=current_size,
                is_last=start + current_size >= total
            )

        except HTTPError as e:
            if e.response.status_code == 404:
                raise ConfluenceResourceNotFoundError(f"空间不存在: {space_key}")
            elif e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                raise ConfluenceRateLimitError(
                    f"API 限流，请 {retry_after} 秒后重试",
                    retry_after
                )
            else:
                raise ConfluenceAPIError(f"查询页面失败: {e}", e.response.status_code)
        except Exception as e:
            raise ConfluenceAPIError(f"查询页面异常: {str(e)}")

    def fetch_page_by_id(
        self,
        page_id: str,
        expand: Optional[List[str]] = None
    ) -> ConfluencePage:
        """
        根据 ID 查询单个页面

        Args:
            page_id: 页面 ID
            expand: 需要扩展的字段

        Returns:
            ConfluencePage: 页面详细信息
        """
        try:
            expand_fields = expand or [
                "body.storage",
                "body.view",
                "version",
                "space",
                "history",
                "metadata.labels",
                "children.attachment"
            ]

            page_data = self.client.get_page_by_id(
                page_id=page_id,
                expand=",".join(expand_fields)
            )
            return self._parse_page(page_data)
        except HTTPError as e:
            if e.response.status_code == 404:
                raise ConfluenceResourceNotFoundError(f"页面不存在: {page_id}")
            else:
                raise ConfluenceAPIError(f"查询页面失败: {e}", e.response.status_code)
        except Exception as e:
            raise ConfluenceAPIError(f"查询页面异常: {str(e)}")

    def fetch_page_by_title(
        self,
        space_key: str,
        title: str,
        expand: Optional[List[str]] = None
    ) -> Optional[ConfluencePage]:
        """
        根据标题查询页面

        Args:
            space_key: 空间 KEY
            title: 页面标题
            expand: 需要扩展的字段

        Returns:
            ConfluencePage: 页面详细信息，如果不存在返回 None
        """
        try:
            expand_fields = expand or ["body.storage", "version", "space", "history"]

            page_data = self.client.get_page_by_title(
                space=space_key,
                title=title,
                expand=",".join(expand_fields)
            )

            if page_data:
                return self._parse_page(page_data)
            return None
        except HTTPError as e:
            if e.response.status_code == 404:
                return None
            else:
                raise ConfluenceAPIError(f"查询页面失败: {e}", e.response.status_code)

    def get_all_spaces(self, limit: int = 100) -> List[ConfluenceSpace]:
        """
        获取所有可访问的空间

        Args:
            limit: 返回数量限制

        Returns:
            List[ConfluenceSpace]: 空间列表
        """
        try:
            result = self.client.get_all_spaces(limit=limit)
            spaces = []

            for space_data in result.get('results', []):
                try:
                    space = self._parse_space(space_data)
                    spaces.append(space)
                except Exception as e:
                    space_key = space_data.get('key', 'UNKNOWN')
                    logger.warning(f"解析空间 {space_key} 失败: {e}")
                    continue

            return spaces
        except HTTPError as e:
            raise ConfluenceAPIError(f"获取空间列表失败: {e}", e.response.status_code)

    def _parse_page(self, page_data: Dict[str, Any]) -> ConfluencePage:
        """
        解析 Confluence 页面原始数据为结构化模型

        Args:
            page_data: Confluence API 返回的原始页面数据

        Returns:
            ConfluencePage: 解析后的页面模型
        """
        # 基础字段
        parsed = {
            "id": page_data['id'],
            "title": page_data['title'],
            "type": page_data['type'],
            "status": page_data.get('status', 'current')
        }

        # 解析空间
        space_data = page_data.get('space', {})
        if space_data:
            parsed["space"] = self._parse_space(space_data)
        else:
            # 如果没有空间数据，创建一个默认空间
            parsed["space"] = ConfluenceSpace(
                id="unknown",
                key="unknown",
                name="Unknown",
                type="global"
            )

        # 解析内容
        body = page_data.get('body', {})
        if 'storage' in body:
            storage_content = body['storage'].get('value', '')
            parsed["body_storage"] = storage_content
            # 转换为纯文本
            parsed["plain_text"] = self._html_to_plain_text(storage_content)

        if 'view' in body:
            parsed["body_view"] = body['view'].get('value', '')

        if 'export_view' in body:
            parsed["body_export_view"] = body['export_view'].get('value', '')

        # 解析版本
        version_data = page_data.get('version', {})
        if version_data:
            parsed["version"] = self._parse_version(version_data)

        # 解析层级关系
        ancestors = page_data.get('ancestors', [])
        if ancestors:
            parsed["parent_id"] = ancestors[-1]['id'] if ancestors else None
            parsed["ancestor_ids"] = [a['id'] for a in ancestors]

        # 解析时间
        history = page_data.get('history', {})
        created_date = history.get('createdDate') or page_data.get('history', {}).get('createdDate')
        if created_date:
            parsed["created_at"] = self._parse_datetime(created_date)
        else:
            parsed["created_at"] = datetime.now()

        # 更新时间从 version 获取
        if version_data and 'when' in version_data:
            parsed["updated_at"] = self._parse_datetime(version_data['when'])
        else:
            parsed["updated_at"] = parsed["created_at"]

        # 解析作者
        created_by = history.get('createdBy')
        if created_by:
            parsed["created_by"] = self._parse_user(created_by)

        if version_data and 'by' in version_data:
            parsed["last_modified_by"] = self._parse_user(version_data['by'])

        # 解析标签
        metadata = page_data.get('metadata', {})
        labels_data = metadata.get('labels', {}).get('results', [])
        parsed["labels"] = [self._parse_label(l) for l in labels_data]

        # 解析附件
        children = page_data.get('children', {})
        attachments_data = children.get('attachment', {}).get('results', [])
        parsed["attachments"] = [self._parse_attachment(a) for a in attachments_data]

        # Web URL
        links = page_data.get('_links', {})
        if 'webui' in links:
            parsed["url"] = self.url + links['webui']
        elif 'base' in links:
            parsed["url"] = links['base'] + links.get('webui', '')

        # 保存原始数据
        parsed["raw_data"] = page_data

        return ConfluencePage(**parsed)

    def _parse_space(self, space_data: Dict[str, Any]) -> ConfluenceSpace:
        """解析空间信息"""
        links = space_data.get('_links', {})
        url = None
        if 'webui' in links:
            url = self.url + links['webui']

        return ConfluenceSpace(
            id=space_data['id'],
            key=space_data['key'],
            name=space_data['name'],
            description=space_data.get('description', {}).get('plain', {}).get('value'),
            type=space_data.get('type', 'global'),
            status=space_data.get('status'),
            homepage_id=space_data.get('homepage', {}).get('id'),
            url=url
        )

    def _parse_user(self, user_data: Dict[str, Any]) -> ConfluenceUser:
        """解析用户信息"""
        return ConfluenceUser(
            account_id=user_data.get('accountId'),
            username=user_data.get('username') or user_data.get('userKey'),
            display_name=user_data.get('displayName', 'Unknown'),
            email=user_data.get('email'),
            avatar_url=user_data.get('profilePicture', {}).get('path')
        )

    def _parse_version(self, version_data: Dict[str, Any]) -> ConfluenceVersion:
        """解析版本信息"""
        created_by = None
        if 'by' in version_data:
            created_by = self._parse_user(version_data['by'])

        return ConfluenceVersion(
            number=version_data['number'],
            message=version_data.get('message'),
            minor_edit=version_data.get('minorEdit', False),
            created_at=self._parse_datetime(version_data['when']),
            created_by=created_by
        )

    def _parse_label(self, label_data: Dict[str, Any]) -> ConfluenceLabel:
        """解析标签信息"""
        return ConfluenceLabel(
            id=label_data.get('id'),
            name=label_data.get('name', ''),
            prefix=label_data.get('prefix')
        )

    def _parse_attachment(self, attachment_data: Dict[str, Any]) -> ConfluenceAttachment:
        """解析附件信息"""
        metadata = attachment_data.get('metadata', {})
        extensions = attachment_data.get('extensions', {})

        created_by = None
        history = attachment_data.get('history', {})
        if 'createdBy' in history:
            created_by = self._parse_user(history['createdBy'])

        download_url = None
        links = attachment_data.get('_links', {})
        if 'download' in links:
            download_url = self.url + links['download']

        return ConfluenceAttachment(
            id=attachment_data['id'],
            title=attachment_data['title'],
            filename=attachment_data.get('title'),
            file_size=extensions.get('fileSize'),
            media_type=extensions.get('mediaType'),
            download_url=download_url,
            created_at=self._parse_datetime(history.get('createdDate')) if history.get('createdDate') else None,
            created_by=created_by
        )

    @staticmethod
    def _html_to_plain_text(html: str) -> str:
        """
        将 HTML 转换为纯文本

        Args:
            html: HTML 内容

        Returns:
            str: 纯文本内容
        """
        if not html:
            return ""

        try:
            # 解码 HTML 实体
            html = unescape(html)

            # 使用自定义解析器提取文本
            extractor = HTMLTextExtractor()
            extractor.feed(html)
            text = extractor.get_text()

            return text
        except Exception as e:
            logger.warning(f"HTML 转文本失败: {e}")
            # 如果解析失败，使用正则表达式简单清理
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

    @staticmethod
    def _parse_datetime(date_str: str) -> datetime:
        """
        解析 Confluence 日期字符串

        Confluence 日期格式: '2024-01-01T12:00:00.000Z' 或 '2024-01-01T12:00:00.000+08:00'
        """
        try:
            # 移除毫秒部分
            if '.' in date_str:
                date_str = date_str.split('.')[0]
            # 移除时区信息
            date_str = date_str.replace('Z', '').split('+')[0].split('-')[0]
            return datetime.fromisoformat(date_str)
        except Exception as e:
            logger.warning(f"日期解析失败: {date_str}, 错误: {e}")
            return datetime.now()

    def close(self) -> None:
        """关闭 Confluence 连接"""
        if self._client:
            self._client = None
            self._is_connected = False
            logger.info("Confluence 连接已关闭")

    def __enter__(self):
        """上下文管理器：进入"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器：退出"""
        self.close()


# 全局单例实例（可选）
_global_confluence_client: Optional[ConfluenceClient] = None


def get_confluence_client() -> ConfluenceClient:
    """
    获取全局 Confluence 客户端单例

    Returns:
        ConfluenceClient: Confluence 客户端实例
    """
    global _global_confluence_client
    if _global_confluence_client is None:
        _global_confluence_client = ConfluenceClient()
    return _global_confluence_client

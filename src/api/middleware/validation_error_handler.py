"""
FastAPI 验证错误处理中间件
"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    处理 Pydantic 验证错误，记录详细信息
    """
    logger.error(f"=== Validation Error ===")
    logger.error(f"URL: {request.url}")
    logger.error(f"Method: {request.method}")
    
    try:
        body = await request.body()
        logger.error(f"Request Body: {body.decode('utf-8')}")
    except:
        pass
    
    logger.error(f"Validation Errors:")
    for error in exc.errors():
        logger.error(f"  - Field: {error['loc']}")
        logger.error(f"    Error: {error['msg']}")
        logger.error(f"    Type: {error['type']}")
        if 'input' in error:
            logger.error(f"    Input: {error['input']}")
    
    logger.error(f"========================")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )

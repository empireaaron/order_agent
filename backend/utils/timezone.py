"""
时区工具模块
统一使用北京时间 (Asia/Shanghai)
"""
from datetime import datetime, timezone, timedelta

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def now() -> datetime:
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)


def now_utc() -> datetime:
    """获取当前UTC时间（用于兼容性）"""
    return datetime.now(timezone.utc)


def to_beijing(dt: datetime) -> datetime:
    """将任意时区时间转换为北京时间"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # 如果dt没有时区信息，假设它是UTC时间
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BEIJING_TZ)


def format_beijing(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化北京时间为字符串"""
    if dt is None:
        return ""
    beijing_dt = to_beijing(dt)
    return beijing_dt.strftime(fmt)
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings,SettingsConfigDict
from datetime import timedelta

class Settings(BaseSettings):
    """全局配置。

    可以通过环境变量或 .env 文件覆盖默认值。
    """
    # --- 1. 基础信息 ---
    PROJECT_NAME: str = "SQL Edu Backend"
    DEBUG: bool = True  # 开发模式默认为 True
    API_V1_STR: str = "/api/v1"

    # --- 2. 数据库连接 ---
    # 你的数据库连接字符串
    DB_URL: str

    # --- 3. 安全与认证 (JWT) ---
    # 在终端运行 `openssl rand -hex 32` 可以生成一个安全的随机字符串，需在 .env 中设置
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # Token 过期时间，这里设为 7 天

    # --- 4. CORS 跨域配置 ---
    # 允许访问后端的来源列表，注意这里是 List[str]
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",  # React/Next.js 默认端口
        "http://localhost:5173",  # Vite/Vue 默认端口
        "http://127.0.0.1:5173"
    ]
       # --- 5. AI 大模型配置 ---
    AI_API_KEY: str = ""
    AI_BASE_URL: str = ""
    AI_MODEL_NAME: str = "gpt-3.5-turbo" # 或者是 deepseek-chat 等
    AI_TEMPERATURE: float = 0.7

    # --- 6. 邮件服务器配置 (Outlook) ---
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 465             # Gmail 推荐 465
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "SQL-Edu System"

    # Gmail 465 端口的加密组合：
    MAIL_STARTTLS: bool = False      # 关闭 STARTTLS
    MAIL_SSL_TLS: bool = True        # 开启 SSL/TLS
    
    MAIL_USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    #7.配置JWT密钥和时间 (Settings) - 必须通过 .env 设置，勿写死在代码中
    JWT_SECRET_KEY: str = ""  # 请在 .env 中设置，例如：openssl rand -hex 32 

    # Token 过期时间
    JWT_ACCESS_TOKEN_EXPIRES : timedelta = timedelta(minutes=60)      # Access Token 1小时过期
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=7)         # Refresh Token 7天过期
    # --- 8. 配置加载项 (Pydantic V2 新写法) ---
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore" # 忽略 .env 中多余的字段
    )

# 实例化对象    
settings = Settings()

@lru_cache
def get_settings() -> Settings:
    """获取单例 Settings 实例。"""

    return Settings()


__all__ = ["Settings", "get_settings"]







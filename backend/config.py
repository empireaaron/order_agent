"""
环境配置管理
支持从环境变量或 .env 文件读取配置
"""
import os

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 加载 .env 文件
load_dotenv()


class Settings(BaseSettings):
    """应用配置"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    # Application
    APP_NAME: str = "TicketBot - 智能客服工单系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    API_V1_PREFIX: str = "/api/v1"

    # MySQL 数据库
    MYSQL_HOST: str = Field(default="localhost")
    MYSQL_PORT: int = Field(default=3306)
    MYSQL_USER: str = Field(default="root")
    MYSQL_PASSWORD: str = Field(default="")
    MYSQL_DATABASE: str = Field(default="ticket_bot")

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"

    # Milvus 向量数据库
    MILVUS_HOST: str = Field(default="localhost")
    MILVUS_PORT: int = Field(default=19530)
    MILVUS_DB_NAME: str = Field(default="default")

    # LLM 配置 (支持多种 LLM)
    # OpenAI
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_BASE_URL: str = Field(default="https://api.openai.com/v1")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")

    # Embedding 模型配置
    EMBEDDING_MODEL: str = Field(default="text-embedding-v2")  # DashScope: text-embedding-v2, OpenAI: text-embedding-3-small

    # Anthropic Claude
    ANTHROPIC_API_KEY: str = Field(default="")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-latest")

    # Groq
    GROQ_API_KEY: str = Field(default="")
    GROQ_MODEL: str = Field(default="llama3-70b-8192")

    # Ollama (本地)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="llama3")

    # LangChain 配置
    LANGCHAIN_TRACING_V2: bool = Field(default=False)
    LANGCHAIN_PROJECT: str = Field(default="ticket-bot")

    # JWT 配置
    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production-use-env")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # WebSocket 配置
    WS_HEARTBEAT_INTERVAL: int = Field(default=30)  # 秒

    # 文档处理
    CHUNK_SIZE: int = Field(default=500)
    CHUNK_OVERLAP: int = Field(default=50)

    # MinIO 配置
    MINIO_ENDPOINT: str = Field(default="localhost:9000")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin")
    MINIO_SECRET_KEY: str = Field(default="minioadmin")
    MINIO_BUCKET: str = Field(default="documents")
    MINIO_SECURE: bool = Field(default=False)

    @property
    def llm(self):
        """获取 LLM 实例"""
        from langchain_openai import ChatOpenAI

        if self.OPENAI_API_KEY:
            return ChatOpenAI(
                model=self.OPENAI_MODEL,
                api_key=self.OPENAI_API_KEY,
                base_url=self.OPENAI_BASE_URL if self.OPENAI_BASE_URL else None,
                temperature=0.7
            )
        else:
            # 如果没有配置 API Key，返回 None 或抛出异常
            raise ValueError("OPENAI_API_KEY not configured. Please set it in .env file.")


# 全局配置实例
settings = Settings()
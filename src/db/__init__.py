"""
Módulo de conexión a bases de datos para SentimentInsightUAM_SA.

Este módulo gestiona las conexiones asíncronas a PostgreSQL y MongoDB,
utilizando las mismas bases de datos del proyecto principal de scraping.

Autor: SentimentInsightUAM Team
Fecha: 2025-11-09
"""

import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN POSTGRESQL
# ============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://sentiment_admin:dev_password_2024@localhost:5432/sentiment_uam_db"
)

# Engine asíncrono de SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session maker asíncrono
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager para sesiones de PostgreSQL.
    
    Uso:
        async with get_db_session() as session:
            result = await session.execute(query)
    
    Yields:
        AsyncSession: Sesión de SQLAlchemy activa
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Error en sesión de PostgreSQL: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Inicializa la conexión a PostgreSQL.
    Verifica que la base de datos esté accesible.
    """
    try:
        async with engine.begin() as conn:
            logger.info("✓ Conexión a PostgreSQL establecida correctamente")
    except Exception as e:
        logger.error(f"✗ Error al conectar con PostgreSQL: {e}")
        raise


async def close_db() -> None:
    """
    Cierra las conexiones a PostgreSQL de manera limpia.
    """
    await engine.dispose()
    logger.info("✓ Conexiones a PostgreSQL cerradas")


# ============================================================================
# CONFIGURACIÓN MONGODB
# ============================================================================

MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://sentiment_admin:dev_password_2024@localhost:27017/sentiment_uam_nlp?authSource=sentiment_uam_nlp"
)

MONGO_DB_NAME = os.getenv("MONGO_DB", "sentiment_uam_nlp")

# Cliente MongoDB (singleton)
_mongo_client: AsyncIOMotorClient = None


def get_mongo_client() -> AsyncIOMotorClient:
    """
    Obtiene el cliente MongoDB (patrón singleton).
    
    Returns:
        AsyncIOMotorClient: Cliente MongoDB configurado
    """
    global _mongo_client
    
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(
            MONGO_URL,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=50,
        )
        logger.info("✓ Cliente MongoDB inicializado")
    
    return _mongo_client


def get_mongo_db():
    """
    Obtiene la base de datos MongoDB.
    
    Returns:
        Database: Instancia de la base de datos MongoDB
    """
    client = get_mongo_client()
    return client[MONGO_DB_NAME]


async def init_mongo() -> None:
    """
    Verifica la conexión a MongoDB.
    """
    try:
        client = get_mongo_client()
        await client.admin.command('ping')
        logger.info(f"✓ Conexión a MongoDB establecida correctamente (DB: {MONGO_DB_NAME})")
    except ConnectionFailure as e:
        logger.error(f"✗ Error al conectar con MongoDB: {e}")
        raise


async def close_mongo() -> None:
    """
    Cierra la conexión a MongoDB de manera limpia.
    """
    global _mongo_client
    
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        logger.info("✓ Conexión a MongoDB cerrada")


# ============================================================================
# INICIALIZACIÓN Y CIERRE COMPLETO
# ============================================================================

async def init_all_databases() -> None:
    """
    Inicializa conexiones a ambas bases de datos.
    Llama a esta función al inicio de la aplicación.
    """
    logger.info("Inicializando conexiones a bases de datos...")
    await init_db()
    await init_mongo()
    logger.info("✓ Todas las bases de datos conectadas")


async def close_all_databases() -> None:
    """
    Cierra todas las conexiones a bases de datos.
    Llama a esta función al finalizar la aplicación.
    """
    logger.info("Cerrando conexiones a bases de datos...")
    await close_db()
    await close_mongo()
    logger.info("✓ Todas las bases de datos desconectadas")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "get_db_session",
    "get_mongo_client",
    "get_mongo_db",
    "init_all_databases",
    "close_all_databases",
    "init_db",
    "close_db",
    "init_mongo",
    "close_mongo",
]

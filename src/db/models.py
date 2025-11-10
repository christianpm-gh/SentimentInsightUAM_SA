"""
Modelos ORM de SQLAlchemy para SentimentInsightUAM_SA.

Define solo los modelos necesarios para LEER datos de PostgreSQL
y ACTUALIZAR campos de análisis. No incluye modelos de scraping.

Autor: SentimentInsightUAM Team
Fecha: 2025-11-09
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Integer, DECIMAL, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarativa para modelos ORM"""
    pass


# ============================================================================
# MODELOS PRINCIPALES (Solo lectura)
# ============================================================================

class Profesor(Base):
    """
    Modelo de profesor (lectura).
    Tabla fuente de profesores del scraper.
    """
    __tablename__ = "profesores"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_limpio: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    url_directorio_uam: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_misprofesores: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    departamento: Mapped[str] = mapped_column(String(100), default="Sistemas")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    perfiles: Mapped[List["Perfil"]] = relationship("Perfil", back_populates="profesor")
    resenias: Mapped[List["ReseniaMetadata"]] = relationship("ReseniaMetadata", back_populates="profesor")


class Perfil(Base):
    """
    Modelo de perfil de profesor (lectura).
    Snapshot temporal de métricas.
    """
    __tablename__ = "perfiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profesor_id: Mapped[int] = mapped_column(Integer, ForeignKey("profesores.id", ondelete="CASCADE"), nullable=False)
    calidad_general: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 2), nullable=True)
    dificultad: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 2), nullable=True)
    porcentaje_recomendacion: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2), nullable=True)
    total_resenias_encontradas: Mapped[int] = mapped_column(Integer, default=0)
    scraping_exitoso: Mapped[bool] = mapped_column(Boolean, default=True)
    fuente: Mapped[str] = mapped_column(String(50), default="misprofesores.com")
    fecha_extraccion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    profesor: Mapped["Profesor"] = relationship("Profesor", back_populates="perfiles")


class Curso(Base):
    """
    Modelo de curso (lectura).
    Catálogo de materias impartidas.
    """
    __tablename__ = "cursos"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_normalizado: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    codigo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    departamento: Mapped[str] = mapped_column(String(100), default="Sistemas")
    nivel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    total_resenias: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    resenias: Mapped[List["ReseniaMetadata"]] = relationship("ReseniaMetadata", back_populates="curso")


class ReseniaMetadata(Base):
    """
    Modelo de metadata de reseña (lectura).
    Contiene datos estructurados de la reseña.
    """
    __tablename__ = "resenias_metadata"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profesor_id: Mapped[int] = mapped_column(Integer, ForeignKey("profesores.id", ondelete="CASCADE"), nullable=False)
    curso_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("cursos.id", ondelete="SET NULL"), nullable=True)
    perfil_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("perfiles.id", ondelete="SET NULL"), nullable=True)
    fecha_resenia: Mapped[date] = mapped_column(Date, nullable=False)
    calidad_general: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 2), nullable=True)
    facilidad: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 2), nullable=True)
    asistencia: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    calificacion_recibida: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    nivel_interes: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mongo_opinion_id: Mapped[Optional[str]] = mapped_column(String(24), unique=True, nullable=True)
    tiene_comentario: Mapped[bool] = mapped_column(Boolean, default=False)
    longitud_comentario: Mapped[int] = mapped_column(Integer, default=0)
    fecha_extraccion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fuente: Mapped[str] = mapped_column(String(50), default="misprofesores.com")
    
    # Relaciones
    profesor: Mapped["Profesor"] = relationship("Profesor", back_populates="resenias")
    curso: Mapped[Optional["Curso"]] = relationship("Curso", back_populates="resenias")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "Base",
    "Profesor",
    "Perfil",
    "Curso",
    "ReseniaMetadata",
]

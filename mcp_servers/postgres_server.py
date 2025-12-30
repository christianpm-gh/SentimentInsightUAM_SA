#!/usr/bin/env python3
"""
MCP Server para PostgreSQL - SentimentInsightUAM_SA

Servidor MCP que proporciona acceso a la base de datos relacional PostgreSQL
con herramientas para consultar profesores, cursos, perfiles y reseñas.

Autor: SentimentInsightUAM Team
Fecha: 2025-12-03
"""

import os
import sys
import json
import asyncio
from typing import Any, Optional
from datetime import datetime, date

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

import asyncpg

# Cargar variables de entorno
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Configuración de conexión
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "sentiment_uam_db"),
    "user": os.getenv("POSTGRES_USER", "sentiment_admin"),
    "password": os.getenv("POSTGRES_PASSWORD", "dev_password_2024"),
}

# Pool de conexiones global
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Obtiene o crea el pool de conexiones."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(**POSTGRES_CONFIG, min_size=2, max_size=10)
    return _pool


def serialize_value(value: Any) -> Any:
    """Serializa valores para JSON."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value


def serialize_row(row: asyncpg.Record) -> dict:
    """Convierte un registro asyncpg a diccionario serializable."""
    return {k: serialize_value(v) for k, v in dict(row).items()}


# Crear servidor MCP
server = Server("sentiment-postgres")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Lista las herramientas disponibles."""
    return [
        Tool(
            name="pg_query",
            description="Ejecuta una consulta SQL SELECT en PostgreSQL. Solo lectura.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Consulta SQL SELECT a ejecutar"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Límite de resultados (default: 100)",
                        "default": 100
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="pg_listar_profesores",
            description="Lista profesores con filtros opcionales por departamento o nombre.",
            inputSchema={
                "type": "object",
                "properties": {
                    "departamento": {
                        "type": "string",
                        "description": "Filtrar por departamento (ej: 'Sistemas')"
                    },
                    "nombre": {
                        "type": "string",
                        "description": "Buscar por nombre (búsqueda parcial)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Límite de resultados (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="pg_detalle_profesor",
            description="Obtiene información detallada de un profesor por ID o nombre.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "ID del profesor"
                    },
                    "nombre": {
                        "type": "string",
                        "description": "Nombre del profesor (búsqueda parcial)"
                    }
                }
            }
        ),
        Tool(
            name="pg_listar_cursos",
            description="Lista cursos/materias disponibles.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nombre": {
                        "type": "string",
                        "description": "Buscar por nombre (búsqueda parcial)"
                    },
                    "departamento": {
                        "type": "string",
                        "description": "Filtrar por departamento"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Límite de resultados (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="pg_resenias_profesor",
            description="Obtiene las reseñas (metadata) de un profesor específico.",
            inputSchema={
                "type": "object",
                "properties": {
                    "profesor_id": {
                        "type": "integer",
                        "description": "ID del profesor"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Límite de resultados (default: 50)",
                        "default": 50
                    }
                },
                "required": ["profesor_id"]
            }
        ),
        Tool(
            name="pg_estadisticas",
            description="Obtiene estadísticas generales de la base de datos.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="pg_perfil_profesor",
            description="Obtiene el perfil más reciente de un profesor (calificaciones).",
            inputSchema={
                "type": "object",
                "properties": {
                    "profesor_id": {
                        "type": "integer",
                        "description": "ID del profesor"
                    }
                },
                "required": ["profesor_id"]
            }
        ),
        Tool(
            name="pg_schema",
            description="Muestra el esquema de las tablas de la base de datos.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tabla": {
                        "type": "string",
                        "description": "Nombre de tabla específica (opcional)"
                    }
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Ejecuta una herramienta."""
    pool = await get_pool()
    
    try:
        if name == "pg_query":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 100)
            
            # Validar que sea SELECT
            if not query.strip().upper().startswith("SELECT"):
                return [TextContent(
                    type="text",
                    text="❌ Error: Solo se permiten consultas SELECT"
                )]
            
            # Agregar LIMIT si no existe
            if "LIMIT" not in query.upper():
                query = f"{query} LIMIT {limit}"
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(query)
                result = [serialize_row(row) for row in rows]
            
            return [TextContent(
                type="text",
                text=f"✅ {len(result)} resultados:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
            )]
        
        elif name == "pg_listar_profesores":
            departamento = arguments.get("departamento")
            nombre = arguments.get("nombre")
            limit = arguments.get("limit", 50)
            
            query = """
                SELECT id, nombre_completo, nombre_limpio, departamento, slug, activo
                FROM profesores
                WHERE activo = true
            """
            params = []
            
            if departamento:
                query += f" AND departamento = ${len(params) + 1}"
                params.append(departamento)
            
            if nombre:
                query += f" AND nombre_completo ILIKE ${len(params) + 1}"
                params.append(f"%{nombre}%")
            
            query += f" ORDER BY nombre_limpio LIMIT ${len(params) + 1}"
            params.append(limit)
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                result = [serialize_row(row) for row in rows]
            
            output = f"📚 **{len(result)} profesores encontrados**\n\n"
            for p in result:
                output += f"- **[{p['id']}]** {p['nombre_limpio']} ({p['departamento']})\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "pg_detalle_profesor":
            prof_id = arguments.get("id")
            nombre = arguments.get("nombre")
            
            if not prof_id and not nombre:
                return [TextContent(type="text", text="❌ Debes proporcionar 'id' o 'nombre'")]
            
            query = """
                SELECT p.*, 
                       (SELECT COUNT(*) FROM resenias_metadata WHERE profesor_id = p.id) as total_resenias
                FROM profesores p
                WHERE 
            """
            
            if prof_id:
                query += "p.id = $1"
                params = [prof_id]
            else:
                query += "p.nombre_completo ILIKE $1"
                params = [f"%{nombre}%"]
            
            async with pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)
            
            if not row:
                return [TextContent(type="text", text="❌ Profesor no encontrado")]
            
            p = serialize_row(row)
            output = f"""
👨‍🏫 **Detalle de Profesor**

| Campo | Valor |
|-------|-------|
| ID | {p['id']} |
| Nombre | {p['nombre_completo']} |
| Nombre Limpio | {p['nombre_limpio']} |
| Departamento | {p['departamento']} |
| Slug | {p['slug']} |
| Activo | {'✅' if p['activo'] else '❌'} |
| Total Reseñas | {p['total_resenias']} |
| Creado | {p['created_at']} |
"""
            return [TextContent(type="text", text=output)]
        
        elif name == "pg_listar_cursos":
            nombre = arguments.get("nombre")
            departamento = arguments.get("departamento")
            limit = arguments.get("limit", 50)
            
            query = "SELECT * FROM cursos WHERE 1=1"
            params = []
            
            if nombre:
                query += f" AND nombre ILIKE ${len(params) + 1}"
                params.append(f"%{nombre}%")
            
            if departamento:
                query += f" AND departamento = ${len(params) + 1}"
                params.append(departamento)
            
            query += f" ORDER BY total_resenias DESC LIMIT ${len(params) + 1}"
            params.append(limit)
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                result = [serialize_row(row) for row in rows]
            
            output = f"📖 **{len(result)} cursos encontrados**\n\n"
            for c in result:
                output += f"- **[{c['id']}]** {c['nombre']} ({c['total_resenias']} reseñas)\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "pg_resenias_profesor":
            profesor_id = arguments["profesor_id"]
            limit = arguments.get("limit", 50)
            
            query = """
                SELECT rm.*, c.nombre as curso_nombre
                FROM resenias_metadata rm
                LEFT JOIN cursos c ON rm.curso_id = c.id
                WHERE rm.profesor_id = $1
                ORDER BY rm.fecha_resenia DESC
                LIMIT $2
            """
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, profesor_id, limit)
                result = [serialize_row(row) for row in rows]
            
            output = f"📝 **{len(result)} reseñas del profesor {profesor_id}**\n\n"
            for r in result:
                output += f"- [{r['fecha_resenia']}] {r.get('curso_nombre', 'N/A')} - Calidad: {r.get('calidad_general', 'N/A')}\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "pg_estadisticas":
            async with pool.acquire() as conn:
                stats = {}
                stats['profesores'] = await conn.fetchval("SELECT COUNT(*) FROM profesores WHERE activo = true")
                stats['cursos'] = await conn.fetchval("SELECT COUNT(*) FROM cursos")
                stats['resenias'] = await conn.fetchval("SELECT COUNT(*) FROM resenias_metadata")
                stats['perfiles'] = await conn.fetchval("SELECT COUNT(*) FROM perfiles")
                
                # Departamentos
                dept_rows = await conn.fetch("""
                    SELECT departamento, COUNT(*) as count 
                    FROM profesores 
                    WHERE activo = true 
                    GROUP BY departamento
                """)
                stats['departamentos'] = {row['departamento']: row['count'] for row in dept_rows}
            
            output = f"""
📊 **Estadísticas de PostgreSQL**

| Métrica | Valor |
|---------|-------|
| Profesores activos | {stats['profesores']} |
| Cursos | {stats['cursos']} |
| Reseñas (metadata) | {stats['resenias']} |
| Perfiles | {stats['perfiles']} |

**Por Departamento:**
"""
            for dept, count in stats['departamentos'].items():
                output += f"- {dept}: {count} profesores\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "pg_perfil_profesor":
            profesor_id = arguments["profesor_id"]
            
            query = """
                SELECT p.*, pr.nombre_completo as profesor_nombre
                FROM perfiles p
                JOIN profesores pr ON p.profesor_id = pr.id
                WHERE p.profesor_id = $1
                ORDER BY p.fecha_extraccion DESC
                LIMIT 1
            """
            
            async with pool.acquire() as conn:
                row = await conn.fetchrow(query, profesor_id)
            
            if not row:
                return [TextContent(type="text", text="❌ Perfil no encontrado")]
            
            p = serialize_row(row)
            output = f"""
📈 **Perfil de {p['profesor_nombre']}**

| Métrica | Valor |
|---------|-------|
| Calidad General | {p.get('calidad_general', 'N/A')} |
| Dificultad | {p.get('dificultad', 'N/A')} |
| % Recomendación | {p.get('porcentaje_recomendacion', 'N/A')}% |
| Total Reseñas | {p.get('total_resenias_encontradas', 0)} |
| Fuente | {p.get('fuente', 'N/A')} |
| Fecha Extracción | {p.get('fecha_extraccion', 'N/A')} |
"""
            return [TextContent(type="text", text=output)]
        
        elif name == "pg_schema":
            tabla = arguments.get("tabla")
            
            if tabla:
                query = """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = $1
                    ORDER BY ordinal_position
                """
                async with pool.acquire() as conn:
                    rows = await conn.fetch(query, tabla)
                
                output = f"📋 **Esquema de tabla: {tabla}**\n\n"
                output += "| Columna | Tipo | Nullable | Default |\n|---------|------|----------|---------|\n"
                for r in rows:
                    output += f"| {r['column_name']} | {r['data_type']} | {r['is_nullable']} | {r['column_default'] or '-'} |\n"
            else:
                query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """
                async with pool.acquire() as conn:
                    rows = await conn.fetch(query)
                
                output = "📋 **Tablas disponibles:**\n\n"
                for r in rows:
                    output += f"- {r['table_name']}\n"
            
            return [TextContent(type="text", text=output)]
        
        else:
            return [TextContent(type="text", text=f"❌ Herramienta desconocida: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def main():
    """Punto de entrada principal."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

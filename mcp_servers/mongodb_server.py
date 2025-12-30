#!/usr/bin/env python3
"""
MCP Server para MongoDB - SentimentInsightUAM_SA

Servidor MCP que proporciona acceso a la base de datos MongoDB
con herramientas para consultar y analizar opiniones y sentimientos.

Autor: SentimentInsightUAM Team
Fecha: 2025-12-03
"""

import os
import sys
import json
import asyncio
from typing import Any, Optional
from datetime import datetime, date
from bson import ObjectId

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from motor.motor_asyncio import AsyncIOMotorClient

# Cargar variables de entorno
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Configuración de conexión
MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://sentiment_admin:dev_password_2024@localhost:27017/sentiment_uam_nlp?authSource=sentiment_uam_nlp"
)
MONGO_DB_NAME = os.getenv("MONGO_DB", "sentiment_uam_nlp")

# Cliente MongoDB global
_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    """Obtiene o crea el cliente MongoDB."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    """Obtiene la base de datos."""
    return get_client()[MONGO_DB_NAME]


def serialize_value(value: Any) -> Any:
    """Serializa valores para JSON."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serialize_value(v) for v in value]
    return value


def serialize_doc(doc: dict) -> dict:
    """Convierte un documento MongoDB a diccionario serializable."""
    return serialize_value(doc)


# Crear servidor MCP
server = Server("sentiment-mongodb")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Lista las herramientas disponibles."""
    return [
        Tool(
            name="mongo_query",
            description="Ejecuta una consulta find en MongoDB. Usa sintaxis JSON para filtros.",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Nombre de la colección (default: 'opiniones')",
                        "default": "opiniones"
                    },
                    "filter": {
                        "type": "object",
                        "description": "Filtro de consulta en formato JSON"
                    },
                    "projection": {
                        "type": "object",
                        "description": "Campos a incluir/excluir"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Límite de resultados (default: 20)",
                        "default": 20
                    },
                    "sort": {
                        "type": "object",
                        "description": "Ordenamiento (ej: {'fecha_opinion': -1})"
                    }
                }
            }
        ),
        Tool(
            name="mongo_opiniones_profesor",
            description="Obtiene opiniones de un profesor específico con análisis de sentimiento.",
            inputSchema={
                "type": "object",
                "properties": {
                    "profesor_id": {
                        "type": "integer",
                        "description": "ID del profesor"
                    },
                    "profesor_nombre": {
                        "type": "string",
                        "description": "Nombre del profesor (búsqueda parcial)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Límite de resultados (default: 20)",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="mongo_opiniones_materia",
            description="Obtiene opiniones de una materia/curso específico.",
            inputSchema={
                "type": "object",
                "properties": {
                    "curso": {
                        "type": "string",
                        "description": "Nombre del curso (búsqueda parcial)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Límite de resultados (default: 20)",
                        "default": 20
                    }
                },
                "required": ["curso"]
            }
        ),
        Tool(
            name="mongo_estadisticas_sentimiento",
            description="Obtiene estadísticas de análisis de sentimiento.",
            inputSchema={
                "type": "object",
                "properties": {
                    "profesor_id": {
                        "type": "integer",
                        "description": "ID de profesor (opcional, para filtrar)"
                    },
                    "curso": {
                        "type": "string",
                        "description": "Nombre del curso (opcional, para filtrar)"
                    }
                }
            }
        ),
        Tool(
            name="mongo_distribucion_sentimiento",
            description="Obtiene la distribución de sentimientos (positivo, neutral, negativo).",
            inputSchema={
                "type": "object",
                "properties": {
                    "profesor_id": {
                        "type": "integer",
                        "description": "Filtrar por profesor"
                    },
                    "curso": {
                        "type": "string",
                        "description": "Filtrar por curso"
                    }
                }
            }
        ),
        Tool(
            name="mongo_top_materias",
            description="Obtiene las materias con más opiniones.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Número de materias a mostrar (default: 10)",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="mongo_analisis_categorizacion",
            description="Obtiene análisis de categorización (calidad didáctica, método evaluación, empatía).",
            inputSchema={
                "type": "object",
                "properties": {
                    "profesor_id": {
                        "type": "integer",
                        "description": "Filtrar por profesor"
                    },
                    "curso": {
                        "type": "string",
                        "description": "Filtrar por curso"
                    }
                }
            }
        ),
        Tool(
            name="mongo_buscar_opiniones",
            description="Busca opiniones por texto en el comentario.",
            inputSchema={
                "type": "object",
                "properties": {
                    "texto": {
                        "type": "string",
                        "description": "Texto a buscar en los comentarios"
                    },
                    "sentimiento": {
                        "type": "string",
                        "description": "Filtrar por sentimiento: 'positivo', 'neutral', 'negativo'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Límite de resultados (default: 20)",
                        "default": 20
                    }
                },
                "required": ["texto"]
            }
        ),
        Tool(
            name="mongo_colecciones",
            description="Lista las colecciones disponibles en MongoDB.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="mongo_estructura_documento",
            description="Muestra la estructura de un documento de ejemplo de una colección.",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Nombre de la colección",
                        "default": "opiniones"
                    }
                }
            }
        ),
        Tool(
            name="mongo_aggregate",
            description="Ejecuta un pipeline de agregación en MongoDB.",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Nombre de la colección",
                        "default": "opiniones"
                    },
                    "pipeline": {
                        "type": "array",
                        "description": "Pipeline de agregación en formato JSON"
                    }
                },
                "required": ["pipeline"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Ejecuta una herramienta."""
    db = get_db()
    
    try:
        if name == "mongo_query":
            collection = arguments.get("collection", "opiniones")
            filter_query = arguments.get("filter", {})
            projection = arguments.get("projection")
            limit = arguments.get("limit", 20)
            sort = arguments.get("sort")
            
            cursor = db[collection].find(filter_query, projection)
            if sort:
                cursor = cursor.sort(list(sort.items()))
            cursor = cursor.limit(limit)
            
            docs = await cursor.to_list(length=limit)
            result = [serialize_doc(doc) for doc in docs]
            
            return [TextContent(
                type="text",
                text=f"✅ {len(result)} documentos encontrados:\n```json\n{json.dumps(result, indent=2, ensure_ascii=False)}\n```"
            )]
        
        elif name == "mongo_opiniones_profesor":
            profesor_id = arguments.get("profesor_id")
            profesor_nombre = arguments.get("profesor_nombre")
            limit = arguments.get("limit", 20)
            
            if not profesor_id and not profesor_nombre:
                return [TextContent(type="text", text="❌ Debes proporcionar 'profesor_id' o 'profesor_nombre'")]
            
            filter_query = {}
            if profesor_id:
                filter_query["profesor_id"] = profesor_id
            else:
                filter_query["profesor_nombre"] = {"$regex": profesor_nombre, "$options": "i"}
            
            cursor = db.opiniones.find(filter_query).sort("fecha_opinion", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
            
            output = f"📝 **{len(docs)} opiniones encontradas**\n\n"
            for doc in docs:
                sent = doc.get('sentimiento_general', {})
                clasificacion = sent.get('clasificacion', 'N/A').upper()
                confianza = sent.get('confianza', 0)
                emoji = '✅' if clasificacion == 'POSITIVO' else ('❌' if clasificacion == 'NEGATIVO' else '⚪')
                
                comentario = doc.get('comentario', '')[:150]
                output += f"{emoji} **{clasificacion}** (conf: {confianza:.2f}) - {doc.get('curso', 'N/A')}\n"
                output += f"   > \"{comentario}...\"\n\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "mongo_opiniones_materia":
            curso = arguments["curso"]
            limit = arguments.get("limit", 20)
            
            cursor = db.opiniones.find({
                "curso": {"$regex": curso, "$options": "i"}
            }).sort("fecha_opinion", -1).limit(limit)
            
            docs = await cursor.to_list(length=limit)
            
            output = f"📚 **{len(docs)} opiniones de '{curso}'**\n\n"
            for doc in docs:
                sent = doc.get('sentimiento_general', {})
                clasificacion = sent.get('clasificacion', 'N/A').upper()
                emoji = '✅' if clasificacion == 'POSITIVO' else ('❌' if clasificacion == 'NEGATIVO' else '⚪')
                
                output += f"{emoji} {doc.get('profesor_nombre', 'N/A')}\n"
                output += f"   > \"{doc.get('comentario', '')[:100]}...\"\n\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "mongo_estadisticas_sentimiento":
            profesor_id = arguments.get("profesor_id")
            curso = arguments.get("curso")
            
            filter_query = {}
            if profesor_id:
                filter_query["profesor_id"] = profesor_id
            if curso:
                filter_query["curso"] = {"$regex": curso, "$options": "i"}
            
            total = await db.opiniones.count_documents(filter_query)
            analizadas = await db.opiniones.count_documents({
                **filter_query,
                "sentimiento_general.analizado": True
            })
            
            # Modelo usado
            doc = await db.opiniones.find_one({"sentimiento_general.analizado": True})
            modelo = doc.get('sentimiento_general', {}).get('modelo_version', 'N/A') if doc else 'N/A'
            
            output = f"""
📊 **Estadísticas de Análisis de Sentimiento**

| Métrica | Valor |
|---------|-------|
| Total opiniones | {total} |
| Analizadas | {analizadas} ({analizadas/total*100 if total > 0 else 0:.1f}%) |
| Modelo | {modelo} |
"""
            return [TextContent(type="text", text=output)]
        
        elif name == "mongo_distribucion_sentimiento":
            profesor_id = arguments.get("profesor_id")
            curso = arguments.get("curso")
            
            filter_query = {"sentimiento_general.analizado": True}
            if profesor_id:
                filter_query["profesor_id"] = profesor_id
            if curso:
                filter_query["curso"] = {"$regex": curso, "$options": "i"}
            
            total = await db.opiniones.count_documents(filter_query)
            positivo = await db.opiniones.count_documents({**filter_query, "sentimiento_general.clasificacion": "positivo"})
            neutral = await db.opiniones.count_documents({**filter_query, "sentimiento_general.clasificacion": "neutral"})
            negativo = await db.opiniones.count_documents({**filter_query, "sentimiento_general.clasificacion": "negativo"})
            
            output = f"""
📈 **Distribución de Sentimientos**

| Sentimiento | Cantidad | Porcentaje |
|-------------|----------|------------|
| ✅ Positivo | {positivo} | {positivo/total*100 if total > 0 else 0:.1f}% |
| ⚪ Neutral | {neutral} | {neutral/total*100 if total > 0 else 0:.1f}% |
| ❌ Negativo | {negativo} | {negativo/total*100 if total > 0 else 0:.1f}% |
| **Total** | **{total}** | **100%** |
"""
            return [TextContent(type="text", text=output)]
        
        elif name == "mongo_top_materias":
            limit = arguments.get("limit", 10)
            
            pipeline = [
                {"$group": {"_id": "$curso", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]
            
            cursor = db.opiniones.aggregate(pipeline)
            docs = await cursor.to_list(length=limit)
            
            output = f"🏆 **Top {limit} Materias por Opiniones**\n\n"
            for i, doc in enumerate(docs, 1):
                output += f"{i}. **{doc['_id']}** - {doc['count']} opiniones\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "mongo_analisis_categorizacion":
            profesor_id = arguments.get("profesor_id")
            curso = arguments.get("curso")
            
            filter_query = {"categorizacion.analizado": True}
            if profesor_id:
                filter_query["profesor_id"] = profesor_id
            if curso:
                filter_query["curso"] = {"$regex": curso, "$options": "i"}
            
            total = await db.opiniones.count_documents(filter_query)
            
            categorias = ["calidad_didactica", "metodo_evaluacion", "empatia"]
            output = f"📊 **Análisis de Categorización** ({total} opiniones)\n\n"
            
            for cat in categorias:
                pos = await db.opiniones.count_documents({**filter_query, f"categorizacion.{cat}.valoracion": "positivo"})
                neu = await db.opiniones.count_documents({**filter_query, f"categorizacion.{cat}.valoracion": "neutral"})
                neg = await db.opiniones.count_documents({**filter_query, f"categorizacion.{cat}.valoracion": "negativo"})
                
                cat_display = cat.replace("_", " ").title()
                output += f"**{cat_display}:**\n"
                output += f"  ✅ Positivo: {pos} ({pos/total*100 if total > 0 else 0:.1f}%)\n"
                output += f"  ⚪ Neutral: {neu} ({neu/total*100 if total > 0 else 0:.1f}%)\n"
                output += f"  ❌ Negativo: {neg} ({neg/total*100 if total > 0 else 0:.1f}%)\n\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "mongo_buscar_opiniones":
            texto = arguments["texto"]
            sentimiento = arguments.get("sentimiento")
            limit = arguments.get("limit", 20)
            
            filter_query = {
                "comentario": {"$regex": texto, "$options": "i"}
            }
            if sentimiento:
                filter_query["sentimiento_general.clasificacion"] = sentimiento
            
            cursor = db.opiniones.find(filter_query).limit(limit)
            docs = await cursor.to_list(length=limit)
            
            output = f"🔍 **{len(docs)} opiniones con '{texto}'**\n\n"
            for doc in docs:
                sent = doc.get('sentimiento_general', {})
                clasificacion = sent.get('clasificacion', 'N/A').upper()
                emoji = '✅' if clasificacion == 'POSITIVO' else ('❌' if clasificacion == 'NEGATIVO' else '⚪')
                
                output += f"{emoji} **{doc.get('profesor_nombre', 'N/A')}** - {doc.get('curso', 'N/A')}\n"
                output += f"   > \"{doc.get('comentario', '')[:120]}...\"\n\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "mongo_colecciones":
            collections = await db.list_collection_names()
            
            output = "📦 **Colecciones en MongoDB**\n\n"
            for col in collections:
                count = await db[col].count_documents({})
                output += f"- **{col}**: {count} documentos\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "mongo_estructura_documento":
            collection = arguments.get("collection", "opiniones")
            
            doc = await db[collection].find_one()
            if not doc:
                return [TextContent(type="text", text=f"❌ Colección '{collection}' vacía")]
            
            def describe_structure(obj, indent=0):
                lines = []
                prefix = "  " * indent
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if isinstance(v, dict):
                            lines.append(f"{prefix}**{k}**: (objeto)")
                            lines.extend(describe_structure(v, indent + 1))
                        elif isinstance(v, list):
                            lines.append(f"{prefix}**{k}**: [array]")
                        else:
                            tipo = type(v).__name__
                            lines.append(f"{prefix}**{k}**: {tipo}")
                return lines
            
            structure = describe_structure(serialize_doc(doc))
            output = f"📋 **Estructura de '{collection}'**\n\n" + "\n".join(structure)
            
            return [TextContent(type="text", text=output)]
        
        elif name == "mongo_aggregate":
            collection = arguments.get("collection", "opiniones")
            pipeline = arguments["pipeline"]
            
            cursor = db[collection].aggregate(pipeline)
            docs = await cursor.to_list(length=100)
            result = [serialize_doc(doc) for doc in docs]
            
            return [TextContent(
                type="text",
                text=f"✅ {len(result)} resultados:\n```json\n{json.dumps(result, indent=2, ensure_ascii=False)}\n```"
            )]
        
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

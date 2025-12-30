# MCP Servers - SentimentInsightUAM_SA

Este directorio contiene servidores MCP (Model Context Protocol) para comunicación 
con las bases de datos del proyecto.

## Servidores Disponibles

### 1. PostgreSQL Server (`postgres_server.py`)
Proporciona acceso a la base de datos relacional PostgreSQL.

**Herramientas disponibles:**
- `pg_query` - Ejecuta consultas SQL SELECT
- `pg_listar_profesores` - Lista profesores con filtros
- `pg_detalle_profesor` - Detalle de un profesor
- `pg_listar_cursos` - Lista cursos/materias
- `pg_resenias_profesor` - Reseñas de un profesor
- `pg_estadisticas` - Estadísticas generales
- `pg_perfil_profesor` - Perfil de calificaciones
- `pg_schema` - Esquema de tablas

### 2. MongoDB Server (`mongodb_server.py`)
Proporciona acceso a la base de datos de documentos MongoDB.

**Herramientas disponibles:**
- `mongo_query` - Consulta find genérica
- `mongo_opiniones_profesor` - Opiniones de un profesor
- `mongo_opiniones_materia` - Opiniones de una materia
- `mongo_estadisticas_sentimiento` - Estadísticas de sentimiento
- `mongo_distribucion_sentimiento` - Distribución pos/neu/neg
- `mongo_top_materias` - Top materias por opiniones
- `mongo_analisis_categorizacion` - Análisis de categorías
- `mongo_buscar_opiniones` - Búsqueda por texto
- `mongo_colecciones` - Lista colecciones
- `mongo_estructura_documento` - Estructura de documentos
- `mongo_aggregate` - Pipeline de agregación

## Instalación

### Dependencias
```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias MCP
pip install mcp asyncpg motor python-dotenv
```

## Configuración en VS Code

Agregar al archivo `~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "sentiment-postgres": {
      "command": "/home/mr_ciem/dev/python-dev/SentimentInsightUAM_SA/venv/bin/python",
      "args": ["/home/mr_ciem/dev/python-dev/SentimentInsightUAM_SA/mcp_servers/postgres_server.py"],
      "env": {}
    },
    "sentiment-mongodb": {
      "command": "/home/mr_ciem/dev/python-dev/SentimentInsightUAM_SA/venv/bin/python",
      "args": ["/home/mr_ciem/dev/python-dev/SentimentInsightUAM_SA/mcp_servers/mongodb_server.py"],
      "env": {}
    }
  }
}
```

## Uso

Una vez configurados, los servidores MCP estarán disponibles automáticamente
en el asistente AI de VS Code, permitiendo consultas directas a las bases de datos.

### Ejemplos de uso:

**PostgreSQL:**
- "Lista los profesores del departamento de Sistemas"
- "Muestra el perfil del profesor con ID 36"
- "¿Cuántas reseñas hay en total?"

**MongoDB:**
- "Muestra la distribución de sentimientos"
- "Busca opiniones que mencionen 'examen'"
- "Top 10 materias con más opiniones"

## Notas

- Los servidores utilizan las credenciales del archivo `.env` del proyecto
- Solo se permiten operaciones de lectura (SELECT en PostgreSQL)
- Las conexiones se manejan de forma asíncrona para mejor rendimiento

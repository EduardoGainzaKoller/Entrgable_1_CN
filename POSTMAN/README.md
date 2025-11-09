# Pruebas de la API — Champions App

Este proyecto incluye colecciones Postman para probar los endpoints del API Gateway desplegado en AWS.

## Archivos incluidos
- `ChampionsAPI_Base.postman_collection.json` — versión base de la API (sin API Key).  
- `ChampionsAPI_Desacoplada.postman_collection.json` — versión desacoplada de la API (con API Key requerida).

---

## Uso de las colecciones

### 1. Importación en Postman
Las colecciones pueden importarse en Postman mediante la opción **Import**.  
Se debe seleccionar el archivo `.json` correspondiente o pegar su contenido en la pestaña *Raw Text*.  
Una vez importadas, los endpoints quedarán disponibles para su ejecución.

### 2. Configuración de variables
Antes de ejecutar las solicitudes, deben configurarse las variables de entorno indicadas en Postman, de acuerdo con los valores obtenidos del despliegue en AWS:

| Variable | Descripción | Ejemplo |
|-----------|--------------|----------|
| `base_url` | URL base de la API (output `ApiUrl` en CloudFormation) | `https://abc123.execute-api.us-east-1.amazonaws.com/prod` |
| `api_key` | (Solo versión desacoplada) valor de la API Key (output `ApiKeyValue`) | `abcdEFGH12345678` |
| `champion_id` | ID de prueba para operaciones GET/PUT/DELETE | `1` |

---

## Endpoints disponibles

La API ofrece los siguientes endpoints para gestionar campeones:

### GET /champions
Obtiene la lista completa de campeones.
- **Método**: GET
- **Autenticación**: No requerida (base) / API Key (desacoplada)
- **Respuesta**: Array de objetos champion

### GET /champions/{champion_id}
Obtiene un campeón específico por su ID.
- **Método**: GET
- **Parámetros**: champion_id (path)
- **Autenticación**: No requerida (base) / API Key (desacoplada)
- **Respuesta**: Objeto champion

### POST /champions
Crea un nuevo campeón.
- **Método**: POST
- **Body**: Objeto champion (JSON)
- **Autenticación**: No requerida (base) / API Key (desacoplada)
- **Respuesta**: Objeto champion creado

### PUT /champions/{champion_id}
Actualiza un campeón existente.
- **Método**: PUT
- **Parámetros**: champion_id (path)
- **Body**: Objeto champion (JSON)
- **Autenticación**: No requerida (base) / API Key (desacoplada)
- **Respuesta**: Objeto champion actualizado

### DELETE /champions/{champion_id}
Elimina un campeón existente.
- **Método**: DELETE
- **Parámetros**: champion_id (path)
- **Autenticación**: No requerida (base) / API Key (desacoplada)
- **Respuesta**: Mensaje de confirmación

## Estructura del objeto Champion

```json
{
  "id": "string",
  "name": "string",
  "role": "string",
  "difficulty": "string",
  "description": "string"
}
```

## Códigos de respuesta

| Código | Descripción |
|--------|-------------|
| 200 | Operación exitosa |
| 201 | Recurso creado exitosamente |
| 400 | Solicitud incorrecta |
| 404 | Recurso no encontrado |
| 403 | Acceso denegado (solo versión desacoplada) |
| 500 | Error interno del servidor |

## Ejemplos de uso

### Crear un nuevo campeón
```json
POST /champions
{
  "name": "Ahri",
  "role": "Mage",
  "difficulty": "Moderate",
  "description": "The Nine-Tailed Fox"
}
```

### Actualizar un campeón existente
```json
PUT /champions/1
{
  "name": "Ahri",
  "role": "Mage",
  "difficulty": "High",
  "description": "The Nine-Tailed Fox - Updated"
}
```

---

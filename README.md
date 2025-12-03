# SIPV – Sistema de Inventario y Punto de Venta  
Aplicación web desarrollada con Django, MySQL y Docker para la gestión integral de inventario, ventas, compras y facturación en una pulpería o negocio minorista.

---

## 1. Descripción del Proyecto

El Sistema de Inventario y Punto de Venta (SIPV) es una plataforma web diseñada para optimizar las operaciones diarias de comercios minoristas.  
Permite administrar productos, categorías, proveedores, compras, ventas, facturas, movimientos de inventario y reportes operativos.

El sistema está desarrollado con:

- Django 5.2 (Backend)
- MySQL 8.0 Primary–Replica
- Docker y Docker Compose
- TailwindCSS (UI)
- Django Rest Framework para APIs internas

Su arquitectura está orientada a facilitar escalabilidad, mantenibilidad y despliegue reproducible tanto en desarrollo como en producción.

---

## 2. Características Principales

### Módulo de Inventario
- Gestión de productos, categorías y proveedores  
- Control de existencias y unidades  
- Movimientos automáticos por compras y ventas  
- Ajustes manuales de inventario

### Módulo de Compras
- Registro de órdenes de compra  
- Cálculo automático de costos  
- Actualización de inventario al recibir productos

### Módulo de Ventas y POS
- Búsqueda rápida de productos  
- Carrito de venta optimizado  
- Aplicación de reglas de precio  
- Generación de facturas

### Módulo SAR y Facturación
- Facturación conforme a requisitos fiscales locales  
- Control de rangos y numeración  
- Emisión de facturas válidas

### Auditoría y Seguridad
- Registro de actividades  
- Control de permisos basado en roles  
- Integración con sistema de autenticación personalizado

---

## 3. Arquitectura del Proyecto

El sistema está organizado con una estructura modular:

```
backend/
  maestros/
  inventario/
  compras/
  ventas/
  facturas/
  caja/
  sar/
  auditoria/
  common/
  authapp/
docker/
static/
templates/
```

Cada módulo representa una pieza funcional independiente y mantiene sus propios modelos, vistas y controladores.

---

## 4. Requisitos Previos

- Python 3.11+
- Docker y Docker Compose
- MySQL 8.0 (si no se usa Docker)
- Git

---

## 5. Instalación con Docker

### 1. Clonar el repositorio

```bash
git clone https://github.com/usuario/sipv.git
cd sipv
```

### 2. Crear archivo de entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
cp .env.example .env
```

Editar valores según su entorno.

### 3. Levantar la aplicación

```bash
docker compose up -d --build
```

Esto inicia:

- MySQL Primary
- MySQL Replica
- Django (sipv_web)
- Adminer (para visualizar la base de datos)

### 4. Acceder al sistema

- Aplicación web: http://localhost  
- Adminer: http://localhost:8080

---

## 6. Ejecución sin Docker (modo desarrollo)

1. Crear entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Aplicar migraciones:

```bash
python manage.py migrate
```

4. Ejecutar servidor:

```bash
python manage.py runserver
```

---

## 7. Estructura de Archivos

- `backend/` – Código principal de la aplicación  
- `docker/` – Configuraciones de MySQL y contenedores  
- `templates/` – Plantillas HTML  
- `static/` – Archivos estáticos usados durante desarrollo  
- `staticfiles/` – Archivos estáticos recolectados (collectstatic)

---

## 8. Variables de Entorno

El proyecto utiliza un archivo `.env` para credenciales y configuración sensible:

```
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=sipv
DB_USER=sipvuser
DB_PASSWORD=sipvpass
DB_HOST=mysql_primary
DB_PORT=3306
LANGUAGE_CODE=es-hn
TIME_ZONE=America/Tegucigalpa
```

Este archivo **no debe subirse al repositorio**.

---

## 9. Licencia

Este proyecto es propiedad del autor y no se distribuye bajo una licencia abierta, a menos que se indique lo contrario.

---

## 10. Autor

Sistema desarrollado por Allan Flores para usos educativos y comerciales.

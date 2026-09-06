# Atuel Gomas - Catálogo Técnico & Plataforma B2B Mayorista

Proyecto web desarrollado en **Python** aplicando **Clean Architecture** (Arquitectura Limpia según Robert C. Martin / Uncle Bob) y el patrón **Modelo-Vista-Controlador (MVC)**. Diseñado especialmente para la comercialización mayorista y minorista de mangueras, burletes, fuelles, planchas de caucho y repuestos técnicos hacia ferreterías industriales y casas de repuestos automotores.

---

## 🏛️ Estructura de Clean Architecture

El proyecto se encuentra modularizado en 4 capas estrictas con la regla de dependencia unidireccional (el núcleo del negocio no conoce frameworks ni bases de datos):

```
atuel_gomas/
├── src/
│   ├── domain/                  # 1. Capa de Dominio (Entidades y Reglas de Negocio Puras)
│   │   ├── entities/            # Product, Customer, Order, VehicleCompatibility
│   │   ├── value_objects/       # Dimensions, CUIT, Money (inmutables y autocontenidos)
│   │   └── exceptions/          # Excepciones de negocio (InsufficientStock, DomainException)
│   │
│   ├── application/             # 2. Capa de Aplicación (Casos de Uso y Orquestación)
│   │   ├── use_cases/           # Búsqueda de productos, autenticación B2B, creación de pedidos
│   │   ├── ports/               # Interfaces/Contratos (IProductRepository, ICustomerRepository, IPasswordHasher)
│   │   └── dtos/                # Data Transfer Objects (Pydantic) de entrada y salida
│   │
│   ├── adapters/                # 3. Adaptadores de Interfaz (MVC & Repositorios Concretos)
│   │   ├── controllers/         # WebControllers (Endpoints HTTP FastAPI para SSR)
│   │   ├── presenters/          # Modelos de presentación para Jinja2
│   │   ├── repositories/        # Implementaciones de repositorios (Memory y SQLAlchemy)
│   │   └── security/            # Adaptador de hashing criptográfico con Bcrypt
│   │
│   └── infrastructure/          # 4. Infraestructura y Frameworks
│       ├── config/              # Inyección de dependencias (Container IoC)
│       ├── web/                 # Configuración de servidor, middlewares y CORS
│       ├── templates/           # Vistas Jinja2 (HTML5 semántico + HTMX)
│       └── static/              # CSS moderno con diseño industrial técnico, JS y recursos
│
├── tests/
│   ├── unit/                    # Pruebas unitarias de dominio puras (sin DB)
│   └── integration/             # Pruebas de integración HTTP y controladores
│
├── Dockerfile                   # Empaquetado Docker listo para producción
├── requirements.txt             # Dependencias del proyecto
└── main.py                      # Punto de entrada de la aplicación FastAPI
```

---

## 🚀 Cómo Ejecutar el Proyecto Localmente

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DE_TU_REPOSITORIO_GITHUB>
   cd "Atuel Gomas"
   ```

2. **Crear e inicializar el entorno virtual:**
   ```bash
   python -m venv venv
   # En Windows:
   .\venv\Scripts\activate
   # En Linux / Mac:
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la suite de tests (Unitarios + Integración):**
   ```bash
   python -m pytest tests/ -v
   ```

5. **Iniciar el servidor de desarrollo:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   Abrir en el navegador: [http://localhost:8000](http://localhost:8000)

---

## 🌐 Cómo Desplegar en la Nube (GitHub + Render / Railway)

Como mencionaste en los requerimientos iniciales, la estrategia recomendada para no incurrir en costos elevados es:

1. **GitHub:** Subir el código a un repositorio público o privado.
2. **Render.com** (o Railway.app):
   - Crear una cuenta gratuita en [render.com](https://render.com).
   - Crear un **New Web Service** y conectarlo al repositorio de GitHub.
   - Configuración:
     - **Environment:** `Python 3` o `Docker` (utiliza el `Dockerfile` ya incluido en el proyecto).
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 10000`
   - Render configurará automáticamente el despliegue continuo (CI/CD): cada `git push` a GitHub actualizará la web automáticamente con certificado SSL HTTPS gratuito.
3. **Base de Datos (Fase de Crecimiento):**
   - Conectar un cluster de PostgreSQL gratuito en **Neon.tech** mediante la variable de entorno `DATABASE_URL`.
# Atuel_Gomas

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.adapters.controllers.web_controller import router as web_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Atuel Gomas - Sistema B2B y Catálogo Técnico",
        description="Plataforma de venta y consulta técnica mayorista para repuesteras y ferreterías",
        version="1.0.0"
    )

    # Servir archivos estáticos (CSS, JS, imágenes)
    app.mount("/static", StaticFiles(directory="src/infrastructure/static"), name="static")

    # Registrar rutas del controlador
    app.include_router(web_router)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

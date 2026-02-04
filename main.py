from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import httpx
import os
import regina_reg_sec_user_dto
import regina_wrapper_reg_sec_user
from regina_intent_model import load_or_create_model, retrain_model, save_example

app = FastAPI()

# -------------------------------
# Configuración CORS
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Configuración API externa
# (igual que en tu servicio Angular)
# -------------------------------
API_URL_PROCESS = "https://marcaciongps.aquariusconsultores.com:8443/regina-process-dev/api/"   # tu this.apiUrlProcess

API_URL_AUTH = "https://marcaciongps.aquariusconsultores.com:8443/regina-billing-dev/api/auth/"  # tu this.apiUrlAuth

API_URL_SEC = "https://marcaciongps.aquariusconsultores.com:8443/regina-billing-dev/api/" 

USER = regina_reg_sec_user_dto.WrapperRegSecUser()

intent_model = load_or_create_model()

class EntrenamientoRequest(BaseModel):
    texto: str
    intent: str


# -------------------------------
# Obtiene token igual que Angular
# -------------------------------
def obtener_token(dto: regina_reg_sec_user_dto.WrapperRegSecUser) -> str:
    url = f"{API_URL_AUTH}autenticar"
    headers = {
        "Content-Type": "application/json"
    }
    with httpx.Client(timeout=30, verify=False) as client:
        response = client.post(
            url,
            json=dto.model_dump(exclude_none=True),
            headers=headers
        )
        response.raise_for_status()

        data = response.json()
        return data.get("token")



# -------------------------------
# Modelo de request
# -------------------------------
class PreguntaRequest(BaseModel):
    mensaje: str


# -------------------------------
# Cliente a la API real Órdenes de Pago
# -------------------------------
async def obtener_ordenes_pago_api(
    dto: regina_reg_sec_user_dto
):

    url = (
        f"{API_URL_PROCESS}"
        f"orden-pago/listar/"
        f"{dto.codEmpresa}/"
        f"{dto.codSucursal}/"
        f"{dto.codAuxiliar}/"
    )

    # 👉 igual que en Angular: se usa el token ya existente
    api_token = dto.authToken
    if not api_token:
        raise Exception("authToken no enviado en el DTO")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30, verify=False) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

# -------------------------------
# Cliente a la API real Usuarios
# -------------------------------

async def obtener_usuarios_api(
    dto: regina_wrapper_reg_sec_user
):
    url = (
        f"{API_URL_SEC}"
        f"usuario/listar/"
        f"{dto.codEmpresa}/"
        f"{dto.codSucursal}/"
    )

    api_token = dto.authToken
    if not api_token:
        raise Exception("authToken no enviado en el DTO")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30, verify=False) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


# -------------------------------
# Endpoint /chat
# -------------------------------
@app.post("/chat")
async def chat(usuario: regina_reg_sec_user_dto.WrapperRegSecUser):

    texto = (usuario.mensaje or "").strip().lower()

    try:

        intent = intent_model.predict(texto)

        match intent:

            case "ORDENES_PAGO":

                data = await obtener_ordenes_pago_api(usuario)

                return {
                    "tipo": "ordenes",
                    "respuesta": "Lista Órdenes obtenida correctamente",
                    "data": data
                }

            case "USUARIOS":

                wrapper = regina_wrapper_reg_sec_user.WrapperRegSecListUsers(
                    codEmpresa=usuario.codEmpresa,
                    codSucursal=usuario.codSucursal,
                    authToken=usuario.authToken
                )

                data = await obtener_usuarios_api(wrapper)

                return {
                    "tipo": "usuarios",
                    "respuesta": "Lista de usuarios obtenida correctamente",
                    "data": data
                }

            case _:
                return {
                    "tipo": "texto",
                    "respuesta": "No entendí tu solicitud"
                }

    except Exception as e:
        return {
            "tipo": "error",
            "respuesta": "Error inesperado",
            "detalle": str(e)
        }
    
@app.post("/entrenar-intent")
def entrenar_intent(req: EntrenamientoRequest):

    global intent_model

    save_example(
        req.texto.lower().strip(),
        req.intent.strip().upper()
    )

    intent_model = retrain_model()

    return {
        "ok": True,
        "mensaje": "Modelo reentrenado correctamente"
    }


# -------------------------------
# Ejecutar web service en puerto 6700
# -------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=6700, reload=True)

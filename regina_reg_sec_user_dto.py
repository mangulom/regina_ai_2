from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WrapperRegSecUser(BaseModel):
    userUsername: Optional[str] = None
    authToken: Optional[str] = None
    mensaje: Optional[str] = None
    codEmpresa: Optional[str] = None
    codSucursal: Optional[str] = None
    codAuxiliar: Optional[str] = None
    isAdmin: Optional[str] = None

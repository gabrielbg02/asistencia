from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException,  staticfiles, Request, status, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from mongoengine import *
from mongoengine.connection import ConnectionFailure
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime, timedelta, tzinfo, timezone
from passlib.context import CryptContext
from bson.objectid import ObjectId

import os
import controllers
import json



app = FastAPI()
app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


SECRET_KEY = "e2ad5832-eea0-11ef-a2c3-1b7701b438d7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
utc_minus_4 = timezone(timedelta(hours=-4))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    # TODO: Include on the jwt the username and password???
    controllers.User(token.username, token.password)
    return None


# Conexión a MongoDB 
try:
    connect(
        db="asistencia",
        username="heimdall",
        password="Nn77Tw0WPM8Az1W1",
        host="mongodb+srv://cluster0.3vudx.mongodb.net",
        authentication_source='admin',
        ssl=True,
    )
    print("✅ Conectado a MongoDB")
except ConnectionFailure as e:
    print(f"❌ Error de conexión a MongoDB: {e}")

class Asistencia(Document):
    cedula = StringField(required=True) 
    fecha = DateTimeField(required=True)
    meta = {'collection': 'registros_asistencia'}


@app.post("/token", status_code=status.HTTP_200_OK)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = controllers.User(form_data.username, form_data.password)
    user.authenticate_user()
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.full_name}, expires_delta=access_token_expires)

    response = JSONResponse(content={"code":status.HTTP_200_OK, "msg": "ok"})
    response.set_cookie(key="sessionid", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Cabeceras para prevenir caching
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    return response


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    return templates.TemplateResponse("login.html", {"request": request}, headers=headers)


@app.get("/registro", response_class=HTMLResponse)
async def mostrar_formulario(request: Request):
    token = request.cookies.get("sessionid")
    if not token:
        return RedirectResponse(url="/", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
    except JWTError:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("asistencia.html", {"request": request , "user": username})

@app.get("/dashboard", response_class=HTMLResponse)
async def mostrar_formulario(request: Request):
    datos = Asistencia.objects().order_by('-id.generation_time')
    print(f"Cantidad de datos recuperados: {len(datos)}") 
    total_registros = Asistencia.objects.count()
    token = request.cookies.get("sessionid")
    if not token:
        return RedirectResponse(url="/", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
    except JWTError:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("dashboard.html", {"request": request , "user": username, "datos" : datos , "total_registros": total_registros})

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Eliminar la cookie de sesión
    response.delete_cookie("sessionid")
    
    # Cabeceras para prevenir caching
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    # Limpiar cualquier dato de sesión del servidor
    request.session.clear()
    
    return response




# Ruta para procesar el CSV
@app.post("/upload")
async def upload_csv(request: Request, file: UploadFile = File(...)):
    # Validar extensión del archivo
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, detail="Solo se permiten archivos CSV")
    
    try:
        # Leer el CSV con Pandas
        df = pd.read_csv(file.file, encoding='latin1', usecols=['sJobNo', 'Date', 'Time'])
        df['fecha_completa'] = df['Date'] + " " + df['Time']
        
        # Convertir a lista de diccionarios
        datos = df.to_dict('records')
        
        # Insertar en MongoDB
        
        for dato in datos:
            fecha_parseada = datetime.strptime(dato['fecha_completa'].strip(), "%Y-%m-%d %H:%M:%S")
            Asistencia(
                cedula=str(dato['sJobNo']),
                fecha=fecha_parseada
            ).save()
        return templates.TemplateResponse("exito.html", {"request": request})
    
    except Exception as e:
        raise HTTPException(500, detail=f"Error al procesar el CSV: {str(e)}")


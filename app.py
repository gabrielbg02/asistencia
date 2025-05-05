import pandas as pd
from mongoengine import connect, Document, StringField
from mongoengine.connection import ConnectionFailure

# --- 1. Cargar solo columnas específicas del CSV ---
try:
    # Lee solo las columnas necesarias
    columnas_necesarias = ['sName', 'sJobNo', 'Date', 'Time']  # Ajusta los nombres exactos de las columnas en tu CSV
    df = pd.read_csv("in-23042025.CSV", encoding='latin1', usecols=columnas_necesarias)
    
    df['fecha_completa'] = " " + df['Date'] + " " + df['Time']
    
    print("Datos cargados correctamente. Filas:", len(df))
    print(df.head())  # Verificación rápida
except Exception as e:
    print(f"Error al cargar el CSV: {e}")
    exit()

# --- 2. Conexión a MongoDB con MongoEngine ---
try:
    connect(
        db="asistencia",
        username="heimdall",
        password="Nn77Tw0WPM8Az1W1",
        host="mongodb+srv://cluster0.3vudx.mongodb.net",
        authentication_source='admin',
        ssl=True,
    )
    print("Conexión a MongoDB exitosa")
except ConnectionFailure as e:
    print(f"No se pudo conectar a MongoDB: {e}")

# --- 3. Definición del Documento ---
class Asistencia(Document):
    nombre = StringField()
    cedula = StringField() 
    fecha = StringField()
    meta = { 'collection': 'registros_asistencia'}

# --- 4. Insertar datos en MongoDB ---
try:
    # Convertir DataFrame a lista de diccionarios
    datos = df.to_dict('records')
    
    # Insertar cada registro
    for dato in datos:
        Asistencia(
            nombre=dato['sName'],
            cedula=str(dato['sJobNo']),  # Asegurar que cédula sea string
            fecha=str(dato['fecha_completa'])
        ).save()
    
    print(f"Datos insertados: {len(datos)} registros")
except Exception as e:
    print(f"Error al insertar datos: {e}")
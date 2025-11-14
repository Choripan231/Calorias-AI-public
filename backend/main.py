from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# CORS para permitir Expo/React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta a la base de datos de alimentos
DB_PATH = os.path.join(os.path.dirname(__file__), "nutrition_db.json")

# Cargar alimentos
def load_db():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- RUTAS -------------

@app.get("/")
def root():
    return {"status": "backend ok", "message": "CaloriasAI backend activo"}

@app.get("/nutrition")
def get_nutrition():
    """Devuelve todos los alimentos"""
    data = load_db()
    return data

@app.get("/nutrition/{food_name}")
def get_food(food_name: str):
    """Busca un alimento por nombre exacto"""
    db = load_db()
    food_name = food_name.lower()

    for item in db:
        if item["name"].lower() == food_name:
            return item

    return {"error": "Food not found"}

# Ejemplo de predicción simple
@app.post("/predict")
def predict(data: dict):
    """Demostración placeholder"""
    return {"message": "Modelo no integrado aún", "received": data}

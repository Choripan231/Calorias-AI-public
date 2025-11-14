"""CaloriasAI - Versión ampliada con macronutrientes y PWA HUD.
Editable y comentado.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict
import io, json, sqlite3, os
from datetime import date, datetime
from PIL import Image
import torch
import torchvision.transforms as T
from torchvision import models

DB_FILE = 'db_calorias.sqlite'
NUTRITION_DB = 'nutrition_db.json'

app = FastAPI(title='Calorias AI - Avanzado')

# ---------- Inicializar DB (sqlite) ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            age INTEGER,
            sex TEXT,
            height_cm REAL,
            weight_kg REAL,
            activity_level TEXT,
            goal_weight_kg REAL,
            goal_rate_kg_per_week REAL,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            timestamp TEXT,
            description TEXT,
            kcal REAL,
            grams REAL,
            kcal_per_100g REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- Cargar DB nutricional local (json) ----------
def load_nutrition_db():
    if not os.path.exists(NUTRITION_DB):
        return {}
    with open(NUTRITION_DB, 'r', encoding='utf-8') as f:
        return json.load(f)

NUT_DB = load_nutrition_db()

# ---------- Modelo imagen (simple) ----------
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = models.mobilenet_v3_large(pretrained=True).eval().to(device)
transform = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ---------- Utilidades nutricionales ----------
CAL_PER_GRAM = {'protein': 4, 'carbs': 4, 'fat': 9}
ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'active': 1.725,
    'very_active': 1.9
}

def bmr_mifflin_sejor(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    if sex.lower() in ['m', 'male']:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def tdee(weight_kg: float, height_cm: float, age: int, sex: str, activity: str) -> float:
    return bmr_mifflin_sejor(weight_kg, height_cm, age, sex) * ACTIVITY_MULTIPLIERS.get(activity, 1.375)

def macro_plan_for_weight_gain(current_weight: float, goal_rate_kg_per_week: float,
                               maintenance_calories: float, protein_per_kg: float = 2.0,
                               split: Dict[str, float] = None):
    """
    Devuelve kcal diarias objetivo y gramos de macros recomendados.
    - protein_per_kg: gramos de proteína por kg de peso corporal (default 2.0 g/kg para ganancia muscular)
    - split: reparto de calorías restante entre carbs y fat (porcentajes, deben sumar 1.0)
    """
    if split is None:
        split = {'carbs': 0.5, 'fat': 0.5}

    kcal_change_per_day = (goal_rate_kg_per_week * 7700) / 7.0
    target_calories = maintenance_calories + kcal_change_per_day

    protein_g = protein_per_kg * current_weight
    protein_kcal = protein_g * CAL_PER_GRAM['protein']

    remaining_kcal = target_calories - protein_kcal
    if remaining_kcal < 0:
        remaining_kcal = max(0, target_calories * 0.2)

    carbs_kcal = remaining_kcal * split['carbs']
    fat_kcal = remaining_kcal * split['fat']

    carbs_g = carbs_kcal / CAL_PER_GRAM['carbs']
    fat_g = fat_kcal / CAL_PER_GRAM['fat']

    return {
        'target_calories': round(target_calories, 1),
        'daily_surplus_deficit': round(kcal_change_per_day, 1),
        'protein_g': round(protein_g, 1),
        'protein_kcal': round(protein_kcal, 1),
        'carbs_g': round(carbs_g, 1),
        'carbs_kcal': round(carbs_kcal, 1),
        'fat_g': round(fat_g, 1),
        'fat_kcal': round(fat_kcal, 1)
    }

# ---------- Helpers DB ----------
def save_user(profile: dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO users 
        (user_id, name, age, sex, height_cm, weight_kg, activity_level, goal_weight_kg, goal_rate_kg_per_week, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        profile['user_id'], profile.get('name'), profile.get('age'), profile.get('sex'),
        profile.get('height_cm'), profile.get('weight_kg'), profile.get('activity_level'),
        profile.get('goal_weight_kg'), profile.get('goal_rate_kg_per_week'),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

def get_user(user_id: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT user_id, name, age, sex, height_cm, weight_kg, activity_level, goal_weight_kg, goal_rate_kg_per_week FROM users WHERE user_id=?', (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    keys = ['user_id', 'name', 'age', 'sex', 'height_cm', 'weight_kg', 'activity_level', 'goal_weight_kg', 'goal_rate_kg_per_week']
    return dict(zip(keys, row))

def log_meal_db(user_id: str, description: str, kcal: float, grams: Optional[float] = None, kcal_per_100g: Optional[float] = None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO meals (user_id, timestamp, description, kcal, grams, kcal_per_100g) VALUES (?, ?, ?, ?, ?, ?)',
              (user_id, datetime.utcnow().isoformat(), description, kcal, grams, kcal_per_100g))
    conn.commit()
    conn.close()

def get_daily_meals(user_id: str, for_date: date):
    start = datetime(for_date.year, for_date.month, for_date.day).isoformat()
    end = datetime(for_date.year, for_date.month, for_date.day, 23, 59, 59).isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT timestamp, description, kcal, grams, kcal_per_100g FROM meals WHERE user_id=? AND timestamp BETWEEN ? AND ? ORDER BY timestamp ASC',
              (user_id, start, end))
    rows = c.fetchall()
    conn.close()
    return [{'timestamp': r[0], 'description': r[1], 'kcal': r[2], 'grams': r[3], 'kcal_per_100g': r[4]} for r in rows]

# ---------- Endpoints ----------
class UserProfile(BaseModel):
    user_id: str
    name: Optional[str]
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    activity_level: str
    goal_weight_kg: float
    goal_rate_kg_per_week: float

class ExactMeal(BaseModel):
    user_id: str
    description: str
    grams: float
    kcal_per_100g: float

@app.post('/register_user')
async def register_user(profile: UserProfile):
    save_user(profile.dict())
    return {'status': 'ok'}

@app.get('/profile/{user_id}')
async def profile(user_id: str):
    u = get_user(user_id)
    if not u:
        raise HTTPException(status_code=404, detail='Usuario no encontrado')
    t = tdee(u['weight_kg'], u['height_cm'], u['age'], u['sex'], u['activity_level'])
    return {'user': u, 'tdee': round(t, 1)}

@app.post('/log-exact')
async def log_exact(meal: ExactMeal):
    if not get_user(meal.user_id):
        raise HTTPException(status_code=404, detail='Usuario no encontrado')
    kcal = (meal.kcal_per_100g * meal.grams) / 100.0
    log_meal_db(meal.user_id, meal.description, kcal, grams=meal.grams, kcal_per_100g=meal.kcal_per_100g)
    return {'status': 'ok', 'kcal_logged': round(kcal, 2)}

@app.post('/macro-plan')
async def macro_plan(user_id: str = Form(...), protein_g_per_kg: Optional[float] = Form(2.0), carbs_fat_split: Optional[str] = Form('50-50')):
    u = get_user(user_id)
    if not u:
        raise HTTPException(status_code=404, detail='Usuario no encontrado')
    maintenance = tdee(u['weight_kg'], u['height_cm'], u['age'], u['sex'], u['activity_level'])
    goal_rate = float(u.get('goal_rate_kg_per_week') or 0.25)
    try:
        c_pct, f_pct = [float(x)/100.0 for x in carbs_fat_split.split('-')]
    except Exception:
        c_pct, f_pct = 0.5, 0.5
    split = {'carbs': c_pct, 'fat': f_pct}
    plan = macro_plan_for_weight_gain(u['weight_kg'], goal_rate, maintenance, protein_per_kg=float(protein_g_per_kg), split=split)
    return plan

@app.get('/')
async def index():
    fp = os.path.join('static', 'frontend', 'index.html')
    return FileResponse(fp)

@app.get('/static/{path:path}')
async def static_files(path: str):
    fp = os.path.join('static', 'frontend', path)
    if not os.path.exists(fp):
        raise HTTPException(status_code=404)
    return FileResponse(fp)

@app.get('/nutrition_db')
async def nutrition_db():
    return JSONResponse(content=NUT_DB)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
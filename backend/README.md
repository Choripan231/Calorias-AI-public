
# Calorias AI - Prototipo Avanzado

Incluye:
- API (main.py) con endpoints extendidos: /log-exact, /macro-plan, /daily-summary, /profile, /nutrition_db
- Base nutricional local: nutrition_db.json (varios alimentos y macronutrientes)
- PWA HUD en static/frontend (index.html, manifest.json) — instalable desde navegador en tablet Android.

## Instalación rápida (PWA, recomendado si quieres usar desde tablet sin compilar APK)
1. Ejecuta la API en un ordenador o en un servidor accesible en la misma red.
2. Abre la IP: `http://<IP_DEL_SERVIDOR>:8000/` en el navegador del tablet.
3. Añadir a pantalla de inicio (Chrome: menú -> Añadir a pantalla de inicio).

## Generar APK desde tablet
- Compilar un APK nativo directamente en la tablet no es práctico ni fiable. Opciones:
  - Usar la **PWA** incluida: se instala como app sin APK (recomendado para tablet).
  - Opción avanzada: usar **Expo / EAS** en la nube para compilar un APK y descargarlo en la tablet (requiere cuenta Expo y subir el cliente React Native).

## Uso de la PWA HUD
- Abre `/` en el servidor; la HUD leerá datos de `/profile/demo`, `/daily-summary/demo` y `/macro-plan?user_id=demo` si existen.
- Registra un usuario real con `/register_user` (user_id por ejemplo: tu correo o 'demo').



# Calorias AI - Expo Go Project

## Uso en tablet
1. Instala **Expo Go** en tu tablet (Play Store / App Store).
2. En la misma red Wi-Fi que tu tablet, ejecuta tu backend FastAPI en tu PC:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
3. Abre el proyecto Expo Go en tu tablet:
   ```bash
   npm install
   npm start
   ```
4. Escanea el QR que aparece en la pantalla con **Expo Go**.
5. La app se conecta al backend y muestra HUD negro/rojo con calorías y macros.

## Generar APK
1. Crea cuenta en [Expo](https://expo.dev/) y sigue sus pasos para **EAS Build**.
2. Ejecuta:
   ```bash
   eas build -p android --profile production
   ```
   Expo generará APK instalable en tu tablet.

## Nota
- El color predominante es negro (#000) y los textos y botones son rojos (#ff2d55).
- Editable y escalable: puedes añadir nuevas pantallas, alimentos y funcionalidades.

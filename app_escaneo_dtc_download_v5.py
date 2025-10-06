# -*- coding: utf-8 -*-
# 🧰 Asistente de Escaneo — Base DTC Motor (P0001–P0999) — Descarga directa de PDF (v5)
# Cambios v5:
# - Fondo blanco eliminado globalmente (background transparente forzado).
# - Tarjetas y panel translúcido SIN borde (solo blur + sombra).
# - Botón WhatsApp con pulsación cada 2s.
#
# Ejecutar:
#   python app_escaneo_dtc_download_v5.py

from pywebio import start_server
from pywebio.output import (
    put_markdown, put_html, put_text, put_button, use_scope,
    put_row, put_table, popup, close_popup, toast, put_file
)
from pywebio.input import input, input_group, TEXT
from pywebio.session import set_env, run_js
import re
from datetime import datetime

APP_TITLE = "Asistente de Escaneo — Base DTC Motor (P0001–P0999)"
BRAND = "Si no tenes DTC solicita un escaneo en las redes!"

UNSPLASH_ID = "Lxl-K_R_QPc"
UNSPLASH_MAIN = f"https://unsplash.com/photos/{UNSPLASH_ID}/download?force=true&w=1920"

# --- Links redes (actualizados) ---
IG_URL = "https://www.instagram.com/cesar.check.engine?igsh=MTk1NHIwbWVkbmNqOA=="
FB_URL = "https://www.facebook.com/share/17DnSCk7Fu/"
WA_URL = "https://wa.me/5491172379474?text=Hola!%20Quiero%20un%20escaneo%20vehicular."

# =================== THEME ===================
def setup_theme_and_social():
    put_html(f"""
    <style>
      html, body {{
        height: 100%;
        margin: 0;
        background:
          radial-gradient(ellipse at center, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.78) 100%),
          url('{UNSPLASH_MAIN}') no-repeat center center fixed;
        background-size: cover;
        color: #fff;
        font-family: 'Segoe UI', Roboto, Arial, sans-serif;
      }}
      /* 🔳 Forzar transparencia global para eliminar fondo blanco residual */
      * {{
        background-color: transparent !important;
      }}
      /* Panel principal translúcido (sin borde) */
      .pywebio-content {{
        max-width: 920px;
        margin: 6vh auto 16vh;
        background: rgba(25,25,25,0.45);
        backdrop-filter: blur(16px) saturate(160%);
        -webkit-backdrop-filter: blur(16px) saturate(160%);
        border-radius: 22px;
        padding: 28px;
        text-align: left;
        box-shadow: 0 10px 36px rgba(0,0,0,0.65);
      }}
      h1, h2, h3, p {{ text-shadow: 0 2px 8px rgba(0,0,0,0.85); }}
      .chip {{
        display:inline-block; padding:6px 10px; border-radius:999px;
        margin:2px 6px 2px 0; font-size:.9rem;
        background: rgba(255,255,255,0.08);
      }}
      .chip b{{color:#fff}}

      /* Tarjeta translúcida para cada resultado/segmento (sin borde) */
      .card {{
        background: rgba(25,25,25,0.45);
        backdrop-filter: blur(12px) saturate(160%);
        -webkit-backdrop-filter: blur(12px) saturate(160%);
        border-radius: 16px;
        padding: 14px 16px;
        margin: 10px 0 14px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.35);
      }}
      .card ul, .card ol {{ margin: 6px 0 0 18px; }}
      .card b {{ color: #fff; }}

      /* --- Barra IG/FB (se mantiene sin blur) --- */
      .social-bar {{
        position: fixed;
        left: 50%;
        transform: translateX(-50%);
        bottom: max(10px, env(safe-area-inset-bottom));
        display: flex;
        gap: 8px;
        padding: 8px 10px;
        background: rgba(0,0,0,0.20);
        border-radius: 999px;
        z-index: 998;
        border: 1px solid rgba(255,255,255,0.18);
      }}
      .social-bar a {{
        display: inline-flex; align-items: center; gap: 6px;
        text-decoration: none; color: #fff;
        padding: 6px 10px; border-radius: 999px;
        font-size: 0.85rem; font-weight: 600;
        transition: transform .15s ease;
      }}
      .social-bar a:hover {{ transform: scale(1.08); }}
      .ig {{ background: #E1306C; }}
      .fb {{ background: #1877F2; }}
      .social-bar svg {{ width: 16px; height: 16px; fill: white; }}

      /* --- Botón flotante WhatsApp con pulsación cada 2s --- */
      .wa-fab {{
        position: fixed; right: 18px;
        bottom: max(18px, calc(env(safe-area-inset-bottom) + 18px));
        width: 52px; height: 52px; border-radius: 50%;
        background-color: #25D366 !important;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 10px 24px rgba(0,0,0,0.5); z-index: 9999;
        text-decoration: none; border: 2px solid rgba(255,255,255,0.25);
      }}
      .wa-fab svg {{ width: 24px; height: 24px; fill: #fff; }}
      @keyframes wa-pulse {{
        0% {{ transform: scale(1); box-shadow: 0 10px 24px rgba(0,0,0,0.5);}}
        50% {{ transform: scale(1.12); box-shadow: 0 14px 28px rgba(0,0,0,0.55), 0 0 0 10px rgba(37,211,102,0.25);}}
        100% {{ transform: scale(1); box-shadow: 0 10px 24px rgba(0,0,0,0.5);}}
      }}
      .wa-fab.pulse {{ animation: wa-pulse 2s ease-in-out infinite; }}

      @media (max-width: 520px) {{
        .pywebio-content {{ margin: 4vh 10px 16vh; padding: 22px; }}
      }}
    </style>

    <!-- Barra social -->
    <div class="social-bar">
      <a class="ig" href="{IG_URL}" target="_blank" rel="noopener" aria-label="Instagram">
        <svg viewBox="0 0 448 512"><path d="M224,202.66A53.34,53.34,0,1,0,277.34,256,53.38,53.38,0,0,0,224,202.66Zm124.71-41.37a31.11,31.11,0,1,0,31.11,31.11A31.11,31.11,0,0,0,348.71,161.29ZM398.8,80A93.2,93.2,0,0,0,368,64.47C335.86,53.67,265.71,48,224,48S112.14,53.67,80,64.47A93.2,93.2,0,0,0,49.2,80C36.91,92.28,24.63,114,21.2,148.06,17.29,188,16,233.38,16,256s1.29,68,5.2,107.94C24.63,398,36.91,419.72,49.2,432A93.2,93.2,0,0,0,80,447.53C112.14,458.33,182.29,464,224,464s112.14-5.67,144-16.47A93.2,93.2,0,0,0,398.8,432c12.29-12.28,24.57-34,28-68.06C429.71,324,431,278.62,431,256s-1.29,68-4.2-107.94C423.37,114,411.09,92.28,398.8,80ZM224,338.67A82.67,82.67,0,1,1,306.67,256,82.76,82.76,0,0,1,224,338.67Z"/></svg>
        Instagram
      </a>
      <a class="fb" href="{FB_URL}" target="_blank" rel="noopener" aria-label="Facebook">
        <svg viewBox="0 0 320 512"><path d="M279.14 288l14.22-92.66h-88.91V128c0-25.35 12.42-50.06 52.24-50.06H295V6.26S273.91 0 252.36 0c-73.22 0-121.07 44.38-121.07 124.72V195.3H56.89V288h74.4v224h92.66V288z"/></svg>
        Facebook
      </a>
    </div>

    <!-- Botón flotante WhatsApp con pulsación continua -->
    <a class="wa-fab pulse" id="waFab" href="{WA_URL}" target="_blank" rel="noopener" aria-label="WhatsApp">
      <svg viewBox="0 0 448 512">
        <path d="M380.9 97.1C339-7.8 241.4-30.2 160 23.2 78.6 76.7 46.9 176 80.5 261.9l-19.4 70.3 72.1-18.9c47.6 25.6 104.1 27.9 152.2 6.3 88.8-41.2 127.5-145.1 95.5-222.5zM224 367.8c-26.8 0-52.9-6.6-76.2-19.1l-5.4-3-42.8 11.2 11.4-41.5-3.5-5.7C83.1 275.2 74.9 246 74.9 216c0-81.4 66.4-147.8 147.8-147.8s147.8 66.4 147.8 147.8S305.4 367.8 224 367.8zM309.5 282c-4.1-2-24.3-12-28.1-13.4-3.8-1.4-6.6-2-9.4 2-2.8 3.9-10.8 13.4-13.3 16.1-2.5 2.8-4.9 3-9 1.1-4.1-2-17.1-6.3-32.5-20.1-12-10.7-20.1-23.9-22.5-28-2.3-4.1-.2-6.3 1.7-8.2 1.7-1.7 3.9-4.5 5.8-6.7 1.9-2.2 2.5-3.9 3.8-6.6 1.2-2.8 .6-5.2-.3-7.3-.9-2-8.3-20-11.4-27.3-3-7.3-6.1-6.3-8.4-6.4-2.1-.1-4.6-.1-7.1-.1-2.5 0-6.6 .9-10 4.5-3.4 3.7-13.1 12.8-13.1 31.2s13.4 36.2 15.3 38.7c1.9 2.5 26.3 40.2 63.9 56.3 8.9 3.8 15.8 6.1 21.2 7.8 8.9 2.8 17 2.4 23.4 1.5 7.1-1 24.3-9.9 27.8-19.5 3.5-9.6 3.5-17.9 2.4-19.5-1.1-1.5-3.9-2.5-8.1-4.5z"/>
      </svg>
    </a>
    """)

# =================== LÓGICA DTC (igual a v4) ===================
SUBS_DESC = {
    "FUEL_PRESSURE": "Sistema de combustible/mezcla: presión de riel, bomba, regulador y correlaciones MAF/MAP.",
    "MAF": "Medición de flujo de aire (MAF) y correlaciones de mezcla.",
    "MAP": "Presión absoluta múltiple (MAP) y barométrica (BARO).",
    "ECT/IAT": "Temperaturas de motor y admisión (sensores NTC).",
    "TPS/APP/ETC": "Posición de mariposa, pedal y cuerpo electrónico de aceleración.",
    "INJECTOR": "Control de inyectores, alimentación y balance.",
    "MISFIRE": "Encendido, misfires, knock y sincronismo.",
    "CKP/CMP": "Sensores de posición cigüeñal/árbol de levas.",
    "O2_HEATER": "Circuitos de calefactor de sondas lambda.",
    "O2_SENSOR": "Señal de sondas (rich/lean, respuesta).",
    "CAT": "Eficiencia del catalizador y contrapresión.",
    "EVAP": "Control de vapores de combustible y estanqueidad.",
    "EGR": "Recirculación de gases y control de emisiones.",
    "IDLE/VSS": "Ralentí, velocidad y cargas auxiliares.",
    "ECU/REF": "ECU, comunicación y referencias de 5 V.",
    "TRANSMISION": "Códigos TCM/transmisión (referencia — fuera del alcance motor).",
    "GENERAL": "Powertrain (general)."
}

def diag_plantilla(subsistema, extra=""):
    base = {
        "MAF": [
            "Verificar conector, terminales y masa del sensor MAF.",
            "Comprobar referencia 5 V (KOEO).",
            "Medir señal MAF: 0.8–1.2 V en ralentí; sube hasta 4.0–4.5 V a 4.000 rpm.",
            "Observar g/s en vivo: 2–7 g/s en ralentí (1.6–2.0 L), proporcional a cilindrada.",
            "Inspeccionar fugas de admisión antes del MAF y filtro obstruido.",
            "Limpiar con limpiador específico (no tocar hilo).",
            "Probar continuidad hasta ECU si la señal es plana o errática."
        ],
        "MAP": [
            "Revisar manguera de vacío (si aplica) y conector.",
            "Confirmar 5 V de referencia (KOEO).",
            "Medir señal MAP: KOEO ≈ 4.5–5.0 V; ralentí ≈ 0.9–1.5 V.",
            "Comparar MAP–MAF: incoherencia sugiere fuga o sensor defectuoso.",
            "Verificar vacío motor: 18–22 inHg aprox. en ralentí."
        ],
        "ECT/IAT": [
            "Medir resistencia NTC: 20°C ≈ 2–3 kΩ; 80°C ≈ 300–500 Ω.",
            "Confirmar 5 V y masa.",
            "Comparar ECT con IAT en frío (similares, <3°C).",
            "Revisar continuidad y conectores sulfatados si hay saltos en la lectura."
        ],
        "O2_HEATER": [
            "Medir resistencia del calefactor: 8–14 Ω.",
            "Verificar 12 V al calefactor (KOEO) y masa del circuito.",
            "Controlar fusible del circuito HO2S Heater."
        ],
        "O2_SENSOR": [
            "Observar sonda estrecha: 0.10–0.90 V oscilante en lazo cerrado.",
            "Si fija pobre/rica, confirmar con test de propano y descartar fugas.",
            "Chequear respuesta: forzar enriquecimiento y observar cambio rápido."
        ],
        "CAT": [
            "Comparar O₂ upstream vs downstream (downstream debe oscilar menos).",
            "Descartar misfire/mezcla rica previa antes de reemplazar catalizador.",
            "Medir contrapresión de escape si hay sospecha de obstrucción."
        ],
        "EVAP": [
            "Inspeccionar tapa de combustible (sellado correcto).",
            "Realizar test de humo (líneas, canister, válvulas).",
            "Revisar válvula de purga: trabada abierta → mezcla pobre inestable."
        ],
        "EGR": [
            "Inspeccionar carbón en conductos y válvula EGR.",
            "Comandar EGR con escáner: apertura excesiva casi apaga en ralentí.",
            "Verificar que el sensor de posición EGR refleje el comando."
        ],
        "FUEL_PRESSURE": [
            "Medir presión con manómetro: comparar con especificación (ej.: 3.0–3.5 bar multipunto).",
            "Probar caudal de bomba y caída de voltaje en alimentación.",
            "Controlar regulador de presión y retorno obstruido."
        ],
        "INJECTOR": [
            "Comprobar pulso con lámpara noid.",
            "Medir resistencia de bobina: 12–16 Ω (alta impedancia).",
            "Realizar balance de inyectores (caída de presión similar)."
        ],
        "MISFIRE": [
            "Identificar cilindro; intercambiar bobina/bujía para ver si el fallo se traslada.",
            "Realizar prueba de compresión/fugas (variación ≤ ±10%).",
            "Verificar mezcla: fugas de vacío, MAF/MAP y presión de combustible."
        ],
        "CKP/CMP": [
            "Inspeccionar conector y presencia de limaduras en sensor CKP.",
            "Medir: inductivo 500–1.500 Ω; Hall 5 V y señal cuadrada.",
            "Ajustar distancia al reluctor y confirmar correlación CKP–CMP."
        ],
        "TPS/APP/ETC": [
            "Verificar 5 V de referencia y masa.",
            "Observar TPS: barrido 0.5 V → 4.5 V sin saltos.",
            "Realizar aprendizaje/baseline del cuerpo electrónico; limpiar si hay suciedad."
        ],
        "IDLE/VSS": [
            "Revisar IAC/ETC: pasos o % coherentes con velocidad de ralentí.",
            "Detectar fugas de vacío (mangueras, PCV) si hay rpm elevadas.",
            "Confirmar VSS coherente con velocidad real."
        ],
        "ECU/REF": [
            "Comprobar líneas de 5 V comunes (un sensor en corto tumba el bus).",
            "Verificar relé principal y masas de ECU (caída < 0.2 V).",
            "Comprobar continuidad CAN y terminaciones."
        ]
    }
    pasos = base.get(subsistema, ["Inspección visual y eléctrica básica.",
                                  "Verificar 5 V, masa y continuidad.",
                                  "Datos en vivo y correlaciones.",
                                  "Pruebas de carga."])
    if extra:
        pasos.append(extra)
    return pasos

# Recomendaciones por subsistema
def recomendaciones(subsistema):
    base = {
        "MAF": [
            "Limpiar MAF con aerosol específico; **no** tocar el hilo.",
            "Comparar g/s con cilindrada y RPM; **descartar** fugas antes del MAF.",
            "Medir caída de voltaje en masa y 5 V; **reparar** falsos contactos."
        ],
        "MAP": [
            "Controlar manguera y puertos de vacío; **reemplazar** si están cuarteados.",
            "Comparar MAP con BARO al KOEO; **calibrar** si difiere mucho.",
            "Testear con bomba de vacío (si aplica) y **observar** la curva de salida."
        ],
        "ECT/IAT": [
            "Medir resistencia en frío y caliente; **sustituir** si queda fuera de tabla.",
            "Comparar ECT vs IAT al arranque; **investigar** diferencias >3°C.",
            "Controlar estado del termostato si la temperatura es errática."
        ],
        "O2_HEATER": [
            "Verificar fusibles y **reparar** masa floja del calefactor.",
            "Medir resistencia; **reemplazar** sonda si está abierta o en corto."
        ],
        "O2_SENSOR": [
            "Forzar enriquecimiento y **confirmar** respuesta rápida.",
            "Inspeccionar **fugas de escape** antes del sensor; **sellar** juntas.",
            "Revisar masas de motor y **limpiar** puntos de unión."
        ],
        "CAT": [
            "Analizar causas **upstream** (misfire/mezcla) antes de **reemplazar** el catalizador.",
            "Medir contrapresión; **confirmar** obstrucción."
        ],
        "EVAP": [
            "**Testear** estanqueidad con humo; **reparar** mangueras y válvulas.",
            "Verificar tapa de combustible; **sustituir** si no sella."
        ],
        "EGR": [
            "Descarbonizar conductos y **verificar** asiento de la válvula.",
            "Usar el escáner para **comandar** y **evaluar** la respuesta del motor."
        ],
        "FUEL_PRESSURE": [
            "Medir presión estática y dinámica; **comparar** con especificación.",
            "Realizar prueba de caudal y **verificar** caída de voltaje en cables."
        ],
        "INJECTOR": [
            "**Ultrasonido** y limpieza si hay desbalance.",
            "Medir resistencia y **sustituir** el que difiera claramente."
        ],
        "MISFIRE": [
            "**Intercambiar** componentes (bobina/bujía) para aislar el cilindro.",
            "**Comprobar** compresión y fugas de cilindro."
        ],
        "CKP/CMP": [
            "**Ajustar** luz al reluctor y **verificar** alineación de marcas.",
            "**Observar** señal con osciloscopio si está disponible."
        ],
        "TPS/APP/ETC": [
            "**Realizar** aprendizaje del cuerpo; **limpiar** mariposa si pega.",
            "**Verificar** correlación APP1/APP2 y **reparar** cableado si hay salto."
        ],
        "IDLE/VSS": [
            "**Sellar** fugas de vacío y **comprobar** PCV.",
            "**Revisar** acumulación de carbón en cuerpo/IAC."
        ],
        "ECU/REF": [
            "**Aislar** sensores en corto en la línea de 5 V desconectándolos uno a uno.",
            "**Verificar** relé principal y **limpiar** masas de ECU."
        ],
        "GENERAL": [
            "**Registrar** datos freeze frame y **comparar** con síntomas del cliente.",
            "**Actualizar** software ECU si existe boletín aplicable."
        ],
        "TRANSMISION": [
            "**Escanear** TCM y **corroborar** señales de par desde ECU motor."
        ]
    }
    return base.get(subsistema, base["GENERAL"])

def info_codigo(num):
    if   1 <= num <= 4:
        return ("FUEL_PRESSURE", "Regulador de volumen de combustible — circuito/función", True)
    if  30 <= num <= 39:
        return ("O2_HEATER", "Calentador de sensor O₂ — circuito (Bancos/Sensores)", True)
    if 100 <= num <= 104: return ("MAF", "Sensor MAF — circuito/rango/funcionamiento", True)
    if 105 <= num <= 109: return ("MAP", "Sensor MAP/Baro — circuito/rango/funcionamiento", True)
    if 110 <= num <= 114: return ("ECT/IAT", "Sensor IAT — circuito/rango", True)
    if 115 <= num <= 119: return ("ECT/IAT", "Sensor ECT — circuito/rango", True)
    if 120 <= num <= 129: return ("TPS/APP/ETC", "Posición de acelerador — circuito/rango", True)
    if 130 <= num <= 169: return ("O2_SENSOR", "Sensor de oxígeno — circuito/respuesta", True)
    if 170 <= num <= 179: return ("FUEL_PRESSURE", "Trim de combustible fuera de rango (B1/B2)", True)
    if 171 == num:        return ("MAF", "Mezcla pobre — Banco 1 (P0171)", True)
    if 172 == num:        return ("MAF", "Mezcla rica — Banco 1 (P0172)", True)
    if 174 == num:        return ("MAF", "Mezcla pobre — Banco 2 (P0174)", True)
    if 175 == num:        return ("MAF", "Mezcla rica — Banco 2 (P0175)", True)
    if 180 <= num <= 189: return ("FUEL_PRESSURE", "Temperatura de combustible / relacionados", True)
    if 190 <= num <= 199: return ("FUEL_PRESSURE", "Sensor de presión de riel — circuito/rango", True)
    if 200 <= num <= 219: return ("INJECTOR", "Circuito/control de inyectores", True)
    if 230 <= num <= 239: return ("FUEL_PRESSURE", "Bomba de combustible — control/circuito", True)
    if 240 <= num <= 249: return ("FUEL_PRESSURE", "EVAP — purga/ventilación — circuito", True)
    if 250 <= num <= 259: return ("FUEL_PRESSURE", "Relación A/F — restricción/desempeño", True)
    if 260 <= num <= 269: return ("TPS/APP/ETC", "Actuador aceleración (ETC) — desempeño", True)
    if 280 <= num <= 289: return ("FUEL_PRESSURE", "Presión/boost — desempeño", True)
    if 290 <= num <= 299: return ("FUEL_PRESSURE", "Under/overboost", True)
    if 300 == num:        return ("MISFIRE", "Misfire aleatorio/múltiple (P0300)", True)
    if 301 <= num <= 339: return ("MISFIRE", "Misfire cilindro específico", True)
    if 325 <= num <= 329: return ("MISFIRE", "Sensor de detonación (Knock) — circuito", True)
    if 335 <= num <= 339: return ("CKP/CMP", "Sensor CKP — circuito/posición", True)
    if 340 <= num <= 349: return ("CKP/CMP", "Sensor CMP — circuito/posición", True)
    if 350 <= num <= 369: return ("MISFIRE", "Bobinas/primario-secundario — circuito", True)
    if 400 == num:        return ("EGR", "EGR — flujo insuficiente", True)
    if 401 == num:        return ("EGR", "EGR — flujo insuficiente detectado", True)
    if 402 == num:        return ("EGR", "EGR — flujo excesivo", True)
    if 410 <= num <= 419: return ("EGR", "Aire secundario — circuito/desempeño", True)
    if 420 == num:        return ("CAT", "Catalizador por debajo del umbral (B1)", True)
    if 430 == num:        return ("CAT", "Catalizador por debajo del umbral (B2)", True)
    if 440 <= num <= 459: return ("EVAP", "EVAP — fugas/ventilación/purga", True)
    if 460 <= num <= 469: return ("FUEL_PRESSURE", "Sensor de nivel de combustible — circuito/alto/bajo", True)
    if 480 <= num <= 489: return ("EGR", "Ventilador/sistema emisiones", True)
    if 500 == num:        return ("IDLE/VSS", "VSS — circuito", True)
    if 505 == num:        return ("IDLE/VSS", "IAC — funcionamiento", True)
    if 520 <= num <= 529: return ("IDLE/VSS", "Presión de aceite motor / sensores", True)
    if 550 <= num <= 559: return ("IDLE/VSS", "Dirección asistida / carga — impacto en ralentí", True)
    if 560 <= num <= 569: return ("ECU/REF", "Sistema de voltaje — alto/bajo/irregular", True)
    if 600 <= num <= 609: return ("ECU/REF", "Comunicación serie/Link — fallas", True)
    if 610 <= num <= 619: return ("ECU/REF", "Control de vehículo — checksum/programación", True)
    if 620 <= num <= 629: return ("ECU/REF", "Control actuadores (regulación/velocidad)", True)
    if 650 == num:        return ("ECU/REF", "Control de lámpara MIL — circuito", True)
    if 680 <= num <= 689: return ("ECU/REF", "Referencia 5 V — fallas (línea común)", True)
    if 700 <= num <= 999: return ("TRANSMISION", "Código de transmisión/TCM (referencia de par motor)", False)
    if   1 <= num <= 199:  return ("FUEL_PRESSURE", "Medición de aire/combustible — circuito/rango", True)
    elif 200 <= num <= 299:return ("INJECTOR", "Inyección/boost — circuito/desempeño", True)
    elif 300 <= num <= 399:return ("MISFIRE", "Encendido/sincronismo — fallas", True)
    elif 400 <= num <= 499:return ("EGR", "Emisiones (EGR/EVAP/CAT) — desempeño", True)
    elif 500 <= num <= 599:return ("IDLE/VSS", "Ralentí/velocidad/eléctrico — desempeño", True)
    elif 600 <= num <= 699:return ("ECU/REF", "ECU/Comunicación/Referencias — fallas", True)
    return ("GENERAL", "Powertrain (general)", True)

def tips_especiales(num):
    tips = []
    if num in (171, 174):
        tips.append("Lean crónico: fugas de vacío, PCV trabada, MAF sucio, purga EVAP abierta.")
    if num in (172, 175):
        tips.append("Rica crónica: presión de combustible alta, inyector trabado, retorno obstruido.")
    if num in (420, 430):
        tips.append("Catalizador: revisar misfire y mezcla previa; un fallo upstream destruye el catalizador.")
    if num == 300:
        tips.append("Misfire aleatorio: alimentación bobinas, masas comunes y vibraciones/cables.")
    if num in (335, 340):
        tips.append("Sincronismo: chequear correlación CKP–CMP (grados) y estado de correa/cadena.")
    return tips

def parse_codes(text):
    raw = re.split(r'[,\s;]+', text.strip().upper())
    codes = []
    for token in raw:
        if not token:
            continue
        if token.startswith('P'):
            token = token[1:]
        if not token.isdigit():
            continue
        n = int(token)
        if 1 <= n <= 999:
            codes.append(n)
    seen = set(); norm = []
    for n in codes:
        if n not in seen:
            norm.append(n); seen.add(n)
    return norm

def render_entry(num):
    codigo = f"P{num:04d}"
    subsistema, desc, es_motor = info_codigo(num)

    header = f"<div class='chip'><b>{codigo}</b> — {desc}</div>"
    sistema = f"<div class='chip'>Sistema: {SUBS_DESC.get(subsistema, subsistema)}</div>"

    bloques = [f"<div class='card'>{header}<br/>{sistema}<div style='margin:6px 0'></div>"]

    if not es_motor:
        cuerpo = ["<ul>",
                  "<li>Este código corresponde a <b>Transmisión (TCM)</b>.</li>",
                  "<li>Revisar comunicación con TCM y estrategias de par motor.</li>",
                  "</ul>"]
        bloques.append("".join(cuerpo))
    else:
        pasos = diag_plantilla(subsistema)
        extra = tips_especiales(num)
        cuerpo = ["<b>Diagnóstico (nivel taller)</b><ol>"] + [f"<li>{p}</li>" for p in pasos] + ["</ol>"]
        if extra:
            cuerpo += ["<p><i>Notas:</i> " + " ".join(extra) + "</p>"]
        bloques.append("".join(cuerpo))

        recs = recomendaciones(subsistema)
        bloques.append("<b>🧾 Recomendaciones</b><ul>" + "".join([f"<li>{r}</li>" for r in recs]) + "</ul>")

    bloques.append("</div>")
    return "".join(bloques)

# =================== EXPORT A PDF (descarga inmediata) ===================
def export_pdf_download(nums):
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A5
        from reportlab.lib import colors
        from io import BytesIO

        buff = BytesIO()

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="H", parent=styles["Heading1"], fontSize=15.5, leading=17, alignment=TA_LEFT))
        styles.add(ParagraphStyle(name="Sub", parent=styles["Normal"], fontSize=9.6, leading=12))
        styles.add(ParagraphStyle(name="N", parent=styles["Normal"], fontSize=9.6, leading=12))

        def on_page(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.grey)
            canvas.drawString(10*mm, A5[1]-10*mm+2, BRAND[:110])
            canvas.drawRightString(A5[0]-10*mm, 6*mm, f"Pág. {doc.page}")
            canvas.restoreState()

        doc = SimpleDocTemplate(
            buff, pagesize=A5,
            leftMargin=10*mm, rightMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm,
            title="Informe de Diagnóstico DTC — Motor"
        )
        story = []
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        story.append(Paragraph("Informe de Diagnóstico DTC — Motor", styles["H"]))
        story.append(Paragraph(f"{BRAND}", styles["Sub"]))
        story.append(Paragraph(f"Fecha: {fecha}", styles["Sub"]))
        story.append(Spacer(1, 4*mm))

        for n in nums:
            story.append(Paragraph(render_entry(n), styles["N"]))
            story.append(Spacer(1, 2*mm))

        doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

        fname = f"Informe_DTC_{datetime.now().strftime('%Y-%m-%d')}.pdf"
        data = buff.getvalue()
        buff.close()

        put_file(fname, data, label="⬇️ Descargar PDF")
    except Exception as e:
        popup("Exportar a PDF", [
            put_markdown("No se pudo generar el PDF."),
            put_text(str(e)),
            put_markdown("Instalá reportlab así: `pip install reportlab`"),
            put_button("Cerrar", onclick=close_popup)
        ])

# =================== APP ===================
def home_header():
    put_markdown(f"# 🧰 {APP_TITLE}")
    put_markdown("> Ingresá uno o varios códigos (ej.: `P0171, P0300`) y obtené el diagnóstico de taller.")
    put_markdown(f"_**{BRAND}**_")

def buscar_por_codigo():
    data = input_group("Buscar por código DTC", [
        input(label="Códigos (coma o espacio):", name="codes", type=TEXT, placeholder="P0171 P0300 P0420"),
    ])
    nums = parse_codes(data["codes"] or "")
    if not nums:
        toast("No se reconocieron códigos. Probá con P0171, P0300, etc.", color="warn")
        return
    with use_scope("result", clear=True):
        rows = [[put_html(render_entry(n))] for n in nums]
        put_table(rows)
        put_row([
            put_button("📄 Exportar PDF (descargar)", onclick=lambda: export_pdf_download(nums)),
            put_button("🔁 Nueva búsqueda", onclick=lambda: run_js("location.reload()"))
        ], size="auto")

def app():
    setup_theme_and_social()
    set_env(title=APP_TITLE)
    home_header()
    put_row([
        put_button("🔎 Buscar por código", onclick=buscar_por_codigo)
    ], size="auto")
    put_text("© 2025 César Mastrocola — Check Engine Escaneo Vehicular")

if __name__ == "__main__":
    start_server(app, host="0.0.0.0", port=8080, debug=True, auto_open_webbrowser=False, show_server_info=False)

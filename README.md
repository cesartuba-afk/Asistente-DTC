# Asistente de Escaneo — Base DTC Motor (P0001–P0999)

App PyWebIO con descarga directa de PDF, pensada para ejecutarse en Render.com como **Web Service**.

---

## ✅ Requisitos
- Cuenta en [Render](https://render.com)
- Repositorio con estos archivos:
  - `app_escaneo_dtc_download_v5.py` (la app)
  - `requirements.txt`
  - `Procfile`
  - `README.md` (este archivo)

> **Nota importante:** En Render, la app **debe** escuchar el **puerto** indicado por la variable de entorno `PORT` y el **host** `0.0.0.0`.

---

## 🔧 Ajuste mínimo en el código (PORT dinámico)
Abrí `app_escaneo_dtc_download_v5.py` y reemplazá la línea de inicio del servidor por esto (o confirmá que ya esté así):

```python
import os
# ...
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    start_server(app, host="0.0.0.0", port=port, debug=True, auto_open_webbrowser=False, show_server_info=False)
```

Con esto la app se adapta al puerto que Render le asigna.

---

## 🚀 Deploy en Render (paso a paso)

1. Subí este proyecto a un repositorio (GitHub, GitLab o Bitbucket).
2. En Render, creá un **New + → Web Service**.
3. Conectá tu repo y elegí:
   - **Runtime**: Python 3.11 (o 3.10/3.12)
   - **Build Command**: *(vacío)* — Render instala automáticamente desde `requirements.txt`.
   - **Start Command**: `python app_escaneo_dtc_download_v5.py`  
     > Alternativa: Render reconoce `Procfile` con: `web: python app_escaneo_dtc_download_v5.py`.
4. Variables de entorno (opcional): no se requieren. La variable `PORT` la maneja Render.
5. Click en **Create Web Service** y esperá a que construya e inicie.

Cuando el servicio quede **Live**, Render mostrará la **URL pública**. Abrila y usá la app:
- Buscá DTC (ej. `P0171 P0300`).
- Exportá PDF con **⬇️ Descargar PDF**.

---

## 📦 Dependencias
Se instalan automáticamente desde `requirements.txt`:
- `pywebio`: servidor web mínimo y UI reactiva.
- `reportlab`: generación del PDF en memoria.

> Si preferís fijar versiones, podés usar por ejemplo:
> ```txt
> pywebio==1.8.3
> reportlab==4.*
> ```

---

## 📝 Notas operativas
- El **almacenamiento** en Render es efímero: los PDF se **generan en memoria** y se **descargan** al instante, no quedan guardados en el servidor.
- El **botón de WhatsApp** pulsa cada 2 s y abre tu enlace `wa.me`.
- La **barra de redes** (IG/FB) se mantiene como estaba (sin blur).
- Toda la UI es **translúcida** (cristal) y sin bordes visibles.

---

## 🆘 Problemas comunes

- **La app no abre en Render / “Listening on wrong port”**
  Asegurate de haber aplicado el bloque `os.environ['PORT']` en el `start_server` y `host="0.0.0.0"`.

- **“ModuleNotFoundError: pywebio/reportlab”**  
  Confirmá que `requirements.txt` esté en la raíz del repo.

- **Descarga de PDF no aparece**  
  Verificá que `reportlab` se haya instalado y que no existan bloqueos del navegador para descargas automáticas.

---

## 🔒 Seguridad
- La app no pide credenciales ni guarda datos.
- Si deseás proteger el acceso, podés **restringir por IP** con reglas de Render o incorporar una clave simple en el `input_group`.

---

## 📱 App móvil Flutter para escanear con ELM327 v1.5

En la carpeta [`elm327_scanner`](elm327_scanner) se incluye una app Flutter de ejemplo lista para conectarse a un adaptador **ELM327 v1.5** por Bluetooth clásico.

### Características principales

- Descubrimiento de dispositivos Bluetooth cercanos y control del estado del adaptador.
- Emparejamiento con el módulo ELM327 y envío de comandos AT comunes para inicializarlo.
- Paneles en tiempo real que muestran los sensores OBD-II disponibles actualizados cinco veces por segundo.
- Botones para leer información del vehículo (VIN, PIDs disponibles) y obtener o borrar códigos de falla (DTC).
- Manejo básico de estados, errores y respuestas del OBD-II usando `provider`.

### Pasos para ejecutar

1. **Instalá Flutter** siguiendo la [documentación oficial](https://docs.flutter.dev/get-started/install) y asegurate de tener un dispositivo Android con Bluetooth clásico.
2. Desde la raíz del repositorio, instalá las dependencias:

   ```bash
   cd elm327_scanner
   flutter pub get
   ```

3. Conecta tu dispositivo físico (o usa un emulador con soporte Bluetooth) y ejecutá la app:

   ```bash
   flutter run
   ```

4. Emparejá el ELM327 desde la app y utilizá los botones para consultar o borrar DTC.

> **Nota:** El paquete [`flutter_bluetooth_serial`](https://pub.dev/packages/flutter_bluetooth_serial) requiere permisos adicionales en Android. Revisa y ajusta los archivos de configuración (por ejemplo `android/app/src/main/AndroidManifest.xml`) según tu caso de uso antes de distribuir la app.
>
> Para ejecutar la app desde un navegador (por ejemplo `flutter run -d chrome`) primero habilitá el soporte web en tu instalación de Flutter y regenerá los archivos de plataforma:
>
> ```bash
> flutter config --enable-web
> flutter create . --platforms=web
> ```
>
> Sin estos pasos, la compilación para web mostrará un error indicando que el proyecto no está configurado para esa plataforma.

---

## 📄 Licencia
Uso interno para taller de diagnóstico. Ajustá y redistribuí según tus necesidades.

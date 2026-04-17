# Publicar la app para la clase (Streamlit Community Cloud)

Este proyecto es una aplicacion **Streamlit** en Python. Para que los estudiantes **solo abran un enlace** en el navegador (sin instalar Python), el docente la publica una vez en **Streamlit Community Cloud** (gratuito con cuenta de GitHub).

---

## Parte 1 — Lo que debe hacer el docente (una sola vez)

### 1. Crear un repositorio en GitHub

1. Entre en [https://github.com/new](https://github.com/new) y cree un repositorio **publico** (por ejemplo `nash-mejor-respuesta`).
2. **Importante:** los archivos de esta carpeta deben quedar en la **raiz** del repositorio, es decir, en la raiz deben verse al menos:
   - `app.py`
   - `game_logic.py`
   - `requirements.txt`
   - (opcional) `.streamlit/config.toml`

   Puede copiar **todo el contenido** de la carpeta `nash_best_response_app` a la raiz del repo.

### 2. Subir el codigo desde su ordenador

En Terminal, dentro de la carpeta del proyecto (donde esta `app.py`):

```bash
git init
git add app.py game_logic.py requirements.txt .streamlit .gitignore
git add "README_PUBLICACION.md" "COMO_USAR_EN_OTRO_ORDENADOR.txt" 2>/dev/null || true
git commit -m "App Nash mejor respuesta para clase"
git branch -M main
git remote add origin https://github.com/SU_USUARIO/SU_REPO.git
git push -u origin main
```

(Ajuste la URL de `origin` a su repositorio real.)

Los archivos `NashBR Launcher.app`, `.command` y `.bat` **no hacen falta** en la nube; puede omitirlos del `git add` si prefiere un repo mas limpio.

### 3. Desplegar en Streamlit Community Cloud

1. Entre en [https://share.streamlit.io/](https://share.streamlit.io/) e inicie sesion con **GitHub**.
2. **Create app** (o New app).
3. Elija el **repositorio** y la rama **`main`**.
4. **Main file path:** `app.py`
5. **App URL:** dejara una direccion del tipo `https://SU-APP.streamlit.app`
6. Pulse **Deploy** y espere a que el estado pase a **Running**.

Si falla el despliegue, revise el **log**: casi siempre falta algun paquete en `requirements.txt` o la ruta de `app.py` no es la correcta.

### 4. Compartir con la clase

Envie por correo, LMS o chat **solo el enlace** `https://....streamlit.app` (y opcionalmente una frase: “Abran en Chrome o en el navegador que usen en clase”).

---

## Parte 2 — Lo que deben hacer los estudiantes

1. **Abrir el enlace** que les envio el profesor (debe empezar por `https://` y terminar en algo como `.streamlit.app`).
2. Usar un **navegador actualizado** (Chrome, Edge, Firefox o Safari).
3. **No necesitan** instalar Python ni descargar el proyecto si usted publico la app en la nube.
4. En la aplicacion pueden:
   - Leer la pesta?a **Teoria y derivacion**;
   - En **Matriz e interaccion**, cambiar los **pagos** en los recuadros, usar los **deslizadores** de `q` y `p`, y ver las **graficas** y los **equilibrios**.

Si la pagina va lenta o aparece “sleeping”, es limitacion del plan gratuito: vuelvan a abrir el enlace o esperen unos segundos.

---

## Si no usan la nube (ordenadores del aula con Python)

Entonces cada alumno o laboratorio necesita Python y dependencias; puede repartir la carpeta del proyecto y seguir `COMO_USAR_EN_OTRO_ORDENADOR.txt` o el lanzador `.bat` / `.command`.

---

## Enlaces utiles

- Streamlit Community Cloud: [https://streamlit.io/cloud](https://streamlit.io/cloud)
- Documentacion: [https://docs.streamlit.io/streamlit-community-cloud](https://docs.streamlit.io/streamlit-community-cloud)
- Crear repo en GitHub: [https://github.com/new](https://github.com/new)

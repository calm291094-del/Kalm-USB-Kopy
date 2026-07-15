# ⚔️ Kalm-USB-Kopy

<div align="center">
  <img src="https://raw.githubusercontent.com/klorenzo29/Kalm-USB-Kopy/kalm_icon.png" alt="Kalm-USB-Kopy Logo" width="200">
  <br>
  <strong>Sistema Avanzado de Gestión de Memorias USB</strong>
  <br>
  <em>Inspirado en Tensei Shitara Slime Datta Ken y Overlord</em>
</div>

---

## 📋 Tabla de Contenidos
- [Descripción](#-descripción)
- [Características Principales](#-características-principales)
- [Requisitos del Sistema](#-requisitos-del-sistema)
- [Instalación](#-instalación)
- [Guía de Uso](#-guía-de-uso)
- [Capturas de Pantalla](#-capturas-de-pantalla)
- [Configuración](#-configuración)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Contribuciones](#-contribuciones)
- [Licencia](#-licencia)
- [Contacto](#-contacto)

---

## 📝 Descripción

**Kalm-USB-Kopy** es una aplicación de escritorio diseñada para gestionar y controlar las copias de datos a memorias USB. Desarrollada específicamente para emprendedores que ofrecen servicios de copia de archivos, esta herramienta automatiza el proceso de registro, cálculo de precios y generación de informes.

### 🎯 ¿Para quién es?

- 📦 Emprendedores de servicios de copia de datos
- 🏪 Locales de cibercafés y centros de copiado
- 📚 Bibliotecas y centros educativos
- 💼 Profesionales que necesitan gestionar múltiples memorias USB

---

## ✨ Características Principales

### 🔮 Gestión Inteligente
- ✅ **Detección Automática**: Detecta automáticamente cuando conectas una memoria USB
- ✅ **Identificación de Memorias**: Reconoce cada memoria por su serial único
- ✅ **Asignación de Nombres**: Permite asignar nombres personalizados a cada memoria
- ✅ **Historial por Memoria**: Registro completo de todas las copias realizadas por cada memoria

### 💰 Control Financiero
- ✅ **Cálculo Automático**: Calcula automáticamente el precio basado en GB copiados
- ✅ **Precio Configurable**: Ajusta el precio por GB según tu mercado
- ✅ **Informes Diarios**: Genera informes detallados de ventas diarias
- ✅ **Estadísticas Avanzadas**: Análisis de tendencias y patrones de uso

### 🎨 Diseño y UX
- ✅ **Temas Personalizables**: Más de 15 temas disponibles (oscuro, claro, fantasia, etc.)
- ✅ **Notificaciones Windows**: Notificaciones emergentes al finalizar copias
- ✅ **Minimización a Bandeja**: Se minimiza a la bandeja del sistema como un antivirus
- ✅ **Icono Personalizado**: Logo moderno con la letra "K"

### 🛠️ Herramientas Avanzadas
- ✅ **Respaldos Automáticos**: Crea copias de seguridad de tu base de datos
- ✅ **Exportación de Datos**: Exporta historial y base de memorias a CSV/JSON
- ✅ **Análisis de Tendencias**: Detecta patrones de uso y recomienda acciones
- ✅ **Limpieza de Historial**: Elimina registros antiguos automáticamente

---

## 📦 Requisitos del Sistema

### Mínimos
- 🖥️ Windows 7 o superior
- 💾 100 MB de espacio en disco
- 🧠 2 GB de RAM
- 🐍 Python 3.8 o superior (para desarrollo)

### Recomendados
- 🖥️ Windows 10/11
- 💾 500 MB de espacio en disco
- 🧠 4 GB de RAM
- 🔌 Puertos USB 2.0 o superior

---

## 🚀 Instalación

### 🔧 Instalación desde Código Fuente

1. **Clona el repositorio**
```bash
git clone https://github.com/klorenzo29/Kalm-USB-Kopy.git
cd Kalm-USB-Kopy

3. Instala las dependencias
pip install -r requirements.txt

4. Ejecuta la aplicación
python kalm_usb_kopy.py

📦 Instalación desde Ejecutable

    Descarga el ejecutable desde Releases

    Ejecuta Kalm-USB-Kopy.exe

    Configura el precio por GB en el menú Configuración

🐍 Dependencias
ttkbootstrap>=1.10.0
psutil>=5.9.0
pywin32>=305
pystray>=0.19.0
pillow>=10.0.0
plyer>=0.9.0

📖 Guía de Uso
🚀 Primeros Pasos

    Inicia la aplicación: Aparecerá la ventana principal

    Conecta una USB: La aplicación detectará automáticamente la memoria

    Asigna un nombre: Si es la primera vez, te pedirá un nombre

    Configura el precio: Ve a Configuración > Precio por GB

    ¡Empieza a copiar!: Selecciona la memoria y haz clic en "Iniciar Copia"

💾 Proceso de Copia

    Selecciona la memoria de la lista de unidades conectadas

    Haz clic en "Iniciar Copia"

    Ingresa los GB a copiar (se calcula automáticamente el precio)

    Confirma la copia: La aplicación registrará automáticamente la transacción

    Recibe notificación: Aparecerá una notificación emergente con los detalles

📊 Gestión de Informes

    Generar informe diario: Menú Archivo > Generar Informe Diario

    Ver historial completo: Menú Archivo > Ver Historial Completo

    Exportar datos: Menú Archivo > Exportar Historial (CSV)

    Ver estadísticas: Pestaña "Estadísticas"

🎨 Personalización

    Cambiar tema: Menú Configuración > Cambiar Tema

    Inicio con Windows: Menú Configuración > Iniciar con Windows

    Minimizar a bandeja: Menú Configuración > Minimizar a Bandeja

    Duración notificaciones: Configuración General > Notificaciones

📸 Capturas de Pantalla
🖥️ Ventana Principal
https://raw.githubusercontent.com/klorenzo29/Kalm-USB-Kopy/main/screenshots/main_window.png

💾 Gestión de Memorias
https://raw.githubusercontent.com/klorenzo29/Kalm-USB-Kopy/main/screenshots/memories.png

📊 Estadísticas
https://raw.githubusercontent.com/klorenzo29/Kalm-USB-Kopy/main/screenshots/stats.png

🎨 Temas
https://raw.githubusercontent.com/klorenzo29/Kalm-USB-Kopy/main/screenshots/themes.png

🔔 Notificaciones
https://raw.githubusercontent.com/klorenzo29/Kalm-USB-Kopy/main/screenshots/notifications.png

⚙️ Configuración
📁 Archivos de Configuración
Archivo	Descripción
config_kalm.json	Configuración general del programa
historial_kalm.json	Historial de todas las copias
memorias_kalm.db	Base de datos de memorias identificadas
estadisticas_kalm.json	Estadísticas y análisis de tendencias

🔧 Configuración Avanzada
{
    "precio_por_gb": 5.0,
    "moneda": "CUP",
    "iniciar_con_windows": false,
    "tema": "darkly",
    "auto_detectar": true,
    "carpeta_respaldo": "",
    "mostrar_notificaciones": true,
    "minimizar_bandeja": true,
    "notificaciones_duracion": 0,
    "max_historial": 10000,
    "formato_informe": "txt"
}

📂 Estructura del Proyecto
Kalm-USB-Kopy/
├── 📁 screenshots/          # Capturas de pantalla
├── 📁 reportes_kalm/        # Informes generados
├── 📁 backup_kalm_*/        # Respaldos automáticos
├── 🐍 kalm_usb_kopy.py      # Código principal
├── 📄 config_kalm.json      # Configuración
├── 📄 historial_kalm.json   # Historial
├── 📄 memorias_kalm.db      # Base de memorias
├── 📄 estadisticas_kalm.json # Estadísticas
├── 📄 requirements.txt      # Dependencias
├── 📄 LICENSE               # Licencia
└── 📄 README.md             # Este archivo

🛠️ Tecnologías Utilizadas
🖥️ Frontend

    Tkinter: Biblioteca GUI estándar de Python

    ttkbootstrap: Temas modernos para Tkinter

    Pillow: Procesamiento de imágenes

⚙️ Backend

    Python 3.8+: Lenguaje de programación principal

    psutil: Monitoreo de dispositivos USB

    pywin32: Integración con Windows

    plyer: Notificaciones del sistema

🛡️ Seguridad

    Hashlib: Identificación única de memorias

    JSON: Almacenamiento seguro de datos

🤝 Contribuciones

¡Las contribuciones son bienvenidas! Para contribuir:

    Fork el repositorio

    Crea una rama para tu feature (git checkout -b feature/AmazingFeature)

    Commit tus cambios (git commit -m 'Add some AmazingFeature')

    Push a la rama (git push origin feature/AmazingFeature)

    Abre un Pull Request

📝 Guía de Contribución

    🐛 Reporta bugs en Issues

    💡 Sugiere mejoras en Discussions

    📚 Mejora la documentación

    🎨 Diseña nuevos temas

📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para más detalles.
MIT License

Copyright (c) 2026 Carlos A. Lorenzo Marro

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
...

👤 Contacto

Creador: Carlos A. Lorenzo Marro

    📧 Email: klorenzo29@nauta.cu

    🐙 GitHub: klorenzo29

    🐦 Twitter: @klorenzo29

🙏 Agradecimientos

    Inspiración: Tensei Shitara Slime Datta Ken y Overlord

    Comunidad: A todos los usuarios que contribuyen con feedback

    Emprendedores cubanos: Por su esfuerzo y perseverancia

⭐ Apoya el Proyecto

Si te gusta Kalm-USB-Kopy, considera:

    ⭐ Darle una estrella en GitHub

    🐛 Reportar bugs y sugerir mejoras

    📝 Compartir el proyecto con otros emprendedores

    💬 Dejar un comentario o testimonio

<div align="center"> <strong>⚔️ Kalm-USB-Kopy - Gestión de Memorias USB ⚔️</strong> <br> <em>Hecho con ❤️ para emprendedores</em> </div> ```

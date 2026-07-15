"""
Kalm-USB-Kopy - Gestor de Memorias USB
Versión: 3.1.1
Descripción: Sistema avanzado de gestión de memorias USB con notificaciones Windows
Creador: Carlos A. Lorenzo Marro
Email: klorenzo29@nauta.cu
"""

import os
import sys
import json
import shutil
import datetime
import threading
import time
import subprocess
import winreg
from pathlib import Path
from tkinter import *
from tkinter import ttk, messagebox, scrolledtext
from tkinter import filedialog
import psutil
import tkinter as tk
from tkinter import font as tkfont
import hashlib
import pickle
from collections import Counter
import ctypes
from ctypes import wintypes
import base64

# Intentar importar ttkbootstrap
try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    from ttkbootstrap.tooltip import ToolTip
    BOOTSTRAP_AVAILABLE = True
except ImportError:
    BOOTSTRAP_AVAILABLE = False
    print("ttkbootstrap no instalado. Usando tema por defecto.")
    tb = ttk

# Intentar importar para notificaciones
try:
    from plyer import notification
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False
    print("plyer no instalado. Instalar: pip install plyer")

# ==================== TEMAS VÁLIDOS DE TTKBOOTSTRAP ====================
TEMAS_VALIDOS = [
    'darkly',      # Oscuro con azules (recomendado)
    'superhero',   # Estilo cómic
    'cyborg',      # Futurista
    'vapor',       # Vaporwave
    'solar',       # Oscuro con solares
    'flatly',      # Plano moderno
    'journal',     # Estilo diario
    'litera',      # Estilo literario
    'lumen',       # Claro
    'minty',       # Verde menta
    'pulse',       # Animado
    'sandstone',   # Arena
    'united',      # Unido
    'yeti',        # Moderno
    'cosmo',       # Cosmopolita
    'simplex',     # Simple
    'cerulean'     # Azul cielo
]

# ==================== ICONO SVG K MODERNA ====================
FAVICON_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
    <rect width='100' height='100' rx='20' fill='%232c3e50'/>
    <text x='50' y='70' font-family='Arial' font-size='70' font-weight='bold' fill='white' text-anchor='middle'>K</text>
</svg>"""

# ==================== SISTEMA DE NOTIFICACIONES WINDOWS ====================

class WindowsNotifier:
    """Sistema de notificaciones estilo Windows"""
    
    def __init__(self):
        self.notification_active = False
        self.notification_window = None
        
    def mostrar_notificacion(self, titulo, mensaje, icono=None, duracion=0):
        """
        Muestra una notificación estilo Windows
        duracion=0 significa que no se cierra automáticamente
        """
        # Método 1: Usar plyer si está disponible
        if NOTIFICATION_AVAILABLE:
            try:
                notification.notify(
                    title=titulo,
                    message=mensaje,
                    app_name="Kalm-USB-Kopy",
                    timeout=duracion if duracion > 0 else 10,
                    app_icon=icono if icono and os.path.exists(icono) else None
                )
                return True
            except:
                pass
        
        # Método 2: Usar ventana personalizada (más control)
        return self._mostrar_notificacion_personalizada(titulo, mensaje, duracion)
    
    def _mostrar_notificacion_personalizada(self, titulo, mensaje, duracion=0):
        """Muestra una notificación con ventana personalizada"""
        try:
            # Crear ventana de notificación
            ventana = tk.Toplevel()
            ventana.title("Kalm-USB-Kopy")
            ventana.geometry("400x200")
            
            # Posicionar en la esquina inferior derecha
            ventana.update_idletasks()
            ancho_pantalla = ventana.winfo_screenwidth()
            alto_pantalla = ventana.winfo_screenheight()
            x = ancho_pantalla - 420
            y = alto_pantalla - 220
            ventana.geometry(f"400x200+{x}+{y}")
            
            # Estilo de la ventana
            ventana.overrideredirect(True)  # Sin bordes
            ventana.attributes('-topmost', True)  # Siempre arriba
            
            # Color de fondo según tema
            fondo = "#1a1a2e"
            color_texto = "white"
            
            # Frame principal
            frame = tk.Frame(ventana, bg=fondo, bd=2, relief=tk.RAISED)
            frame.pack(fill=tk.BOTH, expand=True)
            
            # Título
            titulo_frame = tk.Frame(frame, bg="#2d2d4e")
            titulo_frame.pack(fill=tk.X, padx=0, pady=0)
            
            lbl_titulo = tk.Label(
                titulo_frame,
                text=f"⚔️ {titulo}",
                font=('Segoe UI', 11, 'bold'),
                bg="#2d2d4e",
                fg="#9b59b6"
            )
            lbl_titulo.pack(side=tk.LEFT, padx=10, pady=5)
            
            # Botón cerrar (X)
            btn_cerrar = tk.Button(
                titulo_frame,
                text="✕",
                font=('Segoe UI', 10, 'bold'),
                bg="#2d2d4e",
                fg="white",
                relief=tk.FLAT,
                command=ventana.destroy
            )
            btn_cerrar.pack(side=tk.RIGHT, padx=5, pady=2)
            
            # Mensaje
            mensaje_frame = tk.Frame(frame, bg=fondo)
            mensaje_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Dividir mensaje en líneas
            lineas = mensaje.split('\n')
            for linea in lineas:
                if '💰' in linea or '$' in linea:
                    lbl = tk.Label(
                        mensaje_frame,
                        text=linea,
                        font=('Segoe UI', 10, 'bold'),
                        bg=fondo,
                        fg="#27ae60"
                    )
                elif 'GB' in linea or '📊' in linea:
                    lbl = tk.Label(
                        mensaje_frame,
                        text=linea,
                        font=('Segoe UI', 10),
                        bg=fondo,
                        fg="#3498db"
                    )
                else:
                    lbl = tk.Label(
                        mensaje_frame,
                        text=linea,
                        font=('Segoe UI', 9),
                        bg=fondo,
                        fg=color_texto
                    )
                lbl.pack(anchor=tk.W, pady=1)
            
            # Si duracion > 0, cerrar automáticamente
            if duracion > 0:
                ventana.after(duracion * 1000, ventana.destroy)
            
            # Efecto de entrada
            ventana.attributes('-alpha', 0.0)
            
            def fade_in():
                alpha = ventana.attributes('-alpha')
                if alpha < 1.0:
                    ventana.attributes('-alpha', min(alpha + 0.1, 1.0))
                    ventana.after(30, fade_in)
            
            fade_in()
            
            # Mantener referencia
            self.notification_window = ventana
            return True
            
        except Exception as e:
            print(f"Error al mostrar notificación: {e}")
            return False

# ==================== CONFIGURACIÓN ====================
APP_NAME = "Kalm-USB-Kopy"
APP_VERSION = "3.1.1"
CREATOR = "Carlos A. Lorenzo Marro"
EMAIL = "klorenzo29@nauta.cu"
CONFIG_FILE = "config_kalm.json"
HISTORY_FILE = "historial_kalm.json"
MEMORY_DB = "memorias_kalm.db"
STATS_FILE = "estadisticas_kalm.json"
REPORT_DIR = "reportes_kalm"

DEFAULT_CONFIG = {
    "precio_por_gb": 5.0,
    "moneda": "CUP",
    "iniciar_con_windows": False,
    "tema": "darkly",
    "auto_detectar": True,
    "carpeta_respaldo": "",
    "mostrar_notificaciones": True,
    "minimizar_bandeja": True,
    "analisis_automatico": True,
    "max_historial": 10000,
    "formato_informe": "txt",
    "notificaciones_duracion": 0  # 0 = no se cierra sola
}

# ==================== CLASES BASE ====================

class ConfigManager:
    def __init__(self):
        self.config = {}
        self.cargar_config()
    
    def cargar_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = DEFAULT_CONFIG.copy()
                self.guardar_config()
        except:
            self.config = DEFAULT_CONFIG.copy()
            self.guardar_config()
    
    def guardar_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar configuración: {e}")
    
    def obtener(self, clave, valor_por_defecto=None):
        return self.config.get(clave, valor_por_defecto)
    
    def establecer(self, clave, valor):
        self.config[clave] = valor
        self.guardar_config()
    
    def obtener_precio(self):
        return float(self.config.get("precio_por_gb", 5.0))
    
    def establecer_precio(self, precio):
        self.config["precio_por_gb"] = float(precio)
        self.guardar_config()

class HistoryManager:
    def __init__(self):
        self.historial = []
        self.cargar_historial()
    
    def cargar_historial(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.historial = json.load(f)
        except:
            self.historial = []
    
    def guardar_historial(self):
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.historial, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar historial: {e}")
    
    def agregar_registro(self, registro):
        if 'fecha' not in registro:
            registro['fecha'] = datetime.datetime.now().isoformat()
        self.historial.append(registro)
        self.guardar_historial()
    
    def obtener_diario(self, fecha=None):
        if fecha is None:
            fecha = datetime.datetime.now().date().isoformat()
        
        diario = []
        for registro in self.historial:
            try:
                reg_fecha = datetime.datetime.fromisoformat(registro['fecha']).date().isoformat()
                if reg_fecha == fecha:
                    diario.append(registro)
            except:
                pass
        return diario
    
    def obtener_resumen_diario(self, fecha=None):
        registros = self.obtener_diario(fecha)
        total_gb = sum(r.get('gb_copiados', 0) for r in registros)
        total_precio = sum(r.get('precio', 0) for r in registros)
        return {
            'total_registros': len(registros),
            'total_gb': total_gb,
            'total_precio': total_precio,
            'registros': registros
        }

class ReportGenerator:
    def __init__(self):
        self.history_manager = HistoryManager()
    
    def generar_informe_diario(self, fecha=None):
        if fecha is None:
            fecha = datetime.datetime.now().date().isoformat()
        
        resumen = self.history_manager.obtener_resumen_diario(fecha)
        
        informe = "="*60 + "\n"
        informe += f"📋 INFORME DIARIO - {fecha}\n"
        informe += "="*60 + "\n\n"
        
        informe += f"📊 Total de memorias: {resumen['total_registros']}\n"
        informe += f"💾 Total GB copiados: {resumen['total_gb']:.2f}\n"
        informe += f"💰 Total generado: ${resumen['total_precio']:.2f}\n\n"
        
        informe += "-"*60 + "\n"
        informe += "📝 DETALLE DE TRANSACCIONES:\n"
        informe += "-"*60 + "\n\n"
        
        for i, registro in enumerate(resumen['registros'], 1):
            informe += f"{i}. 💾 Memoria: {registro.get('nombre_memoria', 'N/A')}\n"
            informe += f"   📊 GB Copiados: {registro.get('gb_copiados', 0):.2f}\n"
            informe += f"   💰 Precio: ${registro.get('precio', 0):.2f}\n"
            informe += f"   🕐 Hora: {registro.get('hora', 'N/A')}\n\n"
        
        informe += "="*60 + "\n"
        informe += f"⚙️ Generado por {APP_NAME} v{APP_VERSION}\n"
        informe += f"👤 Creador: {CREATOR}\n"
        informe += f"📧 Email: {EMAIL}\n"
        informe += datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return informe
    
    def guardar_informe(self, fecha=None):
        if fecha is None:
            fecha = datetime.datetime.now().date().isoformat()
        
        os.makedirs(REPORT_DIR, exist_ok=True)
        
        informe = self.generar_informe_diario(fecha)
        nombre_archivo = f"informe_{fecha}.txt"
        ruta = os.path.join(REPORT_DIR, nombre_archivo)
        
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(informe)
        
        return ruta

class MemoryManager:
    def __init__(self):
        self.memorias = {}
        self.cargar_memorias()
    
    def cargar_memorias(self):
        try:
            if os.path.exists(MEMORY_DB):
                with open(MEMORY_DB, 'r', encoding='utf-8') as f:
                    self.memorias = json.load(f)
        except:
            self.memorias = {}
    
    def guardar_memorias(self):
        try:
            with open(MEMORY_DB, 'w', encoding='utf-8') as f:
                json.dump(self.memorias, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar memorias: {e}")
    
    def identificar_memoria(self, unidad, nombre=None):
        try:
            import win32api
            drive = win32api.GetVolumeInformation(unidad)
            serial = str(drive[1])
        except:
            serial = hashlib.md5(unidad.encode()).hexdigest()[:8]
        
        for mem_id, data in self.memorias.items():
            if data.get('serial') == serial:
                return mem_id, data
        
        if nombre is None:
            nombre = f"Memoria_{len(self.memorias) + 1}"
        
        mem_id = f"MEM_{int(time.time())}_{serial[:4]}"
        self.memorias[mem_id] = {
            'id': mem_id,
            'nombre': nombre,
            'serial': serial,
            'unidad': unidad,
            'fecha_registro': datetime.datetime.now().isoformat(),
            'veces_usada': 0,
            'total_gb_copiados': 0,
            'total_ingresos': 0,
            'ultima_conexion': datetime.datetime.now().isoformat(),
            'historico': []
        }
        self.guardar_memorias()
        return mem_id, self.memorias[mem_id]
    
    def registrar_copia(self, mem_id, gb, precio, archivos=None):
        if mem_id in self.memorias:
            registro = {
                'fecha': datetime.datetime.now().isoformat(),
                'gb': gb,
                'precio': precio,
                'archivos': archivos or []
            }
            self.memorias[mem_id]['historico'].append(registro)
            self.memorias[mem_id]['veces_usada'] += 1
            self.memorias[mem_id]['total_gb_copiados'] += gb
            self.memorias[mem_id]['total_ingresos'] += precio
            self.memorias[mem_id]['ultima_conexion'] = datetime.datetime.now().isoformat()
            self.guardar_memorias()
    
    def obtener_estadisticas_memoria(self, mem_id):
        if mem_id not in self.memorias:
            return None
        
        data = self.memorias[mem_id]
        historico = data.get('historico', [])
        
        if not historico:
            return {
                'total_copias': 0,
                'total_gb': 0,
                'total_ingresos': 0,
                'promedio_gb': 0,
                'frecuencia': 0
            }
        
        total_copias = len(historico)
        total_gb = sum(h['gb'] for h in historico)
        total_ingresos = sum(h['precio'] for h in historico)
        
        return {
            'total_copias': total_copias,
            'total_gb': total_gb,
            'total_ingresos': total_ingresos,
            'promedio_gb': total_gb / total_copias if total_copias > 0 else 0,
            'frecuencia': total_copias / ((datetime.datetime.now() - datetime.datetime.fromisoformat(data['fecha_registro'])).days + 1)
        }
    
    def obtener_todas_memorias(self):
        return self.memorias
    
    def obtener_memoria_por_unidad(self, unidad):
        for mem_id, data in self.memorias.items():
            if data.get('unidad') == unidad:
                return mem_id, data
        return None, None

class DataAnalyzer:
    def __init__(self, history_manager, memory_manager):
        self.history_manager = history_manager
        self.memory_manager = memory_manager
        self.analisis = {}
        self.cargar_analisis()
    
    def cargar_analisis(self):
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    self.analisis = json.load(f)
        except:
            self.analisis = {}
    
    def guardar_analisis(self):
        try:
            with open(STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.analisis, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar análisis: {e}")
    
    def analizar_tendencias(self):
        todas_memorias = self.memory_manager.obtener_todas_memorias()
        
        total_copias = 0
        total_gb = 0
        total_ingresos = 0
        memorias_activas = 0
        
        for mem_id, data in todas_memorias.items():
            copias = len(data.get('historico', []))
            if copias > 0:
                memorias_activas += 1
                total_copias += copias
                total_gb += data.get('total_gb_copiados', 0)
                total_ingresos += data.get('total_ingresos', 0)
        
        memoria_mas_usada = None
        max_copias = 0
        for mem_id, data in todas_memorias.items():
            copias = len(data.get('historico', []))
            if copias > max_copias:
                max_copias = copias
                memoria_mas_usada = data.get('nombre', mem_id)
        
        ahora = datetime.datetime.now()
        ultimos_7_dias = 0
        ultimos_30_dias = 0
        
        for registro in self.history_manager.historial:
            try:
                fecha = datetime.datetime.fromisoformat(registro['fecha'])
                dias = (ahora - fecha).days
                if dias <= 7:
                    ultimos_7_dias += 1
                if dias <= 30:
                    ultimos_30_dias += 1
            except:
                pass
        
        self.analisis = {
            'ultima_actualizacion': ahora.isoformat(),
            'total_copias': total_copias,
            'total_gb': total_gb,
            'total_ingresos': total_ingresos,
            'memorias_activas': memorias_activas,
            'memoria_mas_usada': memoria_mas_usada,
            'copias_ultimos_7_dias': ultimos_7_dias,
            'copias_ultimos_30_dias': ultimos_30_dias,
            'promedio_diario': total_copias / ((ahora - datetime.datetime.fromisoformat(self.analisis.get('ultima_actualizacion', ahora.isoformat()))).days + 1) if total_copias > 0 else 0
        }
        
        self.guardar_analisis()
        return self.analisis
    
    def obtener_estadisticas_completas(self):
        if not self.analisis or 'ultima_actualizacion' not in self.analisis:
            return self.analizar_tendencias()
        
        try:
            ultima = datetime.datetime.fromisoformat(self.analisis['ultima_actualizacion'])
            ahora = datetime.datetime.now()
            if (ahora - ultima).days >= 1:
                return self.analizar_tendencias()
        except:
            return self.analizar_tendencias()
        
        return self.analisis

class USBMonitor:
    def __init__(self, callback_conexion, callback_desconexion):
        self.callback_conexion = callback_conexion
        self.callback_desconexion = callback_desconexion
        self.unidades_conocidas = set()
        self.monitoreando = False
        self.hilo = None
    
    def iniciar(self):
        self.monitoreando = True
        self.hilo = threading.Thread(target=self._monitorear, daemon=True)
        self.hilo.start()
    
    def detener(self):
        self.monitoreando = False
        if self.hilo:
            self.hilo.join(timeout=1)
    
    def _monitorear(self):
        while self.monitoreando:
            try:
                unidades_actuales = set()
                for particion in psutil.disk_partitions():
                    if 'removable' in particion.opts:
                        unidades_actuales.add(particion.mountpoint)
                
                nuevas = unidades_actuales - self.unidades_conocidas
                for unidad in nuevas:
                    if self.callback_conexion:
                        self.callback_conexion(unidad)
                
                removidas = self.unidades_conocidas - unidades_actuales
                for unidad in removidas:
                    if self.callback_desconexion:
                        self.callback_desconexion(unidad)
                
                self.unidades_conocidas = unidades_actuales
                time.sleep(2)
            except:
                time.sleep(2)
    
    def obtener_unidades_conectadas(self):
        unidades = []
        for particion in psutil.disk_partitions():
            if 'removable' in particion.opts:
                try:
                    uso = psutil.disk_usage(particion.mountpoint)
                    unidades.append({
                        'letra': particion.mountpoint,
                        'total_gb': self._bytes_a_gb(uso.total),
                        'usado_gb': self._bytes_a_gb(uso.used),
                        'libre_gb': self._bytes_a_gb(uso.free)
                    })
                except:
                    pass
        return unidades
    
    def _bytes_a_gb(self, bytes):
        return round(bytes / (1024**3), 2)

def bytes_a_gb(bytes):
    return round(bytes / (1024**3), 2)

# ==================== CLASE PRINCIPAL KALM-USB-KOPY ====================

class KalmUSBKopy:
    """Aplicación principal Kalm-USB-Kopy"""
    
    def __init__(self, root):
        self.root = root
        self.config_manager = ConfigManager()
        self.history_manager = HistoryManager()
        self.report_generator = ReportGenerator()
        self.memory_manager = MemoryManager()
        self.data_analyzer = DataAnalyzer(self.history_manager, self.memory_manager)
        self.notifier = WindowsNotifier()
        
        # Variables de estado
        self.unidad_seleccionada = None
        self.memoria_seleccionada_id = None
        self.memoria_seleccionada_data = None
        self.gb_copiados = 0.0
        self.copiando = False
        self.monitor = None
        self.registro_actual = None
        self.en_bandeja = False
        self.tema_actual = self.config_manager.obtener("tema", "darkly")
        
        # Configurar ventana
        self.root.title(f"{APP_NAME} - Gestor de Memorias USB")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Aplicar icono con la K moderna
        self.aplicar_icono_k()
        
        # Aplicar tema
        self.aplicar_tema()
        
        # Crear UI
        self.crear_widgets()
        self.cargar_configuracion()
        self.iniciar_monitoreo()
        
        # Verificar inicio automático
        if self.config_manager.obtener("iniciar_con_windows", False):
            self.agregar_inicio_windows()
        
        # Configurar minimización a bandeja
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        
        # Análisis inicial
        self.actualizar_estadisticas()
    
    def aplicar_icono_k(self):
        """Aplica el icono con la letra K moderna"""
        try:
            # Crear un icono temporal desde SVG
            import tempfile
            from PIL import Image, ImageDraw, ImageFont
            
            # Crear imagen con la K
            img = Image.new('RGBA', (64, 64), (44, 62, 80))  # #2c3e50
            draw = ImageDraw.Draw(img)
            
            # Dibujar la K
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            draw.text((16, 8), "K", fill=(255, 255, 255), font=font)
            
            # Guardar como .ico
            ico_path = os.path.join(tempfile.gettempdir(), "kalm_icon.ico")
            img.save(ico_path, format='ICO', sizes=[(64, 64)])
            
            # Aplicar icono
            self.root.iconbitmap(default=ico_path)
            
            # Guardar para uso futuro
            self.icon_path = ico_path
            
        except Exception as e:
            print(f"Error al aplicar icono: {e}")
            # Intentar con método alternativo
            try:
                self.root.iconbitmap(default='kalm.ico')
            except:
                pass
    
    def aplicar_tema(self):
        """Aplica el tema configurado sin reiniciar"""
        tema = self.config_manager.obtener("tema", "darkly")
        self.tema_actual = tema
        
        # Validar que el tema existe
        if tema not in TEMAS_VALIDOS:
            tema = "darkly"  # Tema por defecto
            self.config_manager.establecer("tema", tema)
        
        if BOOTSTRAP_AVAILABLE:
            try:
                # Crear nuevo estilo con el tema
                self.style = tb.Style(theme=tema)
                
                # Configurar colores adicionales
                self.style.configure('TLabel', foreground='white')
                self.style.configure('TButton', foreground='white')
                self.style.configure('Treeview', background='#2b2b2b', foreground='white')
                self.style.configure('Treeview.Heading', background='#1a1a2e', foreground='white')
                self.style.configure('TFrame', background='#1a1a2e')
                self.style.configure('TLabelframe', background='#1a1a2e')
                self.style.configure('TLabelframe.Label', background='#1a1a2e', foreground='white')
                
                # Configurar colores de éxito
                self.style.configure('success.TButton', foreground='white')
                
                # Forzar actualización de la UI
                self.root.update_idletasks()
                
                return True
            except Exception as e:
                print(f"Error al aplicar tema '{tema}': {e}")
                # Intentar con tema por defecto
                try:
                    self.style = tb.Style(theme="darkly")
                    self.config_manager.establecer("tema", "darkly")
                    return True
                except:
                    return False
        return False
    
    def on_close(self):
        """Maneja el cierre de la ventana"""
        if self.config_manager.obtener("minimizar_bandeja", True):
            self.root.withdraw()
            # Mostrar notificación
            self.notifier.mostrar_notificacion(
                "Kalm-USB-Kopy",
                "La aplicación sigue ejecutándose en segundo plano.\nHaz clic en el icono de la bandeja para mostrar."
            )
        else:
            if hasattr(self, 'monitor') and self.monitor:
                self.monitor.detener()
            self.root.destroy()
    
    def crear_widgets(self):
        """Crea todos los widgets de la interfaz"""
        
        # Barra de menú
        self.crear_menu()
        
        # Panel principal con pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Pestaña Principal
        self.pestana_principal = ttk.Frame(self.notebook)
        self.notebook.add(self.pestana_principal, text="⚔️ Kalm-USB-Kopy")
        self.crear_pestana_principal()
        
        # Pestaña Memorias
        self.pestana_memorias = ttk.Frame(self.notebook)
        self.notebook.add(self.pestana_memorias, text="💾 Memorias")
        self.crear_pestana_memorias()
        
        # Pestaña Estadísticas
        self.pestana_estadisticas = ttk.Frame(self.notebook)
        self.notebook.add(self.pestana_estadisticas, text="📊 Estadísticas")
        self.crear_pestana_estadisticas()
        
        # Pestaña Historial
        self.pestana_historial = ttk.Frame(self.notebook)
        self.notebook.add(self.pestana_historial, text="📜 Historial")
        self.crear_pestana_historial()
        
        # Barra de estado
        self.crear_barra_estado()
        
        # Inicializar estado
        self.actualizar_estado()
        self.actualizar_unidades()
        self.actualizar_lista_memorias()
        self.actualizar_historial()
    
    def crear_menu(self):
        """Crea la barra de menú"""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        archivo_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 Archivo", menu=archivo_menu)
        archivo_menu.add_command(label="Generar Informe Diario", command=self.generar_informe)
        archivo_menu.add_command(label="Ver Historial Completo", command=self.ver_historial)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Exportar Historial (CSV)", command=self.exportar_csv)
        archivo_menu.add_command(label="Exportar Base de Memorias", command=self.exportar_memorias)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.on_close)
        
        # Menú Configuración
        config_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="⚙️ Configuración", menu=config_menu)
        config_menu.add_command(label="Precio por GB", command=self.abrir_config_precio)
        config_menu.add_command(label="Configuración General", command=self.abrir_config_general)
        config_menu.add_separator()
        config_menu.add_command(label="Iniciar con Windows", command=self.toggle_inicio_windows)
        config_menu.add_command(label="Minimizar a Bandeja", command=self.toggle_bandeja)
        config_menu.add_command(label="Cambiar Tema", command=self.cambiar_tema)
        
        # Menú Herramientas
        herramientas_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🛠️ Herramientas", menu=herramientas_menu)
        herramientas_menu.add_command(label="Analizar Tendencias", command=self.analizar_tendencias)
        herramientas_menu.add_command(label="Limpiar Historial Antiguo", command=self.limpiar_historial)
        herramientas_menu.add_command(label="Respaldo de Base de Datos", command=self.respaldar_datos)
        
        # Menú Ayuda
        ayuda_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ Ayuda", menu=ayuda_menu)
        ayuda_menu.add_command(label="Acerca de", command=self.mostrar_acerca)
        ayuda_menu.add_command(label="Manual Rápido", command=self.mostrar_manual)
        ayuda_menu.add_command(label="Estadísticas del Sistema", command=self.mostrar_estadisticas_sistema)
    
    def crear_pestana_principal(self):
        """Crea la pestaña principal"""
        parent = self.pestana_principal
        
        # Logo y título con la K
        titulo_frame = ttk.Frame(parent)
        titulo_frame.pack(fill=X, pady=10)
        
        # Crear un label con la K estilizada
        titulo = ttk.Label(
            titulo_frame,
            text="⚔️ Kalm-USB-Kopy ⚔️",
            font=('Segoe UI', 28, 'bold'),
            foreground='#9b59b6' if not BOOTSTRAP_AVAILABLE else None
        )
        titulo.pack()
        
        subtitulo = ttk.Label(
            titulo_frame,
            text=f"Sistema de Gestión de Memorias USB | Versión {APP_VERSION}",
            font=('Segoe UI', 10)
        )
        subtitulo.pack()
        
        creador_label = ttk.Label(
            titulo_frame,
            text=f"Creador: {CREATOR} | {EMAIL}",
            font=('Segoe UI', 8),
            foreground='#7f8c8d' if not BOOTSTRAP_AVAILABLE else None
        )
        creador_label.pack()
        
        # Panel superior: Memorias conectadas
        frame_usb = ttk.LabelFrame(parent, text="🔮 Memorias Conectadas", padding=10)
        frame_usb.pack(fill=X, pady=5)
        
        list_frame = ttk.Frame(frame_usb)
        list_frame.pack(fill=BOTH, expand=True)
        
        self.lista_unidades = ttk.Treeview(
            list_frame,
            columns=('Letra', 'Nombre', 'Total', 'Usado', 'Libre'),
            show='headings',
            height=3
        )
        
        self.lista_unidades.heading('Letra', text='Unidad')
        self.lista_unidades.heading('Nombre', text='Nombre de Memoria')
        self.lista_unidades.heading('Total', text='Total (GB)')
        self.lista_unidades.heading('Usado', text='Usado (GB)')
        self.lista_unidades.heading('Libre', text='Libre (GB)')
        
        self.lista_unidades.column('Letra', width=80)
        self.lista_unidades.column('Nombre', width=150)
        self.lista_unidades.column('Total', width=100)
        self.lista_unidades.column('Usado', width=100)
        self.lista_unidades.column('Libre', width=100)
        
        scroll_y = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.lista_unidades.yview)
        self.lista_unidades.configure(yscrollcommand=scroll_y.set)
        
        self.lista_unidades.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)
        
        self.lista_unidades.bind('<<TreeviewSelect>>', self.on_seleccionar_unidad)
        
        btn_frame = ttk.Frame(frame_usb)
        btn_frame.pack(fill=X, pady=(10, 0))
        
        self.btn_analizar = ttk.Button(btn_frame, text="🔍 Analizar Memoria", command=self.analizar_memoria)
        self.btn_analizar.pack(side=LEFT, padx=5)
        
        self.btn_copiar = ttk.Button(btn_frame, text="📋 Copiar Datos", command=self.iniciar_copia, state=DISABLED)
        self.btn_copiar.pack(side=LEFT, padx=5)
        
        self.btn_actualizar = ttk.Button(btn_frame, text="🔄 Actualizar", command=self.actualizar_unidades)
        self.btn_actualizar.pack(side=LEFT, padx=5)
        
        # Panel de control de copia
        frame_control = ttk.LabelFrame(parent, text="⚡ Control de Copias", padding=10)
        frame_control.pack(fill=X, pady=5)
        
        info_frame = ttk.Frame(frame_control)
        info_frame.pack(fill=X, pady=5)
        
        col1 = ttk.Frame(info_frame)
        col1.pack(side=LEFT, fill=X, expand=True)
        
        ttk.Label(col1, text="💾 Memoria:").grid(row=0, column=0, sticky='w', padx=5)
        self.lbl_memoria = ttk.Label(col1, text="Ninguna seleccionada", font=('Segoe UI', 9, 'bold'))
        self.lbl_memoria.grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Label(col1, text="📊 GB a copiar:").grid(row=1, column=0, sticky='w', padx=5)
        self.lbl_gb_copiar = ttk.Label(col1, text="0.00 GB", font=('Segoe UI', 9, 'bold'))
        self.lbl_gb_copiar.grid(row=1, column=1, sticky='w', padx=5)
        
        col2 = ttk.Frame(info_frame)
        col2.pack(side=LEFT, fill=X, expand=True)
        
        ttk.Label(col2, text="💰 Precio por GB:").grid(row=0, column=0, sticky='w', padx=5)
        self.lbl_precio_gb = ttk.Label(col2, text=f"${self.config_manager.obtener_precio():.2f}", font=('Segoe UI', 9, 'bold'))
        self.lbl_precio_gb.grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Label(col2, text="💵 Total a cobrar:").grid(row=1, column=0, sticky='w', padx=5)
        self.lbl_precio_total = ttk.Label(col2, text="$0.00", font=('Segoe UI', 11, 'bold'), foreground='#27ae60')
        self.lbl_precio_total.grid(row=1, column=1, sticky='w', padx=5)
        
        progress_frame = ttk.Frame(frame_control)
        progress_frame.pack(fill=X, pady=10)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            length=300,
            mode='determinate',
            style='success.Horizontal.TProgressbar' if BOOTSTRAP_AVAILABLE else None
        )
        self.progress_bar.pack(fill=X, padx=5)
        
        self.lbl_progreso = ttk.Label(progress_frame, text="✅ Listo para copiar")
        self.lbl_progreso.pack(pady=5)
        
        action_frame = ttk.Frame(frame_control)
        action_frame.pack(fill=X, pady=5)
        
        self.btn_iniciar_copia = ttk.Button(
            action_frame,
            text="🚀 Iniciar Copia",
            command=self.iniciar_copia,
            state=DISABLED,
            style='success.TButton' if BOOTSTRAP_AVAILABLE else None
        )
        self.btn_iniciar_copia.pack(side=LEFT, padx=5)
        
        self.btn_guardar_registro = ttk.Button(
            action_frame,
            text="💾 Guardar Registro Manual",
            command=self.guardar_registro_manual,
            state=DISABLED
        )
        self.btn_guardar_registro.pack(side=LEFT, padx=5)
        
        self.btn_cancelar = ttk.Button(
            action_frame,
            text="⛔ Cancelar",
            command=self.cancelar_copia,
            state=DISABLED
        )
        self.btn_cancelar.pack(side=LEFT, padx=5)
        
        # Panel de resumen rápido
        frame_resumen = ttk.LabelFrame(parent, text="📊 Resumen Rápido", padding=10)
        frame_resumen.pack(fill=X, pady=5)
        
        resumen_frame = ttk.Frame(frame_resumen)
        resumen_frame.pack(fill=X, pady=5)
        
        self.lbl_resumen_memorias = ttk.Label(resumen_frame, text="💾 Memorias activas: 0", font=('Segoe UI', 9))
        self.lbl_resumen_memorias.pack(side=LEFT, padx=15)
        
        self.lbl_resumen_copias = ttk.Label(resumen_frame, text="📋 Copias hoy: 0", font=('Segoe UI', 9))
        self.lbl_resumen_copias.pack(side=LEFT, padx=15)
        
        self.lbl_resumen_ingresos = ttk.Label(resumen_frame, text="💰 Ingresos hoy: $0.00", font=('Segoe UI', 9, 'bold'), foreground='#27ae60')
        self.lbl_resumen_ingresos.pack(side=LEFT, padx=15)
    
    def crear_pestana_memorias(self):
        """Crea la pestaña de gestión de memorias"""
        parent = self.pestana_memorias
        
        frame_lista = ttk.LabelFrame(parent, text="💾 Base de Memorias", padding=10)
        frame_lista.pack(fill=BOTH, expand=True, pady=5)
        
        self.tree_memorias = ttk.Treeview(
            frame_lista,
            columns=('Nombre', 'Serial', 'Veces', 'Total_GB', 'Ingresos', 'Ultima'),
            show='headings',
            height=10
        )
        
        self.tree_memorias.heading('Nombre', text='Nombre')
        self.tree_memorias.heading('Serial', text='Serial ID')
        self.tree_memorias.heading('Veces', text='Veces Usada')
        self.tree_memorias.heading('Total_GB', text='Total GB')
        self.tree_memorias.heading('Ingresos', text='Ingresos')
        self.tree_memorias.heading('Ultima', text='Última Conexión')
        
        self.tree_memorias.column('Nombre', width=150)
        self.tree_memorias.column('Serial', width=100)
        self.tree_memorias.column('Veces', width=80)
        self.tree_memorias.column('Total_GB', width=80)
        self.tree_memorias.column('Ingresos', width=80)
        self.tree_memorias.column('Ultima', width=120)
        
        scroll_y = ttk.Scrollbar(frame_lista, orient=VERTICAL, command=self.tree_memorias.yview)
        self.tree_memorias.configure(yscrollcommand=scroll_y.set)
        
        self.tree_memorias.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)
        
        self.tree_memorias.bind('<<TreeviewSelect>>', self.on_seleccionar_memoria_db)
        
        action_frame = ttk.Frame(frame_lista)
        action_frame.pack(fill=X, pady=5)
        
        ttk.Button(action_frame, text="🔄 Actualizar Lista", command=self.actualizar_lista_memorias).pack(side=LEFT, padx=5)
        ttk.Button(action_frame, text="✏️ Editar Nombre", command=self.editar_nombre_memoria).pack(side=LEFT, padx=5)
        ttk.Button(action_frame, text="📊 Ver Historial", command=self.ver_historial_memoria).pack(side=LEFT, padx=5)
        ttk.Button(action_frame, text="🗑️ Eliminar", command=self.eliminar_memoria).pack(side=LEFT, padx=5)
        
        frame_detalles = ttk.LabelFrame(parent, text="📋 Detalles de Memoria", padding=10)
        frame_detalles.pack(fill=X, pady=5)
        
        self.txt_detalles_memoria = scrolledtext.ScrolledText(
            frame_detalles,
            height=5,
            wrap=WORD,
            font=('Consolas', 9),
            bg='#2b2b2b' if BOOTSTRAP_AVAILABLE else 'white',
            fg='white' if BOOTSTRAP_AVAILABLE else 'black'
        )
        self.txt_detalles_memoria.pack(fill=BOTH, expand=True)
        self.txt_detalles_memoria.config(state=DISABLED)
    
    def crear_pestana_estadisticas(self):
        """Crea la pestaña de estadísticas"""
        parent = self.pestana_estadisticas
        
        frame_general = ttk.LabelFrame(parent, text="📊 Estadísticas Generales", padding=10)
        frame_general.pack(fill=BOTH, expand=True, pady=5)
        
        stats_grid = ttk.Frame(frame_general)
        stats_grid.pack(fill=X, pady=10)
        
        row1 = ttk.Frame(stats_grid)
        row1.pack(fill=X, pady=5)
        
        self.lbl_stats_total_copias = ttk.Label(row1, text="📋 Total Copias: 0", font=('Segoe UI', 10))
        self.lbl_stats_total_copias.pack(side=LEFT, padx=20)
        
        self.lbl_stats_total_gb = ttk.Label(row1, text="💾 Total GB: 0.00", font=('Segoe UI', 10))
        self.lbl_stats_total_gb.pack(side=LEFT, padx=20)
        
        self.lbl_stats_total_ingresos = ttk.Label(row1, text="💰 Total Ingresos: $0.00", font=('Segoe UI', 10, 'bold'), foreground='#27ae60')
        self.lbl_stats_total_ingresos.pack(side=LEFT, padx=20)
        
        row2 = ttk.Frame(stats_grid)
        row2.pack(fill=X, pady=5)
        
        self.lbl_stats_memorias_activas = ttk.Label(row2, text="💾 Memorias Activas: 0", font=('Segoe UI', 10))
        self.lbl_stats_memorias_activas.pack(side=LEFT, padx=20)
        
        self.lbl_stats_memoria_top = ttk.Label(row2, text="🏆 Memoria más usada: Ninguna", font=('Segoe UI', 10))
        self.lbl_stats_memoria_top.pack(side=LEFT, padx=20)
        
        self.lbl_stats_promedio = ttk.Label(row2, text="📈 Promedio diario: 0.00", font=('Segoe UI', 10))
        self.lbl_stats_promedio.pack(side=LEFT, padx=20)
        
        row3 = ttk.Frame(stats_grid)
        row3.pack(fill=X, pady=5)
        
        self.lbl_stats_ultimos_7 = ttk.Label(row3, text="📆 Últimos 7 días: 0 copias", font=('Segoe UI', 10))
        self.lbl_stats_ultimos_7.pack(side=LEFT, padx=20)
        
        self.lbl_stats_ultimos_30 = ttk.Label(row3, text="📆 Últimos 30 días: 0 copias", font=('Segoe UI', 10))
        self.lbl_stats_ultimos_30.pack(side=LEFT, padx=20)
        
        ttk.Button(frame_general, text="🔄 Actualizar Estadísticas", command=self.actualizar_estadisticas).pack(pady=10)
        
        frame_tendencias = ttk.LabelFrame(parent, text="📈 Tendencias Detectadas", padding=10)
        frame_tendencias.pack(fill=BOTH, expand=True, pady=5)
        
        self.txt_tendencias = scrolledtext.ScrolledText(
            frame_tendencias,
            height=8,
            wrap=WORD,
            font=('Consolas', 9),
            bg='#2b2b2b' if BOOTSTRAP_AVAILABLE else 'white',
            fg='white' if BOOTSTRAP_AVAILABLE else 'black'
        )
        self.txt_tendencias.pack(fill=BOTH, expand=True)
        self.txt_tendencias.config(state=DISABLED)
        
        self.actualizar_tendencias()
    
    def crear_pestana_historial(self):
        """Crea la pestaña de historial"""
        parent = self.pestana_historial
        
        frame_filtros = ttk.Frame(parent)
        frame_filtros.pack(fill=X, pady=5)
        
        ttk.Label(frame_filtros, text="Filtrar por fecha:").pack(side=LEFT, padx=5)
        
        ttk.Label(frame_filtros, text="Desde:").pack(side=LEFT, padx=5)
        self.filtro_fecha_ini = ttk.Entry(frame_filtros, width=15)
        self.filtro_fecha_ini.pack(side=LEFT, padx=5)
        self.filtro_fecha_ini.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Label(frame_filtros, text="Hasta:").pack(side=LEFT, padx=5)
        self.filtro_fecha_fin = ttk.Entry(frame_filtros, width=15)
        self.filtro_fecha_fin.pack(side=LEFT, padx=5)
        self.filtro_fecha_fin.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Button(frame_filtros, text="🔍 Filtrar", command=self.filtrar_historial).pack(side=LEFT, padx=5)
        ttk.Button(frame_filtros, text="📄 Exportar", command=self.exportar_historial_filtrado).pack(side=LEFT, padx=5)
        
        frame_historial = ttk.LabelFrame(parent, text="📜 Historial de Copias", padding=10)
        frame_historial.pack(fill=BOTH, expand=True, pady=5)
        
        self.historial_tree = ttk.Treeview(
            frame_historial,
            columns=('Fecha', 'Hora', 'Memoria', 'Unidad', 'GB', 'Precio', 'Estado'),
            show='headings',
            height=15
        )
        
        self.historial_tree.heading('Fecha', text='Fecha')
        self.historial_tree.heading('Hora', text='Hora')
        self.historial_tree.heading('Memoria', text='Memoria')
        self.historial_tree.heading('Unidad', text='Unidad')
        self.historial_tree.heading('GB', text='GB')
        self.historial_tree.heading('Precio', text='Precio')
        self.historial_tree.heading('Estado', text='Estado')
        
        self.historial_tree.column('Fecha', width=100)
        self.historial_tree.column('Hora', width=80)
        self.historial_tree.column('Memoria', width=150)
        self.historial_tree.column('Unidad', width=80)
        self.historial_tree.column('GB', width=80)
        self.historial_tree.column('Precio', width=80)
        self.historial_tree.column('Estado', width=100)
        
        scroll_y = ttk.Scrollbar(frame_historial, orient=VERTICAL, command=self.historial_tree.yview)
        self.historial_tree.configure(yscrollcommand=scroll_y.set)
        
        self.historial_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)
    
    def crear_barra_estado(self):
        """Crea la barra de estado"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=BOTTOM, fill=X, padx=10, pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="🟢 Sistema listo")
        self.status_label.pack(side=LEFT)
        
        # Información del creador en la barra de estado
        creador_status = ttk.Label(
            self.status_frame,
            text=f"👤 {CREATOR}",
            font=('Segoe UI', 8),
            foreground='#7f8c8d' if not BOOTSTRAP_AVAILABLE else None
        )
        creador_status.pack(side=LEFT, padx=20)
        
        self.precio_label = ttk.Label(
            self.status_frame,
            text=f"💰 Precio: ${self.config_manager.obtener_precio():.2f}/GB"
        )
        self.precio_label.pack(side=RIGHT)
    
    # ==================== MÉTODOS DE NOTIFICACIÓN ====================
    
    def mostrar_notificacion_exitosa(self, nombre_memoria, gb, precio):
        """Muestra una notificación de copia exitosa"""
        mensaje = f"""
💾 Memoria: {nombre_memoria}
📊 GB Copiados: {gb:.2f} GB
💰 Precio: ${precio:.2f}
✅ Estado: Completado
        """
        
        duracion = self.config_manager.obtener("notificaciones_duracion", 0)
        
        self.notifier.mostrar_notificacion(
            "✅ Copia Completada - Kalm-USB-Kopy",
            mensaje,
            duracion=duracion
        )
    
    def mostrar_notificacion_conexion(self, unidad, nombre_memoria):
        """Muestra una notificación de conexión USB"""
        mensaje = f"""
💾 Memoria: {nombre_memoria}
📌 Unidad: {unidad}
✅ Conectada correctamente
        """
        
        duracion = self.config_manager.obtener("notificaciones_duracion", 0)
        
        self.notifier.mostrar_notificacion(
            "🔮 Memoria USB Detectada",
            mensaje,
            duracion=duracion
        )
    
    # ==================== MÉTODOS DE INTERFAZ ====================
    
    def actualizar_unidades(self):
        """Actualiza la lista de unidades USB"""
        for item in self.lista_unidades.get_children():
            self.lista_unidades.delete(item)
        
        unidades = self.monitor.obtener_unidades_conectadas() if self.monitor else []
        
        if not unidades:
            self.lista_unidades.insert('', 0, values=('Ninguna', 'No hay', '-', '-', '-'))
            self.unidad_seleccionada = None
            self.btn_copiar.config(state=DISABLED)
            self.btn_iniciar_copia.config(state=DISABLED)
            self.lbl_memoria.config(text="Ninguna memoria conectada")
            return
        
        for unidad in unidades:
            mem_id, data = self.memory_manager.obtener_memoria_por_unidad(unidad['letra'])
            nombre = data.get('nombre', 'No registrada') if data else 'No registrada'
            
            self.lista_unidades.insert(
                '',
                END,
                values=(
                    unidad['letra'],
                    nombre,
                    f"{unidad['total_gb']:.2f}",
                    f"{unidad['usado_gb']:.2f}",
                    f"{unidad['libre_gb']:.2f}"
                ),
                tags=(unidad['letra'],)
            )
        
        if self.lista_unidades.get_children():
            self.lista_unidades.selection_set(self.lista_unidades.get_children()[0])
            self.on_seleccionar_unidad(None)
    
    def on_seleccionar_unidad(self, event):
        """Maneja la selección de una unidad"""
        selection = self.lista_unidades.selection()
        if not selection:
            return
        
        item = selection[0]
        valores = self.lista_unidades.item(item, 'values')
        
        if valores[0] == 'Ninguna' or valores[0] == 'No hay memorias':
            return
        
        self.unidad_seleccionada = valores[0]
        
        mem_id, data = self.memory_manager.obtener_memoria_por_unidad(valores[0])
        
        if data:
            nombre_memoria = data.get('nombre', 'Sin nombre')
            self.memoria_seleccionada_id = mem_id
            self.memoria_seleccionada_data = data
        else:
            # Si no existe, pedir nombre
            nombre_memoria = self.pedir_nombre_memoria(valores[0])
            mem_id, data = self.memory_manager.identificar_memoria(valores[0], nombre_memoria)
            self.memoria_seleccionada_id = mem_id
            self.memoria_seleccionada_data = data
        
        self.lbl_memoria.config(text=f"{nombre_memoria} ({valores[0]})")
        self.btn_copiar.config(state=NORMAL)
        self.btn_iniciar_copia.config(state=NORMAL)
        
        try:
            gb_libre = float(valores[3]) if valores[3] != '-' else 0
        except:
            gb_libre = 0
        
        self.lbl_gb_copiar.config(text=f"{gb_libre:.2f} GB")
        
        precio = gb_libre * self.config_manager.obtener_precio()
        self.lbl_precio_total.config(text=f"${precio:.2f}")
        
        self.actualizar_estado(f"Seleccionada: {nombre_memoria} - {valores[0]}")
    
    def pedir_nombre_memoria(self, unidad):
        """Pide el nombre para una nueva memoria"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Nueva Memoria Detectada - Kalm-USB-Kopy")
        ventana.geometry("400x200")
        ventana.transient(self.root)
        ventana.grab_set()
        
        # Icono K
        ttk.Label(ventana, text="⚔️ Kalm-USB-Kopy", font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        ttk.Label(ventana, text=f"Se ha detectado una nueva memoria en {unidad}").pack(pady=5)
        ttk.Label(ventana, text="Asigna un nombre para identificarla:").pack(pady=5)
        
        frame = ttk.Frame(ventana)
        frame.pack(pady=10, padx=20, fill=X)
        
        nombre_var = tk.StringVar(value=f"Memoria_{unidad.replace(':', '')}")
        entry_nombre = ttk.Entry(frame, textvariable=nombre_var, width=30, font=('Segoe UI', 10))
        entry_nombre.pack(anchor='w', pady=5)
        entry_nombre.focus()
        entry_nombre.select_range(0, tk.END)
        
        def guardar_nombre():
            nombre = nombre_var.get().strip()
            if not nombre:
                nombre = f"Memoria_{unidad.replace(':', '')}"
            ventana.destroy()
            self.nombre_memoria_pendiente = nombre
        
        def cancelar():
            ventana.destroy()
            self.nombre_memoria_pendiente = f"Memoria_{unidad.replace(':', '')}"
        
        btn_frame = ttk.Frame(ventana)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="✅ Guardar", command=guardar_nombre, style='success.TButton' if BOOTSTRAP_AVAILABLE else None).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=cancelar).pack(side=LEFT, padx=5)
        
        # Esperar a que se cierre la ventana
        ventana.wait_window()
        
        return getattr(self, 'nombre_memoria_pendiente', f"Memoria_{unidad.replace(':', '')}")
    
    def iniciar_copia(self):
        """Inicia el proceso de copia"""
        if not self.unidad_seleccionada:
            messagebox.showwarning("Advertencia", "Selecciona una memoria primero")
            return
        
        if self.copiando:
            messagebox.showinfo("Información", "Ya hay una copia en proceso")
            return
        
        if self.memoria_seleccionada_data and not self.memoria_seleccionada_data.get('nombre'):
            nombre = f"Memoria_{self.unidad_seleccionada.replace(':', '')}"
            self.memory_manager.memorias[self.memoria_seleccionada_id]['nombre'] = nombre
            self.memory_manager.guardar_memorias()
        
        ventana = tk.Toplevel(self.root)
        ventana.title("Configurar Copia - Kalm-USB-Kopy")
        ventana.geometry("450x320")
        ventana.transient(self.root)
        ventana.grab_set()
        
        ttk.Label(ventana, text="⚔️ Configuración de Copia", font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        try:
            uso = psutil.disk_usage(self.unidad_seleccionada)
            libre_gb = bytes_a_gb(uso.free)
        except:
            libre_gb = 0
        
        frame = ttk.Frame(ventana)
        frame.pack(pady=10, padx=20, fill=X)
        
        ttk.Label(frame, text=f"💾 Memoria: {self.lbl_memoria.cget('text')}").pack(anchor='w', pady=2)
        ttk.Label(frame, text=f"📊 Espacio libre: {libre_gb:.2f} GB").pack(anchor='w', pady=2)
        
        ttk.Label(frame, text="GB a copiar:").pack(anchor='w', pady=(10, 0))
        gb_var = tk.StringVar(value=f"{min(libre_gb, 10):.2f}")
        entry_gb = ttk.Entry(frame, textvariable=gb_var, width=15, font=('Segoe UI', 11))
        entry_gb.pack(anchor='w', pady=5)
        entry_gb.focus()
        
        precio_frame = ttk.Frame(ventana)
        precio_frame.pack(pady=10, fill=X, padx=20)
        
        ttk.Label(precio_frame, text="💰 Precio estimado:").pack(side=LEFT)
        lbl_precio_estimado = ttk.Label(
            precio_frame,
            text=f"${float(gb_var.get()) * self.config_manager.obtener_precio():.2f}",
            font=('Segoe UI', 13, 'bold'),
            foreground='#27ae60' if not BOOTSTRAP_AVAILABLE else None
        )
        lbl_precio_estimado.pack(side=LEFT, padx=10)
        
        def actualizar_precio(*args):
            try:
                gb = float(gb_var.get())
                precio = gb * self.config_manager.obtener_precio()
                lbl_precio_estimado.config(text=f"${precio:.2f}")
            except:
                pass
        
        gb_var.trace('w', actualizar_precio)
        
        opciones_frame = ttk.Frame(ventana)
        opciones_frame.pack(pady=10, fill=X, padx=20)
        
        ttk.Label(opciones_frame, text="📝 Opciones:").pack(anchor='w')
        
        incluir_subcarpetas = tk.BooleanVar(value=True)
        ttk.Checkbutton(opciones_frame, text="Incluir subcarpetas", variable=incluir_subcarpetas).pack(anchor='w')
        
        btn_frame = ttk.Frame(ventana)
        btn_frame.pack(pady=20)
        
        def confirmar_copia():
            try:
                gb_copiar = float(gb_var.get())
                if gb_copiar <= 0:
                    messagebox.showerror("Error", "Ingresa una cantidad válida")
                    return
                if gb_copiar > libre_gb:
                    messagebox.showerror("Error", "No hay suficiente espacio libre")
                    return
                
                ventana.destroy()
                
                precio = gb_copiar * self.config_manager.obtener_precio()
                nombre_memoria = self.memoria_seleccionada_data.get('nombre', 'Sin nombre') if self.memoria_seleccionada_data else 'Sin nombre'
                
                registro = {
                    'nombre_memoria': nombre_memoria,
                    'unidad': self.unidad_seleccionada,
                    'gb_copiados': round(gb_copiar, 2),
                    'precio': round(precio, 2),
                    'hora': datetime.datetime.now().strftime("%H:%M:%S"),
                    'estado': 'Completado'
                }
                
                self.history_manager.agregar_registro(registro)
                
                if self.memoria_seleccionada_id:
                    self.memory_manager.registrar_copia(
                        self.memoria_seleccionada_id,
                        gb_copiar,
                        precio
                    )
                
                self.registro_actual = registro
                self.actualizar_historial()
                self.actualizar_lista_memorias()
                self.actualizar_estadisticas()
                self.actualizar_resumen()
                
                # MOSTRAR NOTIFICACIÓN EMERGENTE
                self.mostrar_notificacion_exitosa(nombre_memoria, gb_copiar, precio)
                
                messagebox.showinfo(
                    "✅ Copia Registrada",
                    f"Copia registrada exitosamente!\n\n"
                    f"📁 Memoria: {nombre_memoria}\n"
                    f"💾 GB Copiados: {gb_copiar:.2f}\n"
                    f"💰 Precio: ${precio:.2f}\n"
                    f"🕐 Hora: {registro['hora']}\n\n"
                    f"💡 Se ha enviado una notificación emergente."
                )
                
                self.lbl_progreso.config(text="✅ Copia registrada")
                self.actualizar_estado(f"Copia registrada - ${precio:.2f}")
                
            except ValueError:
                messagebox.showerror("Error", "Ingresa un número válido")
        
        ttk.Button(btn_frame, text="✅ Confirmar Copia", command=confirmar_copia, style='success.TButton' if BOOTSTRAP_AVAILABLE else None).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=ventana.destroy).pack(side=LEFT, padx=5)
    
    def cancelar_copia(self):
        """Cancela la copia en curso"""
        self.copiando = False
        self.btn_iniciar_copia.config(state=NORMAL)
        self.btn_cancelar.config(state=DISABLED)
        self.progress_bar['value'] = 0
        self.lbl_progreso.config(text="Copia cancelada")
        self.actualizar_estado("Copia cancelada")
    
    def guardar_registro_manual(self):
        """Guarda un registro manual"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Registro Manual - Kalm-USB-Kopy")
        ventana.geometry("500x400")
        ventana.transient(self.root)
        ventana.grab_set()
        
        ttk.Label(ventana, text="📝 Registro Manual", font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        frame = ttk.Frame(ventana)
        frame.pack(pady=10, padx=20, fill=X)
        
        ttk.Label(frame, text="💾 Memoria:").pack(anchor='w')
        entry_memoria = ttk.Entry(frame, width=40)
        entry_memoria.pack(anchor='w', pady=5)
        entry_memoria.insert(0, f"Manual_{datetime.datetime.now().strftime('%H%M%S')}")
        
        ttk.Label(frame, text="📊 GB Copiados:").pack(anchor='w')
        entry_gb = ttk.Entry(frame, width=15)
        entry_gb.pack(anchor='w', pady=5)
        
        ttk.Label(frame, text="💰 Precio:").pack(anchor='w')
        lbl_precio_manual = ttk.Label(frame, text="$0.00", font=('Segoe UI', 11, 'bold'), foreground='#27ae60')
        lbl_precio_manual.pack(anchor='w', pady=5)
        
        def actualizar_precio_manual(*args):
            try:
                gb = float(entry_gb.get())
                precio = gb * self.config_manager.obtener_precio()
                lbl_precio_manual.config(text=f"${precio:.2f}")
            except:
                pass
        
        entry_gb.bind('<KeyRelease>', actualizar_precio_manual)
        
        def guardar_manual():
            try:
                nombre = entry_memoria.get().strip()
                gb = float(entry_gb.get())
                precio = gb * self.config_manager.obtener_precio()
                
                if not nombre:
                    nombre = f"Manual_{datetime.datetime.now().strftime('%H%M%S')}"
                
                if gb <= 0:
                    messagebox.showerror("Error", "Ingresa una cantidad válida")
                    return
                
                mem_id = None
                for mid, data in self.memory_manager.memorias.items():
                    if data.get('nombre') == nombre:
                        mem_id = mid
                        break
                
                if not mem_id:
                    mem_id, data = self.memory_manager.identificar_memoria(f"Manual_{int(time.time())}", nombre)
                
                self.memory_manager.registrar_copia(mem_id, gb, precio)
                
                registro = {
                    'nombre_memoria': nombre,
                    'unidad': 'Manual',
                    'gb_copiados': round(gb, 2),
                    'precio': round(precio, 2),
                    'hora': datetime.datetime.now().strftime("%H:%M:%S"),
                    'estado': 'Manual'
                }
                
                self.history_manager.agregar_registro(registro)
                self.registro_actual = registro
                self.actualizar_historial()
                self.actualizar_lista_memorias()
                self.actualizar_estadisticas()
                self.actualizar_resumen()
                
                ventana.destroy()
                messagebox.showinfo("✅ Éxito", "Registro manual guardado correctamente")
                
            except ValueError:
                messagebox.showerror("Error", "Ingresa un número válido para GB")
        
        btn_frame = ttk.Frame(ventana)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="💾 Guardar", command=guardar_manual, style='success.TButton' if BOOTSTRAP_AVAILABLE else None).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=ventana.destroy).pack(side=LEFT, padx=5)
    
    def analizar_memoria(self):
        """Analiza el contenido de la memoria seleccionada"""
        if not self.unidad_seleccionada:
            messagebox.showwarning("Advertencia", "Primero selecciona una memoria")
            return
        
        try:
            uso = psutil.disk_usage(self.unidad_seleccionada)
            total_gb = bytes_a_gb(uso.total)
            usado_gb = bytes_a_gb(uso.used)
            libre_gb = bytes_a_gb(uso.free)
            
            nombre = self.memoria_seleccionada_data.get('nombre', 'No registrada') if self.memoria_seleccionada_data else 'No registrada'
            
            mensaje = f"""
🔍 ANÁLISIS DE MEMORIA
📌 Unidad: {self.unidad_seleccionada}
💾 Nombre: {nombre}
📊 Capacidad Total: {total_gb:.2f} GB
📁 Espacio Usado: {usado_gb:.2f} GB
💾 Espacio Libre: {libre_gb:.2f} GB
💰 Valor Estimado: ${libre_gb * self.config_manager.obtener_precio():.2f}
🔄 Veces usada: {self.memoria_seleccionada_data.get('veces_usada', 0) if self.memoria_seleccionada_data else 0}
            """
            
            messagebox.showinfo("Análisis de Memoria", mensaje)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo analizar la memoria: {str(e)}")
    
    # ==================== MÉTODOS DE GESTIÓN DE MEMORIAS ====================
    
    def actualizar_lista_memorias(self):
        """Actualiza la lista de memorias"""
        for item in self.tree_memorias.get_children():
            self.tree_memorias.delete(item)
        
        memorias = self.memory_manager.obtener_todas_memorias()
        
        if not memorias:
            self.tree_memorias.insert('', 0, values=('No hay memorias', '', '', '', '', ''))
            return
        
        for mem_id, data in memorias.items():
            ultima = data.get('ultima_conexion', 'Nunca')
            try:
                ultima = datetime.datetime.fromisoformat(ultima).strftime("%Y-%m-%d %H:%M")
            except:
                ultima = 'Nunca'
            
            self.tree_memorias.insert(
                '',
                END,
                values=(
                    data.get('nombre', 'Sin nombre'),
                    data.get('serial', '')[:8],
                    data.get('veces_usada', 0),
                    f"{data.get('total_gb_copiados', 0):.2f}",
                    f"${data.get('total_ingresos', 0):.2f}",
                    ultima
                ),
                tags=(mem_id,)
            )
    
    def on_seleccionar_memoria_db(self, event):
        """Maneja la selección de una memoria en la base de datos"""
        selection = self.tree_memorias.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree_memorias.item(item, 'values')
        mem_id = self.tree_memorias.item(item, 'tags')[0]
        
        if values[0] == 'No hay memorias':
            return
        
        data = self.memory_manager.memorias.get(mem_id)
        if data:
            self.mostrar_detalles_memoria(mem_id, data)
    
    def mostrar_detalles_memoria(self, mem_id, data):
        """Muestra los detalles de una memoria"""
        self.txt_detalles_memoria.config(state=NORMAL)
        self.txt_detalles_memoria.delete(1.0, END)
        
        historico = data.get('historico', [])
        
        detalles = f"""
📋 DETALLES DE MEMORIA
========================
🆔 ID: {mem_id}
📌 Nombre: {data.get('nombre', 'Sin nombre')}
🔑 Serial: {data.get('serial', 'N/A')}
📁 Unidad: {data.get('unidad', 'N/A')}

📊 ESTADÍSTICAS
========================
📅 Fecha registro: {data.get('fecha_registro', 'N/A')}
🔄 Veces usada: {data.get('veces_usada', 0)}
💾 Total GB copiados: {data.get('total_gb_copiados', 0):.2f}
💰 Total ingresos: ${data.get('total_ingresos', 0):.2f}
🕐 Última conexión: {data.get('ultima_conexion', 'N/A')}

📈 HISTORIAL DE COPIAS (Últimas 10)
========================
        """
        
        if historico:
            for i, reg in enumerate(historico[-10:], 1):
                try:
                    fecha = datetime.datetime.fromisoformat(reg['fecha']).strftime("%Y-%m-%d %H:%M")
                except:
                    fecha = reg.get('fecha', 'N/A')
                detalles += f"{i}. {fecha} | {reg.get('gb', 0):.2f} GB | ${reg.get('precio', 0):.2f}\n"
        else:
            detalles += "No hay registros de copias\n"
        
        self.txt_detalles_memoria.insert(1.0, detalles)
        self.txt_detalles_memoria.config(state=DISABLED)
    
    def editar_nombre_memoria(self):
        """Edita el nombre de una memoria"""
        selection = self.tree_memorias.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una memoria primero")
            return
        
        item = selection[0]
        mem_id = self.tree_memorias.item(item, 'tags')[0]
        data = self.memory_manager.memorias.get(mem_id)
        
        if not data:
            return
        
        ventana = tk.Toplevel(self.root)
        ventana.title("Editar Nombre de Memoria")
        ventana.geometry("400x150")
        ventana.transient(self.root)
        ventana.grab_set()
        
        ttk.Label(ventana, text="Editar Nombre de Memoria", font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        frame = ttk.Frame(ventana)
        frame.pack(pady=10, padx=20, fill=X)
        
        ttk.Label(frame, text="Nuevo nombre:").pack(anchor='w')
        nombre_var = tk.StringVar(value=data.get('nombre', ''))
        entry_nombre = ttk.Entry(frame, textvariable=nombre_var, width=30)
        entry_nombre.pack(anchor='w', pady=5)
        entry_nombre.focus()
        
        def guardar_nombre():
            nuevo_nombre = nombre_var.get().strip()
            if not nuevo_nombre:
                messagebox.showerror("Error", "El nombre no puede estar vacío")
                return
            
            self.memory_manager.memorias[mem_id]['nombre'] = nuevo_nombre
            self.memory_manager.guardar_memorias()
            self.actualizar_lista_memorias()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Nombre actualizado correctamente")
        
        btn_frame = ttk.Frame(ventana)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="💾 Guardar", command=guardar_nombre).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=ventana.destroy).pack(side=LEFT, padx=5)
    
    def ver_historial_memoria(self):
        """Muestra el historial completo de una memoria"""
        selection = self.tree_memorias.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una memoria primero")
            return
        
        item = selection[0]
        mem_id = self.tree_memorias.item(item, 'tags')[0]
        data = self.memory_manager.memorias.get(mem_id)
        
        if not data:
            return
        
        ventana = tk.Toplevel(self.root)
        ventana.title(f"Historial - {data.get('nombre', 'Memoria')}")
        ventana.geometry("800x500")
        ventana.transient(self.root)
        
        frame = ttk.Frame(ventana)
        frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        text_area = scrolledtext.ScrolledText(
            frame,
            wrap=WORD,
            font=('Consolas', 10),
            bg='#2b2b2b' if BOOTSTRAP_AVAILABLE else 'white',
            fg='white' if BOOTSTRAP_AVAILABLE else 'black'
        )
        text_area.pack(fill=BOTH, expand=True)
        
        text_area.insert(END, "="*70 + "\n")
        text_area.insert(END, f"📜 HISTORIAL DE: {data.get('nombre', 'Memoria')}\n")
        text_area.insert(END, "="*70 + "\n\n")
        
        stats = self.memory_manager.obtener_estadisticas_memoria(mem_id)
        if stats:
            text_area.insert(END, "📊 RESUMEN:\n")
            text_area.insert(END, f"   Total de copias: {stats['total_copias']}\n")
            text_area.insert(END, f"   Total GB: {stats['total_gb']:.2f}\n")
            text_area.insert(END, f"   Total ingresos: ${stats['total_ingresos']:.2f}\n")
            text_area.insert(END, f"   Promedio por copia: {stats['promedio_gb']:.2f} GB\n\n")
        
        text_area.insert(END, "📋 DETALLE DE COPIAS:\n")
        text_area.insert(END, "-"*70 + "\n")
        
        historico = data.get('historico', [])
        if historico:
            for i, reg in enumerate(historico, 1):
                try:
                    fecha = datetime.datetime.fromisoformat(reg['fecha']).strftime("%Y-%m-%d %H:%M")
                except:
                    fecha = reg.get('fecha', 'N/A')
                
                text_area.insert(
                    END,
                    f"{i:3d}. {fecha} | {reg.get('gb', 0):6.2f} GB | ${reg.get('precio', 0):7.2f}\n"
                )
        else:
            text_area.insert(END, "No hay registros de copias para esta memoria\n")
        
        text_area.config(state=DISABLED)
        ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=10)
    
    def eliminar_memoria(self):
        """Elimina una memoria de la base de datos"""
        selection = self.tree_memorias.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una memoria primero")
            return
        
        item = selection[0]
        mem_id = self.tree_memorias.item(item, 'tags')[0]
        data = self.memory_manager.memorias.get(mem_id)
        
        if not data:
            return
        
        if messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar la memoria '{data.get('nombre', '')}'?\n\n"
            f"Esto eliminará todo su historial y estadísticas.\n"
            f"Esta acción no se puede deshacer."
        ):
            del self.memory_manager.memorias[mem_id]
            self.memory_manager.guardar_memorias()
            self.actualizar_lista_memorias()
            messagebox.showinfo("Éxito", "Memoria eliminada correctamente")
    
    # ==================== MÉTODOS DE ESTADÍSTICAS ====================
    
    def actualizar_estadisticas(self):
        """Actualiza las estadísticas"""
        stats = self.data_analyzer.obtener_estadisticas_completas()
        
        self.lbl_stats_total_copias.config(text=f"📋 Total Copias: {stats.get('total_copias', 0)}")
        self.lbl_stats_total_gb.config(text=f"💾 Total GB: {stats.get('total_gb', 0):.2f}")
        self.lbl_stats_total_ingresos.config(text=f"💰 Total Ingresos: ${stats.get('total_ingresos', 0):.2f}")
        self.lbl_stats_memorias_activas.config(text=f"💾 Memorias Activas: {stats.get('memorias_activas', 0)}")
        self.lbl_stats_memoria_top.config(text=f"🏆 Memoria más usada: {stats.get('memoria_mas_usada', 'Ninguna')}")
        self.lbl_stats_promedio.config(text=f"📈 Promedio diario: {stats.get('promedio_diario', 0):.2f}")
        self.lbl_stats_ultimos_7.config(text=f"📆 Últimos 7 días: {stats.get('copias_ultimos_7_dias', 0)} copias")
        self.lbl_stats_ultimos_30.config(text=f"📆 Últimos 30 días: {stats.get('copias_ultimos_30_dias', 0)} copias")
    
    def actualizar_tendencias(self):
        """Actualiza el panel de tendencias"""
        self.txt_tendencias.config(state=NORMAL)
        self.txt_tendencias.delete(1.0, END)
        
        stats = self.data_analyzer.obtener_estadisticas_completas()
        
        tendencias = f"""
        📈 ANÁLISIS DE TENDENCIAS - {APP_NAME}
        ============================
        
        """
        
        if stats.get('total_copias', 0) > 0:
            tendencias += f"✅ Total de copias realizadas: {stats['total_copias']}\n"
            tendencias += f"✅ Total de GB copiados: {stats['total_gb']:.2f}\n"
            tendencias += f"✅ Total de ingresos generados: ${stats['total_ingresos']:.2f}\n\n"
            
            tendencias += "📊 PATRONES DETECTADOS:\n"
            tendencias += "-" * 40 + "\n"
            
            if stats.get('promedio_diario', 0) > 1:
                tendencias += "🔹 Alta actividad diaria (más de 1 copia por día)\n"
            elif stats.get('promedio_diario', 0) > 0.5:
                tendencias += "🔹 Actividad moderada (1 copia cada 2 días)\n"
            else:
                tendencias += "🔹 Baja actividad (menos de 1 copia cada 2 días)\n"
            
            if stats.get('copias_ultimos_7_dias', 0) > stats.get('copias_ultimos_30_dias', 0) / 4:
                tendencias += "🔹 Tendencia al alza en los últimos 7 días\n"
            
            if stats.get('memoria_mas_usada'):
                tendencias += f"🔹 Memoria más popular: {stats['memoria_mas_usada']}\n"
            
            tendencias += "\n📅 RECOMENDACIONES:\n"
            tendencias += "-" * 40 + "\n"
            
            if stats.get('promedio_diario', 0) < 1:
                tendencias += "💡 Considera promocionar el servicio para aumentar ventas\n"
            
            if stats.get('memorias_activas', 0) < 3:
                tendencias += "💡 Incentiva a los clientes a usar memorias identificables\n"
            
            tendencias += "💡 Genera informes diarios para mantener control financiero\n"
        else:
            tendencias += "Aún no hay datos suficientes para generar tendencias.\n"
            tendencias += "Comienza a registrar copias para ver análisis aquí."
        
        self.txt_tendencias.insert(1.0, tendencias)
        self.txt_tendencias.config(state=DISABLED)
    
    def actualizar_historial(self, fecha_ini=None, fecha_fin=None):
        """Actualiza el historial"""
        for item in self.historial_tree.get_children():
            self.historial_tree.delete(item)
        
        if fecha_ini and fecha_fin:
            registros = []
            for reg in self.history_manager.historial:
                try:
                    fecha = datetime.datetime.fromisoformat(reg['fecha']).date()
                    if fecha_ini <= fecha <= fecha_fin:
                        registros.append(reg)
                except:
                    pass
        else:
            registros = self.history_manager.historial[-200:]
        
        if not registros:
            self.historial_tree.insert('', 0, values=('', 'No hay registros', '', '', '', '', ''))
            return
        
        for registro in registros:
            try:
                fecha = datetime.datetime.fromisoformat(registro['fecha'])
                fecha_str = fecha.strftime("%Y-%m-%d")
                hora_str = fecha.strftime("%H:%M:%S")
            except:
                fecha_str = 'N/A'
                hora_str = registro.get('hora', 'N/A')
            
            self.historial_tree.insert(
                '',
                'end',
                values=(
                    fecha_str,
                    hora_str,
                    registro.get('nombre_memoria', 'N/A'),
                    registro.get('unidad', 'N/A'),
                    f"{registro.get('gb_copiados', 0):.2f}",
                    f"${registro.get('precio', 0):.2f}",
                    registro.get('estado', 'Completado')
                )
            )
    
    def actualizar_resumen(self):
        """Actualiza el resumen rápido"""
        fecha = datetime.datetime.now().date().isoformat()
        registros = self.history_manager.obtener_diario(fecha)
        
        total_gb = sum(r.get('gb_copiados', 0) for r in registros)
        total_precio = sum(r.get('precio', 0) for r in registros)
        
        memorias_activas = len([m for m in self.memory_manager.memorias.values() if m.get('veces_usada', 0) > 0])
        
        self.lbl_resumen_memorias.config(text=f"💾 Memorias activas: {memorias_activas}")
        self.lbl_resumen_copias.config(text=f"📋 Copias hoy: {len(registros)}")
        self.lbl_resumen_ingresos.config(text=f"💰 Ingresos hoy: ${total_precio:.2f}")
    
    def filtrar_historial(self):
        """Filtra el historial por fecha"""
        try:
            fecha_ini = datetime.datetime.strptime(self.filtro_fecha_ini.get(), "%Y-%m-%d").date()
            fecha_fin = datetime.datetime.strptime(self.filtro_fecha_fin.get(), "%Y-%m-%d").date()
            self.actualizar_historial(fecha_ini, fecha_fin)
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha incorrecto. Usa YYYY-MM-DD")
    
    def exportar_historial_filtrado(self):
        """Exporta el historial filtrado"""
        try:
            import csv
            
            fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre = f"historial_filtrado_{fecha}.csv"
            
            export_dir = os.path.join(os.path.expanduser("~"), "Documentos", "Kalm_Export")
            os.makedirs(export_dir, exist_ok=True)
            
            ruta = os.path.join(export_dir, nombre)
            
            with open(ruta, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Fecha', 'Hora', 'Memoria', 'Unidad', 'GB', 'Precio', 'Estado'])
                
                for item in self.historial_tree.get_children():
                    values = self.historial_tree.item(item, 'values')
                    if values and values[0] != 'No hay registros':
                        writer.writerow(values)
            
            messagebox.showinfo("✅ Exportación", f"Historial exportado a:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
    
    # ==================== MÉTODOS DE CONFIGURACIÓN ====================
    
    def cambiar_tema(self):
        """Abre el selector de temas con temas válidos"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Cambiar Tema - Kalm-USB-Kopy")
        ventana.geometry("550x500")
        ventana.transient(self.root)
        ventana.grab_set()
        
        ttk.Label(ventana, text="🎨 Cambiar Tema", font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        if BOOTSTRAP_AVAILABLE:
            frame = ttk.Frame(ventana)
            frame.pack(pady=10, padx=20, fill=BOTH, expand=True)
            
            ttk.Label(frame, text="Selecciona un tema:").pack(anchor='w', pady=5)
            
            tema_actual = self.config_manager.obtener("tema", "darkly")
            tema_var = tk.StringVar(value=tema_actual)
            
            # Grid de temas (usando TEMAS_VALIDOS)
            temas_frame = ttk.Frame(frame)
            temas_frame.pack(fill=BOTH, expand=True, pady=10)
            
            # Mostrar temas en 3 columnas
            for i, tema in enumerate(TEMAS_VALIDOS):
                row = i // 3
                col = i % 3
                
                btn = ttk.Radiobutton(
                    temas_frame,
                    text=tema.capitalize(),
                    variable=tema_var,
                    value=tema
                )
                btn.grid(row=row, column=col, sticky='w', padx=10, pady=5)
            
            # Vista previa del tema
            preview_frame = ttk.LabelFrame(frame, text="Vista Previa del Tema", padding=10)
            preview_frame.pack(fill=X, pady=10)
            
            preview_inner = ttk.Frame(preview_frame)
            preview_inner.pack(fill=X, pady=5)
            
            lbl_preview = ttk.Label(preview_inner, text="Texto de ejemplo - Kalm-USB-Kopy")
            lbl_preview.pack()
            btn_preview = ttk.Button(preview_inner, text="Botón de prueba")
            btn_preview.pack(pady=5)
            
            def actualizar_vista_previa(*args):
                """Actualiza la vista previa con el tema seleccionado"""
                nuevo_tema = tema_var.get()
                if nuevo_tema in TEMAS_VALIDOS:
                    try:
                        # Crear estilo temporal para vista previa
                        temp_style = tb.Style(theme=nuevo_tema)
                        # Actualizar los widgets de vista previa
                        preview_inner.configure(style='TFrame')
                        lbl_preview.configure(style='TLabel')
                        btn_preview.configure(style='TButton')
                        preview_inner.update()
                    except Exception as e:
                        print(f"Error en vista previa: {e}")
            
            tema_var.trace('w', actualizar_vista_previa)
            
            def aplicar_tema():
                nuevo_tema = tema_var.get()
                if nuevo_tema not in TEMAS_VALIDOS:
                    messagebox.showerror("Error", f"El tema '{nuevo_tema}' no es válido")
                    return
                
                self.config_manager.establecer("tema", nuevo_tema)
                
                # Aplicar tema sin reiniciar
                if self.aplicar_tema():
                    # Actualizar todos los widgets
                    self.root.update_idletasks()
                    ventana.destroy()
                    messagebox.showinfo(
                        "✅ Tema Aplicado",
                        f"El tema '{nuevo_tema}' se ha aplicado correctamente."
                    )
                else:
                    messagebox.showerror("Error", "No se pudo aplicar el tema. Reintenta.")
            
            btn_frame = ttk.Frame(ventana)
            btn_frame.pack(pady=20)
            
            ttk.Button(btn_frame, text="✅ Aplicar Tema", command=aplicar_tema, style='success.TButton' if BOOTSTRAP_AVAILABLE else None).pack(side=LEFT, padx=5)
            ttk.Button(btn_frame, text="❌ Cancelar", command=ventana.destroy).pack(side=LEFT, padx=5)
        else:
            ttk.Label(ventana, text="❌ ttkbootstrap no está instalado").pack(pady=20)
            ttk.Label(ventana, text="Instala: pip install ttkbootstrap").pack(pady=10)
            ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=10)
    
    def abrir_config_precio(self):
        """Abre la configuración de precio"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Configurar Precio por GB")
        ventana.geometry("400x250")
        ventana.transient(self.root)
        ventana.grab_set()
        
        ttk.Label(ventana, text="⚙️ Configurar Precio", font=('Segoe UI', 12, 'bold')).pack(pady=20)
        
        frame = ttk.Frame(ventana)
        frame.pack(pady=20, padx=30, fill=X)
        
        ttk.Label(frame, text="Precio por GB (CUP):").pack(anchor='w')
        
        precio_var = tk.StringVar(value=str(self.config_manager.obtener_precio()))
        entry_precio = ttk.Entry(frame, textvariable=precio_var, width=15, font=('Segoe UI', 12))
        entry_precio.pack(anchor='w', pady=5)
        
        ejemplo_frame = ttk.Frame(ventana)
        ejemplo_frame.pack(pady=10, fill=X, padx=30)
        
        ttk.Label(ejemplo_frame, text="Ejemplo:").pack(anchor='w')
        lbl_ejemplo = ttk.Label(ejemplo_frame, text="1 GB = $5.00 CUP", font=('Segoe UI', 10, 'bold'))
        lbl_ejemplo.pack(anchor='w')
        
        def actualizar_ejemplo(*args):
            try:
                precio = float(precio_var.get())
                lbl_ejemplo.config(text=f"1 GB = ${precio:.2f} CUP")
            except:
                pass
        
        precio_var.trace('w', actualizar_ejemplo)
        
        def guardar_precio():
            try:
                precio = float(precio_var.get())
                if precio <= 0:
                    messagebox.showerror("Error", "El precio debe ser mayor a 0")
                    return
                
                self.config_manager.establecer_precio(precio)
                self.lbl_precio_gb.config(text=f"${precio:.2f}")
                self.precio_label.config(text=f"💰 Precio: ${precio:.2f}/GB")
                ventana.destroy()
                messagebox.showinfo("Éxito", f"Precio actualizado a ${precio:.2f} por GB")
            except ValueError:
                messagebox.showerror("Error", "Ingresa un número válido")
        
        btn_frame = ttk.Frame(ventana)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="💾 Guardar", command=guardar_precio, style='success.TButton' if BOOTSTRAP_AVAILABLE else None).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=ventana.destroy).pack(side=LEFT, padx=5)
    
    def abrir_config_general(self):
        """Abre la configuración general"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Configuración General - Kalm-USB-Kopy")
        ventana.geometry("550x500")
        ventana.transient(self.root)
        ventana.grab_set()
        
        ttk.Label(ventana, text="⚙️ Configuración General", font=('Segoe UI', 12, 'bold')).pack(pady=20)
        
        notebook = ttk.Notebook(ventana)
        notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña General
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        
        ttk.Label(general_frame, text="Configuración del Sistema", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=10, padx=10)
        
        ttk.Label(general_frame, text="📁 Carpeta de respaldo:").pack(anchor='w', padx=10)
        backup_frame = ttk.Frame(general_frame)
        backup_frame.pack(fill=X, padx=10, pady=5)
        
        backup_var = tk.StringVar(value=self.config_manager.obtener("carpeta_respaldo", ""))
        entry_backup = ttk.Entry(backup_frame, textvariable=backup_var, width=40)
        entry_backup.pack(side=LEFT, fill=X, expand=True)
        
        def seleccionar_carpeta():
            carpeta = filedialog.askdirectory(title="Seleccionar carpeta de respaldo")
            if carpeta:
                backup_var.set(carpeta)
        
        ttk.Button(backup_frame, text="📁 Buscar", command=seleccionar_carpeta).pack(side=LEFT, padx=5)
        
        ttk.Label(general_frame, text="Opciones:", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=10, padx=10)
        
        auto_detectar = tk.BooleanVar(value=self.config_manager.obtener("auto_detectar", True))
        ttk.Checkbutton(general_frame, text="Detectar memorias automáticamente", variable=auto_detectar).pack(anchor='w', padx=10)
        
        notificaciones = tk.BooleanVar(value=self.config_manager.obtener("mostrar_notificaciones", True))
        ttk.Checkbutton(general_frame, text="Mostrar notificaciones emergentes", variable=notificaciones).pack(anchor='w', padx=10)
        
        # Pestaña Notificaciones
        notif_frame = ttk.Frame(notebook)
        notebook.add(notif_frame, text="🔔 Notificaciones")
        
        ttk.Label(notif_frame, text="Configuración de Notificaciones", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=10, padx=10)
        
        ttk.Label(notif_frame, text="Duración de notificaciones (segundos):").pack(anchor='w', padx=10)
        ttk.Label(notif_frame, text="(0 = no se cierra automáticamente)", font=('Segoe UI', 8)).pack(anchor='w', padx=10)
        
        duracion_var = tk.StringVar(value=str(self.config_manager.obtener("notificaciones_duracion", 0)))
        entry_duracion = ttk.Entry(notif_frame, textvariable=duracion_var, width=10)
        entry_duracion.pack(anchor='w', padx=10, pady=5)
        
        ttk.Label(notif_frame, text="Vista previa de notificación:").pack(anchor='w', padx=10, pady=10)
        
        def probar_notificacion():
            self.notifier.mostrar_notificacion(
                "🔔 Notificación de Prueba",
                "Esta es una notificación de prueba.\n"
                "Presiona la X para cerrarla."
            )
        
        ttk.Button(notif_frame, text="🔔 Probar Notificación", command=probar_notificacion).pack(anchor='w', padx=10)
        
        # Pestaña Avanzado
        avanzado_frame = ttk.Frame(notebook)
        notebook.add(avanzado_frame, text="Avanzado")
        
        ttk.Label(avanzado_frame, text="Configuración Avanzada", font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=10, padx=10)
        
        max_historial = tk.StringVar(value=str(self.config_manager.obtener("max_historial", 10000)))
        ttk.Label(avanzado_frame, text="Máximo de registros en historial:").pack(anchor='w', padx=10)
        ttk.Entry(avanzado_frame, textvariable=max_historial, width=15).pack(anchor='w', padx=10, pady=5)
        
        formato_informe = tk.StringVar(value=self.config_manager.obtener("formato_informe", "txt"))
        ttk.Label(avanzado_frame, text="Formato de informes:").pack(anchor='w', padx=10)
        ttk.Combobox(avanzado_frame, textvariable=formato_informe, values=['txt', 'csv', 'json'], state='readonly', width=10).pack(anchor='w', padx=10, pady=5)
        
        btn_frame = ttk.Frame(ventana)
        btn_frame.pack(pady=20)
        
        def guardar_config_general():
            self.config_manager.establecer("carpeta_respaldo", backup_var.get())
            self.config_manager.establecer("auto_detectar", auto_detectar.get())
            self.config_manager.establecer("mostrar_notificaciones", notificaciones.get())
            try:
                self.config_manager.establecer("notificaciones_duracion", int(duracion_var.get()))
            except:
                pass
            try:
                self.config_manager.establecer("max_historial", int(max_historial.get()))
            except:
                pass
            self.config_manager.establecer("formato_informe", formato_informe.get())
            
            ventana.destroy()
            messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
        
        ttk.Button(btn_frame, text="💾 Guardar", command=guardar_config_general, style='success.TButton' if BOOTSTRAP_AVAILABLE else None).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=ventana.destroy).pack(side=LEFT, padx=5)
    
    def toggle_inicio_windows(self):
        """Activa o desactiva el inicio con Windows"""
        actual = self.config_manager.obtener("iniciar_con_windows", False)
        
        if actual:
            self.quitar_inicio_windows()
            self.config_manager.establecer("iniciar_con_windows", False)
            messagebox.showinfo("Información", "Inicio con Windows desactivado")
        else:
            self.agregar_inicio_windows()
            self.config_manager.establecer("iniciar_con_windows", True)
            messagebox.showinfo("Información", "Inicio con Windows activado")
        
        self.actualizar_estado(f"Inicio con Windows: {'Activado' if not actual else 'Desactivado'}")
    
    def toggle_bandeja(self):
        """Activa o desactiva la minimización a bandeja"""
        actual = self.config_manager.obtener("minimizar_bandeja", True)
        nuevo = not actual
        self.config_manager.establecer("minimizar_bandeja", nuevo)
        
        estado = "activada" if nuevo else "desactivada"
        messagebox.showinfo("Información", f"Minimización a bandeja {estado}")
    
    def agregar_inicio_windows(self):
        """Agrega el programa al inicio de Windows"""
        try:
            ruta_exe = sys.executable
            if not ruta_exe.endswith('.exe'):
                ruta_exe = os.path.abspath(sys.argv[0])
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "KalmUSBKopy", 0, winreg.REG_SZ, f'"{ruta_exe}"')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar al inicio: {str(e)}")
    
    def quitar_inicio_windows(self):
        """Quita el programa del inicio de Windows"""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, "KalmUSBKopy")
        except:
            pass
    
    # ==================== MÉTODOS DE HERRAMIENTAS ====================
    
    def analizar_tendencias(self):
        """Analiza y muestra tendencias"""
        self.actualizar_tendencias()
        self.actualizar_estadisticas()
        messagebox.showinfo("Análisis Completado", "El análisis de tendencias se ha actualizado correctamente.")
    
    def limpiar_historial(self):
        """Limpia el historial antiguo"""
        if messagebox.askyesno(
            "Limpiar Historial",
            "¿Estás seguro de limpiar el historial antiguo?\n\n"
            "Esto eliminará todos los registros de más de 1 año.\n"
            "Los registros de este año se mantendrán."
        ):
            ahora = datetime.datetime.now()
            limite = ahora - datetime.timedelta(days=365)
            
            nuevos_historial = []
            for reg in self.history_manager.historial:
                try:
                    fecha = datetime.datetime.fromisoformat(reg['fecha'])
                    if fecha > limite:
                        nuevos_historial.append(reg)
                except:
                    nuevos_historial.append(reg)
            
            self.history_manager.historial = nuevos_historial
            self.history_manager.guardar_historial()
            self.actualizar_historial()
            messagebox.showinfo("Éxito", f"Historial limpiado. Se mantuvieron {len(nuevos_historial)} registros.")
    
    def respaldar_datos(self):
        """Crea un respaldo de todos los datos"""
        try:
            fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"backup_kalm_{fecha}"
            os.makedirs(backup_dir, exist_ok=True)
            
            archivos = [CONFIG_FILE, HISTORY_FILE, MEMORY_DB, STATS_FILE]
            for archivo in archivos:
                if os.path.exists(archivo):
                    shutil.copy2(archivo, os.path.join(backup_dir, archivo))
            
            messagebox.showinfo(
                "✅ Respaldo Completado",
                f"Respaldo creado exitosamente.\n\n"
                f"📁 Ubicación: {backup_dir}\n"
                f"📦 Archivos respaldados: {len(archivos)}\n\n"
                f"Recomendación: Guarda esta carpeta en un lugar seguro."
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el respaldo: {str(e)}")
    
    def exportar_memorias(self):
        """Exporta la base de datos de memorias"""
        try:
            fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre = f"base_memorias_{fecha}.json"
            
            export_dir = os.path.join(os.path.expanduser("~"), "Documentos", "Kalm_Export")
            os.makedirs(export_dir, exist_ok=True)
            
            ruta = os.path.join(export_dir, nombre)
            
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(self.memory_manager.memorias, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("✅ Exportación", f"Base de memorias exportada a:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
    
    def generar_informe(self):
        """Genera un informe diario"""
        try:
            fecha = datetime.datetime.now().date().isoformat()
            
            informe = self.report_generator.generar_informe_diario(fecha)
            
            stats = self.data_analyzer.obtener_estadisticas_completas()
            informe += "\n\n📊 ESTADÍSTICAS DE MEMORIAS\n"
            informe += "="*60 + "\n\n"
            informe += f"Total de copias: {stats.get('total_copias', 0)}\n"
            informe += f"Total de GB: {stats.get('total_gb', 0):.2f}\n"
            informe += f"Total ingresos: ${stats.get('total_ingresos', 0):.2f}\n"
            informe += f"Memorias activas: {stats.get('memorias_activas', 0)}\n"
            
            if stats.get('memoria_mas_usada'):
                informe += f"Memoria más usada: {stats['memoria_mas_usada']}\n"
            
            ruta = self.report_generator.guardar_informe(fecha)
            
            messagebox.showinfo(
                "📄 Informe Generado",
                f"Informe diario generado exitosamente.\n\n"
                f"📁 Ubicación: {ruta}\n"
                f"📊 Incluye estadísticas completas\n\n"
                "¿Deseas abrirlo ahora?"
            )
            
            if messagebox.askyesno("Abrir Informe", "¿Abrir el informe?"):
                os.startfile(ruta)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el informe: {str(e)}")
    
    def ver_historial(self):
        """Muestra el historial completo"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Historial Completo - Kalm-USB-Kopy")
        ventana.geometry("900x500")
        ventana.transient(self.root)
        
        frame = ttk.Frame(ventana)
        frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        text_area = scrolledtext.ScrolledText(
            frame,
            wrap=WORD,
            font=('Consolas', 10),
            bg='#2b2b2b' if BOOTSTRAP_AVAILABLE else 'white',
            fg='white' if BOOTSTRAP_AVAILABLE else 'black'
        )
        text_area.pack(fill=BOTH, expand=True)
        
        text_area.insert(END, "="*70 + "\n")
        text_area.insert(END, f"📜 HISTORIAL COMPLETO - {APP_NAME}\n")
        text_area.insert(END, "="*70 + "\n\n")
        
        historial = self.history_manager.historial
        if not historial:
            text_area.insert(END, "No hay registros en el historial\n")
        else:
            fecha_actual = ""
            for registro in historial:
                try:
                    fecha = datetime.datetime.fromisoformat(registro['fecha']).date().isoformat()
                except:
                    fecha = registro.get('fecha', '')[:10]
                
                if fecha != fecha_actual:
                    fecha_actual = fecha
                    text_area.insert(END, f"\n📅 FECHA: {fecha}\n")
                    text_area.insert(END, "-"*70 + "\n")
                
                text_area.insert(
                    END,
                    f"🕐 {registro.get('hora', '')} | "
                    f"💾 {registro.get('nombre_memoria', '')} | "
                    f"📊 {registro.get('gb_copiados', 0):.2f} GB | "
                    f"💰 ${registro.get('precio', 0):.2f} | "
                    f"📌 {registro.get('estado', '')}\n"
                )
        
        text_area.config(state=DISABLED)
        ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=10)
    
    def exportar_csv(self):
        """Exporta el historial a CSV"""
        try:
            import csv
            
            fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre = f"historial_export_{fecha}.csv"
            
            export_dir = os.path.join(os.path.expanduser("~"), "Documentos", "Kalm_Export")
            os.makedirs(export_dir, exist_ok=True)
            
            ruta = os.path.join(export_dir, nombre)
            
            with open(ruta, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Fecha', 'Hora', 'Memoria', 'Unidad', 'GB_Copiados', 'Precio', 'Estado'])
                
                for registro in self.history_manager.historial:
                    try:
                        fecha = datetime.datetime.fromisoformat(registro['fecha']).strftime("%Y-%m-%d")
                        hora = datetime.datetime.fromisoformat(registro['fecha']).strftime("%H:%M:%S")
                    except:
                        fecha = registro.get('fecha', '')[:10]
                        hora = registro.get('hora', '')
                    
                    writer.writerow([
                        fecha,
                        hora,
                        registro.get('nombre_memoria', ''),
                        registro.get('unidad', ''),
                        registro.get('gb_copiados', 0),
                        registro.get('precio', 0),
                        registro.get('estado', '')
                    ])
            
            messagebox.showinfo(
                "✅ Exportación Completa",
                f"Historial exportado exitosamente.\n\n"
                f"📁 Ubicación: {ruta}"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
    
    # ==================== MÉTODOS DE SISTEMA ====================
    
    def iniciar_monitoreo(self):
        """Inicia el monitoreo de USB"""
        self.monitor = USBMonitor(self.on_usb_conectado, self.on_usb_desconectado)
        self.monitor.iniciar()
        self.actualizar_estado("Monitoreo USB activo")
    
    def on_usb_conectado(self, unidad):
        """Maneja la conexión de una USB"""
        self.root.after(0, lambda: self.actualizar_unidades())
        self.root.after(0, lambda: self.actualizar_estado(f"USB conectada: {unidad}"))
        
        # Mostrar notificación de conexión
        if self.config_manager.obtener("mostrar_notificaciones", True):
            # Obtener nombre de la memoria
            mem_id, data = self.memory_manager.obtener_memoria_por_unidad(unidad)
            nombre = data.get('nombre', 'Nueva memoria') if data else 'Nueva memoria'
            self.mostrar_notificacion_conexion(unidad, nombre)
    
    def on_usb_desconectado(self, unidad):
        """Maneja la desconexión de una USB"""
        self.root.after(0, lambda: self.actualizar_unidades())
        self.root.after(0, lambda: self.actualizar_estado(f"USB desconectada: {unidad}"))
    
    def actualizar_estado(self, mensaje=None):
        """Actualiza la barra de estado"""
        if mensaje:
            self.status_label.config(text=f"🟢 {mensaje}")
        else:
            self.status_label.config(text="🟢 Sistema listo")
    
    def cargar_configuracion(self):
        """Carga la configuración inicial"""
        self.precio_label.config(text=f"💰 Precio: ${self.config_manager.obtener_precio():.2f}/GB")
        
        os.makedirs(REPORT_DIR, exist_ok=True)
        
        self.actualizar_historial()
        self.actualizar_lista_memorias()
        self.actualizar_resumen()
    
    def mostrar_acerca(self):
        """Muestra información acerca del programa"""
        mensaje = f"""
        ⚔️ KALM-USB-KOPY ⚔️
        Gestor de Memorias USB
        Versión {APP_VERSION}
        
        🧙‍♂️ Inspirado en:
        - Tensei Shitara Slime Datta Ken
        - Overlord
        
        👤 Creador: {CREATOR}
        📧 Email: {EMAIL}
        
        🔮 CARACTERÍSTICAS AVANZADAS:
        ✓ Monitoreo automático de USB
        ✓ Identificación inteligente de memorias
        ✓ Notificaciones emergentes Windows
        ✓ Cálculo automático de precios
        ✓ Historial completo por memoria
        ✓ Análisis de tendencias
        ✓ Informes diarios detallados
        ✓ Inicio con Windows
        ✓ Minimización a bandeja
        ✓ Temas en tiempo real
        ✓ Icono personalizado con letra K
        
        💰 Configuración por defecto:
        - 1 GB = $5.00 CUP
        
        📊 ESTADÍSTICAS INTELIGENTES:
        • Seguimiento de memorias frecuentes
        • Patrones de uso
        • Recomendaciones automáticas
        
        🎨 Diseño inspirado en fantasía oscura
        
        © 2026 - Todos los derechos reservados
        """
        messagebox.showinfo(f"Acerca de {APP_NAME}", mensaje)
    
    def mostrar_manual(self):
        """Muestra el manual rápido"""
        manual = f"""
        📖 MANUAL RÁPIDO - {APP_NAME}
        
        1. CONECTAR UNA MEMORIA
           ✓ El programa detectará automáticamente la USB
           ✓ Aparecerá en la lista de memorias conectadas
           ✓ Se identificará automáticamente
           ✓ Recibirás una notificación emergente
           ✓ Podrás asignar un nombre personalizado
        
        2. COPIAR DATOS
           ✓ Selecciona la memoria de la lista
           ✓ Haz clic en "Iniciar Copia"
           ✓ Ingresa la cantidad de GB a copiar
           ✓ El precio se calculará automáticamente
           ✓ El registro se guarda automáticamente
           ✓ Recibirás una notificación emergente al finalizar
        
        3. GESTIÓN DE MEMORIAS
           ✓ Accede a "Memorias" para ver todas las memorias registradas
           ✓ Edita el nombre para identificar mejor a cada cliente
           ✓ Ver historial completo de cada memoria
           ✓ Analiza patrones de uso de cada cliente
        
        4. ESTADÍSTICAS Y TENDENCIAS
           ✓ Estadísticas generales del negocio
           ✓ Análisis de patrones de uso
           ✓ Detección de tendencias
           ✓ Recomendaciones automáticas
        
        5. INFORMES
           ✓ Genera informes diarios completos
           ✓ Incluye estadísticas detalladas
           ✓ Exporta en diferentes formatos
        
        6. CONFIGURACIÓN
           ✓ Precio por GB: Menú Configuración
           ✓ Inicio con Windows: Menú Configuración
           ✓ Carpeta de respaldo: Configuración General
           ✓ Minimización a bandeja: Configuración
           ✓ Cambiar Tema: Menú Configuración
           ✓ Duración de notificaciones: Configuración General > Notificaciones
        
        7. HERRAMIENTAS AVANZADAS
           ✓ Analizar Tendencias: Detecta patrones de uso
           ✓ Limpiar Historial: Elimina registros antiguos
           ✓ Respaldo de Datos: Crea copia de seguridad
           ✓ Exportar Base de Memorias: Guarda la información
        
        ⚡ ¡Sistema completamente automático e inteligente!
        
        📧 Para soporte: {EMAIL}
        """
        messagebox.showinfo(f"Manual Rápido - {APP_NAME}", manual)
    
    def mostrar_estadisticas_sistema(self):
        """Muestra estadísticas detalladas del sistema"""
        stats = self.data_analyzer.obtener_estadisticas_completas()
        
        mensaje = f"""
📊 ESTADÍSTICAS DEL SISTEMA - {APP_NAME}
============================

📋 TOTALES:
   - Copias realizadas: {stats.get('total_copias', 0)}
   - GB copiados: {stats.get('total_gb', 0):.2f}
   - Ingresos generados: ${stats.get('total_ingresos', 0):.2f}

💾 MEMORIAS:
   - Registradas: {len(self.memory_manager.memorias)}
   - Activas: {stats.get('memorias_activas', 0)}
   - Más usada: {stats.get('memoria_mas_usada', 'Ninguna')}

📈 TENDENCIAS:
   - Promedio diario: {stats.get('promedio_diario', 0):.2f} copias
   - Últimos 7 días: {stats.get('copias_ultimos_7_dias', 0)} copias
   - Últimos 30 días: {stats.get('copias_ultimos_30_dias', 0)} copias

⚙️ CONFIGURACIÓN:
   - Precio por GB: ${self.config_manager.obtener_precio():.2f}
   - Inicio con Windows: {'Sí' if self.config_manager.obtener('iniciar_con_windows', False) else 'No'}
   - Bandeja: {'Sí' if self.config_manager.obtener('minimizar_bandeja', True) else 'No'}
   - Tema: {self.config_manager.obtener('tema', 'darkly')}
   - Notificaciones: {'Activadas' if self.config_manager.obtener('mostrar_notificaciones', True) else 'Desactivadas'}
   - Duración notificaciones: {self.config_manager.obtener('notificaciones_duracion', 0)} segundos

👤 INFORMACIÓN:
   - Creador: {CREATOR}
   - Email: {EMAIL}
   - Versión: {APP_VERSION}
        """
        
        messagebox.showinfo("Estadísticas del Sistema", mensaje)

# ==================== FUNCIÓN PRINCIPAL ====================

def main():
    """Función principal"""
    # Verificar dependencias
    if not BOOTSTRAP_AVAILABLE:
        print("⚠️ ttkbootstrap no está instalado. Instala: pip install ttkbootstrap")
    
    if not NOTIFICATION_AVAILABLE:
        print("⚠️ plyer no está instalado. Instala: pip install plyer")
    
    # Crear ventana principal
    root = tk.Tk() if not BOOTSTRAP_AVAILABLE else tb.Window()
    
    # Configurar título
    root.title(f"{APP_NAME} - Gestor de Memorias USB")
    
    # Crear aplicación
    app = KalmUSBKopy(root)
    
    # Iniciar loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        if hasattr(app, 'monitor') and app.monitor:
            app.monitor.detener()
        sys.exit(0)

if __name__ == "__main__":
    main()

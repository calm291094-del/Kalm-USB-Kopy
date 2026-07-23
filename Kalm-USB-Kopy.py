"""
Kalm-USB-Kopy · Nexus Pro v6.0.0
Arquitectura: Modular · Reactiva · Autónoma
Estética: Dark Glassmorphism + Neón Orgánico
Creador: Carlos A. Lorenzo Marro
"""

import os, sys, json, shutil, datetime, threading, time, subprocess, winreg
import hashlib, tempfile, csv, io, math, textwrap
from pathlib import Path
from collections import defaultdict, OrderedDict
from typing import Optional, Dict, List, Tuple, Any

import psutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

# ── Dependencias opcionales ──────────────────────────────────────────
try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    BOOTSTRAP = True
except ImportError:
    BOOTSTRAP = False

try:
    from plyer import notification
    PLYER = True
except ImportError:
    PLYER = False

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
    PYSTRAY = True
except ImportError:
    PYSTRAY = False

# ══════════════════════════════════════════════════════════════════════
#  PALETA DE DISEÑO — Dark Glassmorphism + Neón Orgánico
# ══════════════════════════════════════════════════════════════════════
class Palette:
    """Sistema de colores centralizado y coherente."""
    # Fondos
    BG_DEEP      = "#06060c"
    BG_PRIMARY   = "#0c0c16"
    BG_CARD      = "#12121f"
    BG_CARD_HOVER= "#181830"
    BG_ELEVATED  = "#1a1a2c"
    BG_INPUT     = "#0e0e1a"
    BG_TERMINAL  = "#040408"
    # Bordes
    BORDER       = "#1e1e36"
    BORDER_FOCUS = "#b026ff"
    # Texto
    TEXT_PRIMARY  = "#e8e8f0"
    TEXT_SECONDARY= "#8888a8"
    TEXT_DIM      = "#55556e"
    TEXT_ON_ACCENT= "#ffffff"
    # Acentos
    ACCENT_PRIMARY  = "#a855f7"   # Púrpura
    ACCENT_SECONDARY= "#06b6d4"   # Cian
    ACCENT_SUCCESS  = "#10b981"   # Verde
    ACCENT_WARNING  = "#f59e0b"   # Ámbar
    ACCENT_DANGER   = "#ef4444"   # Rojo
    ACCENT_INFO     = "#3b82f6"   # Azul
    # Gradientes (simulados)
    GRADIENT_START = "#7c3aed"
    GRADIENT_END   = "#06b6d4"
    # Neón
    NEON_GLOW_PURPLE = "#c084fc"
    NEON_GLOW_CYAN   = "#22d3ee"
    NEON_GLOW_GREEN  = "#34d399"

P = Palette

# ══════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN Y CONSTANTES
# ══════════════════════════════════════════════════════════════════════
APP_NAME    = "Kalm-USB-Kopy"
APP_VERSION = "6.0.0"
CREATOR     = "Carlos A. Lorenzo Marro"
EMAIL       = "klorenzo29@nauta.cu"

CONFIG_FILE = "config_kalm.json"
HISTORY_FILE= "historial_kalm.json"
MEMORY_DB   = "memorias_kalm.db"
REPORT_DIR  = "reportes_kalm"
BACKUP_DIR  = "backups_kalm"

# Tramos de precio inteligente (GB → precio CUP)
PRECIO_TRAMOS = [
    (0,    1,   5.00),
    (1,    2,  10.00),
    (2,    4,  25.00),
    (4,    8,  50.00),
    (8,   16,  100.00),
    (16,  32,  200.00),
    (32,  64,  400.00),
    (64, 128,  800.00),
    (128,256, 1600.00),
    (256,512, 3200.00),
    (512,1024,6400.00),
]

DEFAULT_CONFIG = {
    "precio_por_gb": 5.0,
    "moneda": "CUP",
    "iniciar_con_windows": True,
    "tema": "cyborg",
    "auto_detectar": True,
    "mostrar_notificaciones": True,
    "minimizar_bandeja": True,
    "max_historial": 10000,
    "notificaciones_duracion": 5,
    "radar_sensibilidad": 5,      # MB mínimos para detectar copia
    "radar_espera_final": 6,      # Segundos de inactividad para considerar copia terminada
    "auto_backup": True,
    "backup_interval_horas": 6,
    "sonido_notificacion": False,
    "tramos_personalizados": [],
}

# ══════════════════════════════════════════════════════════════════════
#  UTILIDADES
# ══════════════════════════════════════════════════════════════════════
def bytes_a_gb(b: int) -> float:
    return round(b / (1024**3), 2)

def calcular_precio(gb: float, tramos: list = None) -> float:
    """Calcula precio usando tramos predefinidos o personalizados."""
    if tramos is None:
        tramos = PRECIO_TRAMOS
    for gmin, gmax, precio in tramos:
        if gmin <= gb <= gmax:
            return precio
    # Si no coincide ningún tramo, interpolar linealmente
    if gb < PRECIO_TRAMOS[0][0]:
        return gb * PRECIO_TRAMOS[0][2]
    ultimo = PRECIO_TRAMOS[-1]
    if gb > ultimo[1]:
        return gb * (ultimo[2] / ultimo[1])
    # Interpolación entre tramos
    for i in range(len(tramos) - 1):
        if tramos[i][1] < gb < tramos[i+1][0]:
            ratio = (gb - tramos[i][1]) / (tramos[i+1][0] - tramos[i][1])
            return tramos[i][2] + ratio * (tramos[i+1][2] - tramos[i][2])
    return gb * 5.0

def formato_moneda(valor: float, moneda: str = "CUP") -> str:
    return f"${valor:.2f} {moneda}"

def timestamp_iso() -> str:
    return datetime.datetime.now().isoformat()

def timestamp_corto() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")

def fecha_iso() -> str:
    return datetime.datetime.now().date().isoformat()

def generar_id(prefijo: str = "ID") -> str:
    return f"{prefijo}_{int(time.time()*1000)}_{hashlib.md5(os.urandom(8)).hexdigest()[:6]}"

def clamp(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))

# ══════════════════════════════════════════════════════════════════════
#  GESTORES DE DATOS — Persistencia segura
# ══════════════════════════════════════════════════════════════════════
class SafeFileIO:
    """Escribe archivos JSON de forma atómica para evitar corrupción."""
    @staticmethod
    def write_json(path: str, data: dict):
        tmp = path + ".tmp"
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)

    @staticmethod
    def read_json(path: str, default=None) -> dict:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default if default is not None else {}


class ConfigManager:
    def __init__(self):
        self.data: dict = SafeFileIO.read_json(CONFIG_FILE, DEFAULT_CONFIG.copy())
        # Asegurar que todas las claves por defecto existan
        for k, v in DEFAULT_CONFIG.items():
            if k not in self.data:
                self.data[k] = v
        self.save()

    def save(self):
        SafeFileIO.write_json(CONFIG_FILE, self.data)

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value):
        self.data[key] = value
        self.save()

    @property
    def precio_base(self) -> float:
        return float(self.get("precio_por_gb", 5.0))

    @property
    def moneda(self) -> str:
        return self.get("moneda", "CUP")


class HistoryManager:
    def __init__(self, max_registros: int = 10000):
        self.data: List[dict] = SafeFileIO.read_json(HISTORY_FILE, [])
        self.max_registros = max_registros
        self._lock = threading.Lock()

    def save(self):
        with self._lock:
            # Truncar si excede el máximo
            if len(self.data) > self.max_registros:
                self.data = self.data[-self.max_registros:]
            SafeFileIO.write_json(HISTORY_FILE, self.data)

    def agregar(self, registro: dict):
        if 'fecha' not in registro:
            registro['fecha'] = timestamp_iso()
        if 'id' not in registro:
            registro['id'] = generar_id("REG")
        with self._lock:
            self.data.append(registro)
        self.save()

    def filtrar(self, fecha: str = None, estado: str = None,
                busqueda: str = None, limite: int = None) -> List[dict]:
        resultados = self.data
        if fecha:
            resultados = [r for r in resultados if r.get('fecha', '').startswith(fecha)]
        if estado:
            resultados = [r for r in resultados if r.get('estado') == estado]
        if busqueda:
            b = busqueda.lower()
            resultados = [r for r in resultados
                          if b in r.get('nombre_memoria', '').lower()
                          or b in r.get('unidad', '').lower()]
        if limite:
            resultados = resultados[-limite:]
        return list(reversed(resultados))

    def resumen_dia(self, fecha: str = None) -> dict:
        fecha = fecha or fecha_iso()
        regs = self.filtrar(fecha=fecha)
        total_gb = sum(r.get('gb_copiados', 0) for r in regs)
        total_precio = sum(r.get('precio', 0) for r in regs)
        internos = len([r for r in regs if r.get('estado') == 'Interno Completado'])
        externos = len([r for r in regs if r.get('estado') == 'Externo Completado'])
        return {
            'registros': len(regs),
            'total_gb': round(total_gb, 2),
            'total_precio': round(total_precio, 2),
            'internos': internos,
            'externos': externos,
            'items': regs
        }

    def resumen_semana(self) -> dict:
        hoy = datetime.datetime.now().date()
        regs = []
        for i in range(7):
            dia = (hoy - datetime.timedelta(days=i)).isoformat()
            regs.extend(self.filtrar(fecha=dia))
        total_gb = sum(r.get('gb_copiados', 0) for r in regs)
        total_precio = sum(r.get('precio', 0) for r in regs)
        return {'registros': len(regs), 'total_gb': round(total_gb, 2), 'total_precio': round(total_precio, 2)}

    def exportar_csv(self, ruta: str, registros: List[dict] = None):
        if registros is None:
            registros = self.data
        campos = ['id', 'fecha', 'nombre_memoria', 'unidad', 'gb_copiados', 'precio', 'estado', 'hora']
        with open(ruta, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=campos, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(registros)

    def limpiar_antiguos(self, dias: int = 90):
        """Elimina registros más antiguos que N días."""
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=dias)).isoformat()
        with self._lock:
            self.data = [r for r in self.data if r.get('fecha', '') >= cutoff]
        self.save()


class MemoryManager:
    def __init__(self):
        self.data: Dict[str, dict] = SafeFileIO.read_json(MEMORY_DB, {})
        self._lock = threading.Lock()

    def save(self):
        with self._lock:
            SafeFileIO.write_json(MEMORY_DB, self.data)

    def identificar(self, unidad: str, nombre: str = None) -> Tuple[str, dict]:
        serial = self._obtener_serial(unidad)
        # Buscar por serial
        for mid, m in self.data.items():
            if m.get('serial') == serial:
                m['ultima_conexion'] = timestamp_iso()
                self.save()
                return mid, m
        # Nueva memoria
        mid = generar_id("MEM")
        self.data[mid] = {
            'id': mid,
            'nombre': nombre or f"USB_{unidad.replace(':', '').upper()}",
            'serial': serial,
            'ultima_unidad': unidad,
            'fecha_registro': timestamp_iso(),
            'veces_usada': 0,
            'total_gb': 0.0,
            'total_ingresos': 0.0,
            'ultima_conexion': timestamp_iso(),
            'historico': [],
            'notas': ''
        }
        self.save()
        return mid, self.data[mid]

    def registrar_copia(self, mid: str, gb: float, precio: float):
        if mid not in self.data:
            return
        m = self.data[mid]
        m['historico'].append({
            'fecha': timestamp_iso(),
            'gb': gb,
            'precio': precio
        })
        m['veces_usada'] += 1
        m['total_gb'] = round(m['total_gb'] + gb, 2)
        m['total_ingresos'] = round(m['total_ingresos'] + precio, 2)
        self.save()

    def obtener_por_unidad(self, unidad: str) -> Tuple[Optional[str], Optional[dict]]:
        serial = self._obtener_serial(unidad)
        for mid, m in self.data.items():
            if m.get('serial') == serial:
                return mid, m
        return None, None

    def listar(self) -> List[Tuple[str, dict]]:
        return sorted(self.data.items(), key=lambda x: x[1].get('total_ingresos', 0), reverse=True)

    def renombrar(self, mid: str, nuevo_nombre: str):
        if mid in self.data:
            self.data[mid]['nombre'] = nuevo_nombre
            self.save()

    def eliminar(self, mid: str):
        if mid in self.data:
            del self.data[mid]
            self.save()

    def agregar_nota(self, mid: str, nota: str):
        if mid in self.data:
            self.data[mid]['notas'] = nota
            self.save()

    @staticmethod
    def _obtener_serial(unidad: str) -> str:
        try:
            import win32api
            info = win32api.GetVolumeInformation(unidad)
            return str(info[1])
        except Exception:
            return hashlib.md5(unidad.encode()).hexdigest()[:12]


class BackupManager:
    """Sistema de respaldo automático con rotación."""
    def __init__(self):
        os.makedirs(BACKUP_DIR, exist_ok=True)

    def crear_backup(self):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = f"backup_{ts}.zip"
        ruta = os.path.join(BACKUP_DIR, nombre)
        archivos = [f for f in [CONFIG_FILE, HISTORY_FILE, MEMORY_DB] if os.path.exists(f)]
        if not archivos:
            return None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                for f in archivos:
                    shutil.copy2(f, os.path.join(tmp, f))
                shutil.make_archive(ruta.replace('.zip', ''), 'zip', tmp)
            self._rotar_backups(max_kept=10)
            return ruta
        except Exception as e:
            print(f"Error creando backup: {e}")
            return None

    def restaurar_backup(self, ruta_zip: str) -> bool:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                shutil.unpack_archive(ruta_zip, tmp)
                for f in [CONFIG_FILE, HISTORY_FILE, MEMORY_DB]:
                    src = os.path.join(tmp, f)
                    if os.path.exists(src):
                        shutil.copy2(src, f)
            return True
        except Exception:
            return False

    def _rotar_backups(self, max_kept: int = 10):
        backups = sorted(Path(BACKUP_DIR).glob("backup_*.zip"), key=os.path.getmtime, reverse=True)
        for b in backups[max_kept:]:
            try:
                b.unlink()
            except Exception:
                pass

    def listar_backups(self) -> List[dict]:
        backups = []
        for p in sorted(Path(BACKUP_DIR).glob("backup_*.zip"), reverse=True):
            stat = p.stat()
            backups.append({
                'ruta': str(p),
                'nombre': p.name,
                'tamano': bytes_a_gb(stat.st_size),
                'fecha': datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            })
        return backups


# ══════════════════════════════════════════════════════════════════════
#  RADAR DE COPIAS EXTERNAS — Detección pasiva mejorada
# ══════════════════════════════════════════════════════════════════════
class CopyRadar:
    """Detecta copias hechas por programas externos monitoreando el delta de espacio usado."""
    def __init__(self, callback, config: ConfigManager):
        self.callback = callback
        self.config = config
        self.running = False
        self.thread = None
        self._baselines: Dict[str, float] = {}
        self._last_used: Dict[str, float] = {}
        self._deltas: Dict[str, float] = {}
        self._idle: Dict[str, int] = {}
        self.paused = False  # Se pausa durante copias internas

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def reset_drive(self, unidad: str):
        """Reinicia la línea base para una unidad (llamar tras conexión)."""
        self._baselines.pop(unidad, None)
        self._last_used.pop(unidad, None)
        self._deltas.pop(unidad, None)
        self._idle.pop(unidad, None)

    def _get_removable(self) -> List[str]:
        drives = []
        for p in psutil.disk_partitions():
            if 'removable' in p.opts:
                try:
                    psutil.disk_usage(p.mountpoint)  # Verificar accesibilidad
                    drives.append(p.mountpoint)
                except Exception:
                    pass
        return drives

    def _loop(self):
        sensibilidad_mb = self.config.get("radar_sensibilidad", 5)
        espera_seg = self.config.get("radar_espera_final", 6)
        umbral_gb = sensibilidad_mb / 1024.0

        while self.running:
            try:
                actuales = self._get_removable()
                # Limpiar desconectadas
                for d in list(self._baselines.keys()):
                    if d not in actuales:
                        for dic in (self._baselines, self._last_used, self._deltas, self._idle):
                            dic.pop(d, None)

                for d in actuales:
                    try:
                        uso = psutil.disk_usage(d)
                        used_gb = uso.used / (1024**3)

                        if d not in self._baselines:
                            self._baselines[d] = used_gb
                            self._last_used[d] = used_gb
                            self._deltas[d] = 0.0
                            self._idle[d] = 0
                            continue

                        delta = used_gb - self._last_used[d]

                        if delta > umbral_gb and not self.paused:
                            self._deltas[d] += delta
                            self._idle[d] = 0
                        else:
                            self._idle[d] += 2  # Intervalo de sleep

                        self._last_used[d] = used_gb

                        # Copia terminada: hubo delta y ahora hay inactividad
                        if self._deltas[d] > 0.01 and self._idle[d] >= espera_seg and not self.paused:
                            total = round(self._deltas[d], 2)
                            precio = calcular_precio(total)
                            self.callback(d, total, precio)
                            # Reset para siguiente copia
                            self._deltas[d] = 0.0
                            self._idle[d] = 0

                    except Exception:
                        pass
                time.sleep(2)
            except Exception:
                time.sleep(3)


# ══════════════════════════════════════════════════════════════════════
#  SISTEMA DE BANDEJA
# ══════════════════════════════════════════════════════════════════════
class TrayManager:
    def __init__(self, root, on_show, on_exit):
        self.root = root
        self.on_show = on_show
        self.on_exit = on_exit
        self.icon = None
        self.running = False
        self._img = self._make_icon()

    def _make_icon(self) -> 'Image.Image':
        try:
            img = Image.new('RGBA', (64, 64), (6, 6, 12, 255))
            draw = ImageDraw.Draw(img)
            # Fondo circular con borde neón
            draw.ellipse([2, 2, 62, 62], fill=(18, 18, 31, 255), outline=(168, 85, 247, 255), width=3)
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except Exception:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), "K", font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((64 - tw) // 2, (64 - th) // 2 - 2), "K", fill=(192, 132, 252, 255), font=font)
            return img
        except Exception:
            return Image.new('RGBA', (64, 64), (168, 85, 247, 255))

    def start(self):
        if not PYSTRAY or self.running:
            return
        try:
            menu = pystray.Menu(
                pystray.MenuItem("Mostrar Kalm-Nexus", self._show, default=True),
                pystray.MenuItem("Salir", self._exit)
            )
            self.icon = pystray.Icon("KalmNexus", self._img, "Kalm-USB-Kopy v6.0", menu)
            self.running = True
            threading.Thread(target=self.icon.run, daemon=True).start()
        except Exception as e:
            print(f"Error bandeja: {e}")

    def _show(self, icon=None, item=None):
        self.root.after(0, self._do_show)

    def _do_show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _exit(self, icon=None, item=None):
        self.running = False
        if self.icon:
            self.icon.stop()
        self.root.after(0, self.on_exit)

    def hide(self):
        self.root.withdraw()

    def stop(self):
        self.running = False
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════
#  WIDGETS PERSONALIZADOS — Glassmorphism moderno
# ══════════════════════════════════════════════════════════════════════
class GlassCard(tk.Frame):
    """Tarjeta con estilo glassmorphism."""
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=P.BG_CARD, highlightbackground=P.BORDER,
                         highlightthickness=1, padx=16, pady=12, **kw)
        self.bind('<Enter>', lambda e: self.config(highlightbackground=P.ACCENT_PRIMARY))
        self.bind('<Leave>', lambda e: self.config(highlightbackground=P.BORDER))


class StatCard(GlassCard):
    """Tarjeta de estadística con valor grande."""
    def __init__(self, parent, titulo: str, valor: str = "0", color: str = P.ACCENT_PRIMARY, **kw):
        super().__init__(parent, **kw)
        self.color = color
        self.lbl_titulo = tk.Label(self, text=titulo, bg=P.BG_CARD, fg=P.TEXT_SECONDARY,
                                   font=('Segoe UI', 9))
        self.lbl_titulo.pack(anchor='w')
        self.lbl_valor = tk.Label(self, text=valor, bg=P.BG_CARD, fg=color,
                                  font=('Consolas', 22, 'bold'))
        self.lbl_valor.pack(anchor='w', pady=(4, 0))
        self.lbl_sub = tk.Label(self, text="", bg=P.BG_CARD, fg=P.TEXT_DIM,
                                font=('Segoe UI', 8))
        self.lbl_sub.pack(anchor='w')

    def set_valor(self, valor: str, sub: str = ""):
        self.lbl_valor.config(text=valor)
        if sub:
            self.lbl_sub.config(text=sub)

    def pulse(self):
        """Efecto de pulso visual al actualizar."""
        original = self.lbl_valor.cget('fg')
        self.lbl_valor.config(fg='#ffffff')
        self.after(200, lambda: self.lbl_valor.config(fg=original))


class NeonButton(tk.Button):
    """Botón con estilo neón."""
    def __init__(self, parent, text: str, command=None, color: str = P.ACCENT_PRIMARY,
                 size: str = 'normal', **kw):
        fonts = {'small': ('Segoe UI', 9), 'normal': ('Segoe UI', 10, 'bold'),
                 'large': ('Segoe UI', 12, 'bold')}
        super().__init__(parent, text=text, command=command,
                         bg=color, fg=P.TEXT_ON_ACCENT,
                         activebackground=P.NEON_GLOW_PURPLE if color == P.ACCENT_PRIMARY else color,
                         activeforeground=P.TEXT_ON_ACCENT,
                         relief=tk.FLAT, cursor='hand2',
                         font=fonts.get(size, fonts['normal']),
                         padx=16, pady=8, **kw)
        self._color = color
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

    def _on_enter(self, e):
        self.config(bg=P.NEON_GLOW_PURPLE if self._color == P.ACCENT_PRIMARY else self._color)

    def _on_leave(self, e):
        self.config(bg=self._color)


class GhostButton(tk.Button):
    """Botón transparente con borde."""
    def __init__(self, parent, text: str, command=None, **kw):
        super().__init__(parent, text=text, command=command,
                         bg=P.BG_CARD, fg=P.TEXT_SECONDARY,
                         activebackground=P.BG_CARD_HOVER, activeforeground=P.TEXT_PRIMARY,
                         relief=tk.FLAT, cursor='hand2',
                         font=('Segoe UI', 9), padx=12, pady=6, **kw)
        self.bind('<Enter>', lambda e: self.config(fg=P.ACCENT_PRIMARY))
        self.bind('<Leave>', lambda e: self.config(fg=P.TEXT_SECONDARY))


class ModernTreeview(ttk.Treeview):
    """Treeview con estilo mejorado."""
    def __init__(self, parent, columns, **kw):
        super().__init__(parent, columns=columns, show='headings', **kw)
        if BOOTSTRAP:
            self.style = tb.Style()
            self.style.configure('Modern.Treeview', background=P.BG_CARD, foreground=P.TEXT_PRIMARY,
                                fieldbackground=P.BG_CARD, rowheight=32, borderwidth=0,
                                font=('Segoe UI', 9))
            self.style.configure('Modern.Treeview.Heading', background=P.BG_ELEVATED,
                                foreground=P.ACCENT_SECONDARY, font=('Segoe UI', 9, 'bold'),
                                borderwidth=0, relief=tk.FLAT)
            self.style.map('Modern.Treeview',
                          background=[('selected', P.ACCENT_PRIMARY)],
                          foreground=[('selected', P.TEXT_ON_ACCENT)])
            self.config(style='Modern.Treeview')


# ══════════════════════════════════════════════════════════════════════
#  VISUALIZACIÓN ASCII — Gráficos en terminal
# ══════════════════════════════════════════════════════════════════════
class AsciiChart:
    """Genera gráficos de barras en ASCII para la terminal."""
    @staticmethod
    def barras_horizontales(datos: List[Tuple[str, float]], ancho: int = 30,
                           char: str = "█", color_map: dict = None) -> str:
        if not datos:
            return "  Sin datos"
        max_val = max(v for _, v in datos) or 1
        lineas = []
        for label, val in datos:
            lleno = int((val / max_val) * ancho)
            barra = char * lleno + "░" * (ancho - lleno)
            lineas.append(f"  {label:<12} {barra} {val:.1f}")
        return "\n".join(lineas)

    @staticmethod
    def sparkline(valores: List[float], ancho: int = 40) -> str:
        if len(valores) < 2:
            return "·" * ancho
        chars = "▁▂▃▄▅▆▇█"
        min_v, max_v = min(valores), max(valores)
        rango = max_v - min_v or 1
        normalizados = [(v - min_v) / rango for v in valores]
        # Reducir a 'ancho' puntos
        paso = max(1, len(normalizados) // ancho)
        reducidos = [normalizados[i] for i in range(0, len(normalizados), paso)][:ancho]
        return "".join(chars[int(clamp(v * (len(chars) - 1), 0, len(chars) - 1))] for v in reducidos)


# ══════════════════════════════════════════════════════════════════════
#  NOTIFICACIÓN VISUAL — Popup elegante
# ══════════════════════════════════════════════════════════════════════
class PopupNotificacion:
    """Notificación emergente con fade-in y auto-dismiss."""
    _ventanas_activas = []

    @classmethod
    def mostrar(cls, parent, titulo: str, mensaje: str, color: str = P.ACCENT_SUCCESS,
                duracion_ms: int = 4000, icono: str = "✓"):
        # Limitar a 3 notificaciones simultáneas
        while len(cls._ventanas_activas) >= 3:
            try:
                cls._ventanas_activas[0].destroy()
            except Exception:
                pass
            cls._ventanas_activas.pop(0)

        win = tk.Toplevel(parent)
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        win.attributes('-alpha', 0.0)
        win.configure(bg=P.BG_DEEP)

        # Posición: esquina inferior derecha
        win.update_idletasks()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        w, h = 380, 140
        x = sw - w - 20
        y = sh - h - 20 - (len(cls._ventanas_activas) * (h + 10))
        win.geometry(f"{w}x{h}+{x}+{y}")

        # Contenedor con borde de color
        outer = tk.Frame(win, bg=color, padx=2, pady=2)
        outer.pack(fill='both', expand=True)
        inner = tk.Frame(outer, bg=P.BG_CARD)
        inner.pack(fill='both', expand=True)

        # Barra superior
        top = tk.Frame(inner, bg=P.BG_ELEVATED, height=36)
        top.pack(fill='x')
        top.pack_propagate(False)
        tk.Label(top, text=f"  {icono}  {titulo}", bg=P.BG_ELEVATED, fg=color,
                 font=('Segoe UI', 10, 'bold'), anchor='w').pack(side='left', fill='x', expand=True, padx=8)

        # Cuerpo
        body = tk.Frame(inner, bg=P.BG_CARD)
        body.pack(fill='both', expand=True, padx=14, pady=10)
        for linea in mensaje.split('\n'):
            tk.Label(body, text=linea, bg=P.BG_CARD, fg=P.TEXT_PRIMARY,
                     font=('Segoe UI', 9), anchor='w').pack(anchor='w')

        cls._ventanas_activas.append(win)

        # Fade in
        def fade_in(alpha=0.0):
            if alpha < 0.95:
                try:
                    win.attributes('-alpha', alpha + 0.15)
                    win.after(25, lambda: fade_in(alpha + 0.15))
                except Exception:
                    pass
        fade_in()

        # Auto cerrar
        def auto_cerrar():
            try:
                if win in cls._ventanas_activas:
                    cls._ventanas_activas.remove(win)
                win.destroy()
            except Exception:
                pass
        if duracion_ms > 0:
            win.after(duracion_ms, auto_cerrar)

        # Cerrar al clic
        win.bind('<Button-1>', lambda e: auto_cerrar())


# ══════════════════════════════════════════════════════════════════════
#  DIALOGOS MODERNOS
# ══════════════════════════════════════════════════════════════════════
class ModernDialog(tk.Toplevel):
    """Base para diálogos modernos."""
    def __init__(self, parent, titulo: str, ancho: int = 460, alto: int = 380):
        super().__init__(parent)
        self.title("")
        self.geometry(f"{ancho}x{alto}")
        self.configure(bg=P.BG_PRIMARY)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        # Centrar en padre
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - ancho) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - alto) // 2
        self.geometry(f"+{px}+{py}")

        # Header
        hdr = tk.Frame(self, bg=P.BG_ELEVATED, height=50)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        tk.Label(hdr, text=titulo, bg=P.BG_ELEVATED, fg=P.ACCENT_PRIMARY,
                 font=('Segoe UI', 13, 'bold')).pack(side='left', padx=16)
        tk.Button(hdr, text="✕", bg=P.BG_ELEVATED, fg=P.TEXT_DIM,
                  relief=tk.FLAT, font=('Segoe UI', 10), cursor='hand2',
                  command=self.destroy).pack(side='right', padx=8)

        # Cuerpo
        self.body = tk.Frame(self, bg=P.BG_PRIMARY)
        self.body.pack(fill='both', expand=True, padx=20, pady=16)

        # Footer
        self.footer = tk.Frame(self, bg=P.BG_PRIMARY, height=50)
        self.footer.pack(fill='x', side='bottom', padx=20, pady=(0, 16))


class DialogoCopia(ModernDialog):
    """Diálogo para iniciar una copia interna."""
    def __init__(self, parent, nombre_memoria: str, unidad: str, gb_libre: float,
                 config: ConfigManager):
        super().__init__(parent, "⚡ Protocolo de Transferencia", 480, 420)
        self.resultado = None
        self.config = config

        # Info de la memoria
        info = GlassCard(self.body)
        info.pack(fill='x', pady=(0, 12))
        tk.Label(info, text=f"💾  {nombre_memoria}", bg=P.BG_CARD, fg=P.TEXT_PRIMARY,
                 font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        tk.Label(info, text=f"Unidad {unidad}  ·  {gb_libre:.2f} GB disponibles",
                 bg=P.BG_CARD, fg=P.ACCENT_SECONDARY, font=('Segoe UI', 9)).pack(anchor='w')

        # GB a copiar
        tk.Label(self.body, text="Cantidad a transferir (GB):", bg=P.BG_PRIMARY,
                 fg=P.TEXT_SECONDARY, font=('Segoe UI', 9)).pack(anchor='w', pady=(8, 4))
        self.gb_var = tk.StringVar(value=f"{min(gb_libre, 4):.2f}")
        entry_frame = tk.Frame(self.body, bg=P.BG_INPUT, highlightbackground=P.BORDER,
                               highlightthickness=1)
        entry_frame.pack(fill='x', ipady=8)
        self.entry = tk.Entry(entry_frame, textvariable=self.gb_var, bg=P.BG_INPUT,
                              fg=P.ACCENT_SUCCESS, font=('Consolas', 16, 'bold'),
                              insertbackground=P.ACCENT_SUCCESS, relief=tk.FLAT,
                              bd=0, justify='center')
        self.entry.pack(fill='x', padx=12)
        self.entry.select_range(0, 'end')
        self.entry.focus()

        # Slider rápido
        self.slider = tk.Scale(self.body, from_=0.1, to=gb_libre, resolution=0.01,
                               orient='horizontal', bg=P.BG_PRIMARY, fg=P.TEXT_DIM,
                               troughcolor=P.BG_CARD, highlightbackground=P.BG_PRIMARY,
                               activebackground=P.ACCENT_PRIMARY, sliderrelief=tk.FLAT,
                               showvalue=False, command=self._on_slider)
        self.slider.set(min(gb_libre, 4))
        self.slider.pack(fill='x', pady=8)

        # Botones rápidos
        btns = tk.Frame(self.body, bg=P.BG_PRIMARY)
        btns.pack(fill='x', pady=4)
        for val in [1, 2, 4, 8, 16]:
            if val <= gb_libre:
                GhostButton(btns, f"{val} GB",
                           command=lambda v=val: self._set_gb(v)).pack(side='left', padx=2)

        # Precio estimado
        precio = calcular_precio(min(gb_libre, 4))
        self.lbl_precio = tk.Label(self.body, text=formato_moneda(precio, config.moneda),
                                   bg=P.BG_PRIMARY, fg=P.ACCENT_SUCCESS,
                                   font=('Consolas', 20, 'bold'))
        self.lbl_precio.pack(pady=8)

        # Tabla de tramos
        tramos_frame = GlassCard(self.body)
        tramos_frame.pack(fill='both', expand=True)
        tk.Label(tramos_frame, text="Tramos de precio:", bg=P.BG_CARD, fg=P.TEXT_DIM,
                 font=('Segoe UI', 8)).pack(anchor='w')
        tramos_text = "  ".join(f"{gmin}-{gmax}GB: ${p}" for gmin, gmax, p in PRECIO_TRAMOS[:6])
        tk.Label(tramos_frame, text=tramos_text, bg=P.BG_CARD, fg=P.TEXT_SECONDARY,
                 font=('Consolas', 7), wraplength=400, justify='left').pack(anchor='w', pady=4)

        # Footer
        NeonButton(self.footer, "🚀 EJECUTAR TRANSFERENCIA", self._confirmar,
                   color=P.ACCENT_SUCCESS, size='large').pack(side='right')
        GhostButton(self.footer, "Cancelar", self.destroy).pack(side='right', padx=8)

        # Binds
        self.gb_var.trace('w', self._on_gb_change)
        self.entry.bind('<Return>', lambda e: self._confirmar())
        self._on_gb_change()

    def _set_gb(self, val):
        self.gb_var.set(f"{val:.2f}")
        self.slider.set(val)

    def _on_slider(self, val):
        self.gb_var.set(f"{float(val):.2f}")

    def _on_gb_change(self, *args):
        try:
            gb = float(self.gb_var.get())
            if gb > 0:
                precio = calcular_precio(gb)
                self.lbl_precio.config(text=formato_moneda(precio, self.config.moneda))
        except ValueError:
            pass

    def _confirmar(self):
        try:
            gb = float(self.gb_var.get())
            if gb <= 0:
                messagebox.showerror("Error", "La cantidad debe ser mayor a 0.", parent=self)
                return
            self.resultado = {
                'gb': round(gb, 2),
                'precio': calcular_precio(gb)
            }
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Ingresa un número válido.", parent=self)


class DialogoPrecio(ModernDialog):
    """Diálogo para configurar precio y tramos."""
    def __init__(self, parent, config: ConfigManager):
        super().__init__(parent, "💰 Configuración de Precios", 500, 450)
        self.config = config

        tk.Label(self.body, text="Precio base por GB (para cálculos manuales):",
                 bg=P.BG_PRIMARY, fg=P.TEXT_SECONDARY, font=('Segoe UI', 9)).pack(anchor='w')
        self.precio_var = tk.StringVar(value=str(config.precio_base))
        pf = tk.Frame(self.body, bg=P.BG_INPUT, highlightbackground=P.BORDER, highlightthickness=1)
        pf.pack(fill='x', ipady=6, pady=4)
        tk.Entry(pf, textvariable=self.precio_var, bg=P.BG_INPUT, fg=P.ACCENT_WARNING,
                 font=('Consolas', 14), insertbackground=P.ACCENT_WARNING, relief=tk.FLAT,
                 bd=0).pack(fill='x', padx=12)

        tk.Label(self.body, text="Moneda:", bg=P.BG_PRIMARY, fg=P.TEXT_SECONDARY,
                 font=('Segoe UI', 9)).pack(anchor='w', pady=(12, 4))
        self.moneda_var = tk.StringVar(value=config.moneda)
        mf = tk.Frame(self.body, bg=P.BG_INPUT, highlightbackground=P.BORDER, highlightthickness=1)
        mf.pack(fill='x', ipady=6)
        tk.Entry(mf, textvariable=self.moneda_var, bg=P.BG_INPUT, fg=P.TEXT_PRIMARY,
                 font=('Consolas', 12), insertbackground=P.TEXT_PRIMARY, relief=tk.FLAT,
                 bd=0).pack(fill='x', padx=12)

        # Vista previa de tramos
        tk.Label(self.body, text="Tramos activos (solo lectura en esta versión):",
                 bg=P.BG_PRIMARY, fg=P.TEXT_DIM, font=('Segoe UI', 8)).pack(anchor='w', pady=(16, 4))
        tc = tk.Frame(self.body, bg=P.BG_CARD, highlightbackground=P.BORDER, highlightthickness=1)
        tc.pack(fill='both', expand=True)
        for gmin, gmax, precio in PRECIO_TRAMOS:
            row = tk.Frame(tc, bg=P.BG_CARD)
            row.pack(fill='x', padx=8, pady=1)
            tk.Label(row, text=f"{gmin:>4} - {gmax:<4} GB", bg=P.BG_CARD, fg=P.TEXT_SECONDARY,
                     font=('Consolas', 9), width=14, anchor='w').pack(side='left')
            tk.Label(row, text=f"→  ${precio:>7.2f}", bg=P.BG_CARD, fg=P.ACCENT_WARNING,
                     font=('Consolas', 9, 'bold'), anchor='e').pack(side='right', padx=8)

        # Footer
        NeonButton(self.footer, "Guardar", self._guardar, color=P.ACCENT_SUCCESS).pack(side='right')
        GhostButton(self.footer, "Cancelar", self.destroy).pack(side='right', padx=8)

    def _guardar(self):
        try:
            precio = float(self.precio_var.get())
            if precio <= 0:
                raise ValueError
            self.config.set("precio_por_gb", precio)
            self.config.set("moneda", self.moneda_var.get().strip() or "CUP")
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Precio inválido.", parent=self)


class DialogoNombre(ModernDialog):
    """Diálogo para nombrar una memoria nueva."""
    def __init__(self, parent, unidad: str):
        super().__init__(parent, "💾 Nueva Memoria Detectada", 400, 220)
        self.resultado = None

        tk.Label(self.body, text=f"Se detectó una memoria nueva en {unidad}",
                 bg=P.BG_PRIMARY, fg=P.TEXT_SECONDARY, font=('Segoe UI', 10)).pack(anchor='w', pady=(8, 12))
        tk.Label(self.body, text="Asignar nombre:", bg=P.BG_PRIMARY, fg=P.TEXT_DIM,
                 font=('Segoe UI', 9)).pack(anchor='w')

        self.nombre_var = tk.StringVar(value=f"USB_{unidad.replace(':', '').upper()}")
        nf = tk.Frame(self.body, bg=P.BG_INPUT, highlightbackground=P.BORDER, highlightthickness=1)
        nf.pack(fill='x', ipady=8, pady=8)
        entry = tk.Entry(nf, textvariable=self.nombre_var, bg=P.BG_INPUT, fg=P.ACCENT_PRIMARY,
                         font=('Segoe UI', 13), insertbackground=P.ACCENT_PRIMARY, relief=tk.FLAT, bd=0)
        entry.pack(fill='x', padx=12)
        entry.select_range(0, 'end')
        entry.focus()
        entry.bind('<Return>', lambda e: self._aceptar())

        NeonButton(self.footer, "Confirmar", self._aceptar, color=P.ACCENT_PRIMARY).pack(side='right')
        GhostButton(self.footer, "Cancelar", self.destroy).pack(side='right', padx=8)

    def _aceptar(self):
        nombre = self.nombre_var.get().strip()
        if nombre:
            self.resultado = nombre
            self.destroy()


class DialogoAcerca(ModernDialog):
    """Diálogo de información."""
    def __init__(self, parent):
        super().__init__(parent, "Acerca de", 420, 340)
        tk.Label(self.body, text="Kalm-USB-Kopy", bg=P.BG_PRIMARY, fg=P.ACCENT_PRIMARY,
                 font=('Segoe UI', 20, 'bold')).pack(pady=(8, 0))
        tk.Label(self.body, text=f"Versión {APP_VERSION} · Nexus Pro", bg=P.BG_PRIMARY,
                 fg=P.TEXT_SECONDARY, font=('Segoe UI', 10)).pack(pady=(0, 16))

        info = GlassCard(self.body)
        info.pack(fill='x')
        lines = [
            ("Creador", CREATOR),
            ("Email", EMAIL),
            ("Motor", "Python + Tkinter + ttkbootstrap"),
            ("Radar", "Detección pasiva de copias externas"),
            ("Backup", "Respaldo automático con rotación"),
        ]
        for label, value in lines:
            row = tk.Frame(info, bg=P.BG_CARD)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=f"{label}:", bg=P.BG_CARD, fg=P.TEXT_DIM,
                     font=('Segoe UI', 9), width=12, anchor='w').pack(side='left')
            tk.Label(row, text=value, bg=P.BG_CARD, fg=P.TEXT_PRIMARY,
                     font=('Segoe UI', 9), anchor='w').pack(side='left', fill='x', expand=True)


# ══════════════════════════════════════════════════════════════════════
#  APLICACIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════════════
class KalmNexus:
    """Aplicación principal — Kalm-USB-Kopy Nexus Pro."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1300x880")
        self.root.minsize(1100, 750)
        self.root.configure(bg=P.BG_DEEP)

        # ── Gestores ──
        self.config = ConfigManager()
        self.history = HistoryManager(self.config.get("max_historial", 10000))
        self.memory = MemoryManager()
        self.backup = BackupManager()

        # ── Estado ──
        self.unidad_sel: Optional[str] = None
        self.mem_id_sel: Optional[str] = None
        self.mem_data_sel: Optional[dict] = None
        self._popup_abierto = False

        # ── Aplicar tema ──
        self._apply_theme()

        # ── Construir UI ──
        self._build_header()
        self._build_body()
        self._build_terminal()
        self._build_statusbar()

        # ── Radar ──
        self.radar = CopyRadar(self._on_copia_externa, self.config)
        self.radar.start()

        # ── Bandeja ──
        self.tray = TrayManager(self.root, self._show_window, self._exit_app)
        if self.config.get("minimizar_bandeja") and PYSTRAY:
            self.tray.start()

        # ── Inicio automático ──
        if self.config.get("iniciar_con_windows"):
            self._set_autostart(True)

        # ── Backup automático ──
        if self.config.get("auto_backup"):
            self._schedule_backup()

        # ── Monitoreo de USBs con refresh periódico ──
        self._refresh_usb_loop()

        # ── Cargar estado inicial ──
        self._load_initial_state()

        # ── Protocolo de cierre ──
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

        # ── Atajos de teclado ──
        self.root.bind('<F5>', lambda e: self._refresh_usb())
        self.root.bind('<F6>', lambda e: self._abrir_copia())
        self.root.bind('<Control-e>', lambda e: self._exportar_csv())
        self.root.bind('<Control-b>', lambda e: self._crear_backup_manual())
        self.root.bind('<Escape>', lambda e: self.root.focus_set())

        self._log("Sistema Nexus Pro iniciado correctamente.", "success")
        self._log("Radar de copias externas activo. Escaneando...", "info")
        self._log(f"Atajos: F5=Refresh · F6=Copiar · Ctrl+E=Exportar · Ctrl+B=Backup", "dim")

    # ── Tema ─────────────────────────────────────────────────────────
    def _apply_theme(self):
        if BOOTSTRAP:
            try:
                self.style = tb.Style(theme=self.config.get("tema", "cyborg"))
                self.style.configure('.', background=P.BG_DEEP, foreground=P.TEXT_PRIMARY)
            except Exception:
                self.style = tb.Style() if BOOTSTRAP else None

    # ── Header ───────────────────────────────────────────────────────
    def _build_header(self):
        self.header = tk.Frame(self.root, bg=P.BG_PRIMARY, height=64)
        self.header.pack(fill='x', side='top')
        self.header.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(self.header, bg=P.BG_PRIMARY)
        logo_frame.pack(side='left', padx=16)
        tk.Label(logo_frame, text="KALM", bg=P.BG_PRIMARY, fg=P.ACCENT_PRIMARY,
                 font=('Segoe UI', 22, 'bold')).pack(side='left')
        tk.Label(logo_frame, text="NEXUS", bg=P.BG_PRIMARY, fg=P.ACCENT_SECONDARY,
                 font=('Segoe UI', 22, 'bold')).pack(side='left', padx=(0, 8))
        tk.Label(logo_frame, text="v6.0", bg=P.BG_PRIMARY, fg=P.TEXT_DIM,
                 font=('Consolas', 9)).pack(side='left', padx=(0, 16))

        # Indicador radar
        self.radar_indicator = tk.Label(self.header, text="● RADAR ACTIVO", bg=P.BG_PRIMARY,
                                        fg=P.ACCENT_SUCCESS, font=('Consolas', 9, 'bold'))
        self.radar_indicator.pack(side='left', padx=12)

        # Botones header
        btn_frame = tk.Frame(self.header, bg=P.BG_PRIMARY)
        btn_frame.pack(side='right', padx=12)
        for text, cmd in [
            ("💰 Precios", self._abrir_config_precio),
            ("📦 Backup", self._crear_backup_manual),
            ("📄 Exportar", self._exportar_csv),
            ("ℹ️ Acerca", lambda: DialogoAcerca(self.root))
        ]:
            GhostButton(btn_frame, text, cmd).pack(side='left', padx=2)

    # ── Body (Tabs) ──────────────────────────────────────────────────
    def _build_body(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=8, pady=(4, 0))

        if BOOTSTRAP:
            self.style.configure('TNotebook', background=P.BG_DEEP, borderwidth=0)
            self.style.configure('TNotebook.Tab', background=P.BG_CARD, foreground=P.TEXT_SECONDARY,
                                padding=[18, 10], font=('Segoe UI', 10, 'bold'))
            self.style.map('TNotebook.Tab',
                          background=[('selected', P.ACCENT_PRIMARY)],
                          foreground=[('selected', P.TEXT_ON_ACCENT)])

        self._build_tab_nexus()
        self._build_tab_memorias()
        self._build_tab_historial()
        self._build_tab_estadisticas()

    # ── Tab: Nexus Principal ─────────────────────────────────────────
    def _build_tab_nexus(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  ⚡ Nexus  ")

        # Panel izquierdo: Unidades USB
        left = tk.Frame(tab, bg=P.BG_DEEP)
        left.pack(side='left', fill='both', expand=True, padx=(8, 4), pady=8)

        tk.Label(left, text="DISPOSITIVOS CONECTADOS", bg=P.BG_DEEP, fg=P.TEXT_DIM,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', pady=(0, 6))

        self.tree_usb = ModernTreeview(left, ('Unidad', 'Nombre', 'Total', 'Usado', 'Libre'))
        self.tree_usb.heading('Unidad', text='Unidad')
        self.tree_usb.heading('Nombre', text='Identidad')
        self.tree_usb.heading('Total', text='Total GB')
        self.tree_usb.heading('Usado', text='Usado GB')
        self.tree_usb.heading('Libre', text='Libre GB')
        self.tree_usb.column('Unidad', width=60, minwidth=60)
        self.tree_usb.column('Nombre', width=160, minwidth=100)
        self.tree_usb.column('Total', width=80, minwidth=60)
        self.tree_usb.column('Usado', width=80, minwidth=60)
        self.tree_usb.column('Libre', width=80, minwidth=60)
        self.tree_usb.pack(fill='both', expand=True)
        self.tree_usb.bind('<<TreeviewSelect>>', self._on_usb_select)
        self.tree_usb.bind('<Double-1>', lambda e: self._abrir_copia())

        # Barra de acciones
        actions = tk.Frame(left, bg=P.BG_DEEP)
        actions.pack(fill='x', pady=(8, 0))
        NeonButton(actions, "🔄 Sincronizar", self._refresh_usb, size='small').pack(side='left')
        NeonButton(actions, "🚀 Iniciar Copia", self._abrir_copia,
                   color=P.ACCENT_SUCCESS).pack(side='right')

        # Panel derecho: Stats + Info
        right = tk.Frame(tab, bg=P.BG_DEEP, width=380)
        right.pack(side='right', fill='y', padx=(4, 8), pady=8)
        right.pack_propagate(False)

        tk.Label(right, text="RESUMEN DEL DÍA", bg=P.BG_DEEP, fg=P.TEXT_DIM,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', pady=(0, 6))

        stats = tk.Frame(right, bg=P.BG_DEEP)
        stats.pack(fill='x')
        self.card_copias = StatCard(stats, "Copias Totales", "0", P.ACCENT_SECONDARY)
        self.card_copias.pack(fill='x', pady=2)
        self.card_gb = StatCard(stats, "GB Procesados", "0.00", P.ACCENT_SUCCESS)
        self.card_gb.pack(fill='x', pady=2)
        self.card_ingresos = StatCard(stats, "Ingresos", "$0.00", P.ACCENT_PRIMARY)
        self.card_ingresos.pack(fill='x', pady=2)

        # Info de memoria seleccionada
        tk.Label(right, text="SELECCIÓN ACTIVA", bg=P.BG_DEEP, fg=P.TEXT_DIM,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', pady=(16, 6))
        self.info_card = GlassCard(right)
        self.info_card.pack(fill='x')
        self.lbl_sel_nombre = tk.Label(self.info_card, text="Ninguna memoria seleccionada",
                                       bg=P.BG_CARD, fg=P.TEXT_PRIMARY, font=('Segoe UI', 11, 'bold'))
        self.lbl_sel_nombre.pack(anchor='w')
        self.lbl_sel_detalle = tk.Label(self.info_card, text="Conecta y selecciona una USB",
                                        bg=P.BG_CARD, fg=P.TEXT_DIM, font=('Segoe UI', 9))
        self.lbl_sel_detalle.pack(anchor='w', pady=(4, 0))
        self.lbl_sel_precio = tk.Label(self.info_card, text="",
                                       bg=P.BG_CARD, fg=P.ACCENT_SUCCESS, font=('Consolas', 16, 'bold'))
        self.lbl_sel_precio.pack(anchor='w', pady=(8, 0))

    # ── Tab: Base de Memorias ────────────────────────────────────────
    def _build_tab_memorias(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  💾 Memorias  ")

        toolbar = tk.Frame(tab, bg=P.BG_DEEP)
        toolbar.pack(fill='x', padx=8, pady=(8, 4))

        self.mem_search_var = tk.StringVar()
        self.mem_search_var.trace('w', lambda *a: self._filtrar_memorias())
        search_f = tk.Frame(toolbar, bg=P.BG_INPUT, highlightbackground=P.BORDER, highlightthickness=1)
        search_f.pack(side='left', ipady=4)
        tk.Entry(search_f, textvariable=self.mem_search_var, bg=P.BG_INPUT, fg=P.TEXT_PRIMARY,
                 font=('Segoe UI', 9), insertbackground=P.TEXT_PRIMARY, relief=tk.FLAT, bd=0,
                 width=30).pack(side='left', padx=8)
        tk.Label(search_f, text="🔍", bg=P.BG_INPUT, fg=P.TEXT_DIM).pack(side='right', padx=8)

        GhostButton(toolbar, "🗑️ Eliminar Seleccionada", self._eliminar_memoria).pack(side='right', padx=4)
        GhostButton(toolbar, "✏️ Renombrar", self._renombrar_memoria).pack(side='right', padx=4)

        self.tree_mem = ModernTreeview(tab, ('Nombre', 'Veces', 'Total GB', 'Ingresos', 'Última'))
        self.tree_mem.heading('Nombre', text='Identidad')
        self.tree_mem.heading('Veces', text='Conexiones')
        self.tree_mem.heading('Total GB', text='GB Copiados')
        self.tree_mem.heading('Ingresos', text='Ingresos')
        self.tree_mem.heading('Última', text='Última Conexión')
        self.tree_mem.column('Nombre', width=180, minwidth=120)
        self.tree_mem.column('Veces', width=90, minwidth=60)
        self.tree_mem.column('Total GB', width=100, minwidth=70)
        self.tree_mem.column('Ingresos', width=100, minwidth=70)
        self.tree_mem.column('Última', width=150, minwidth=100)
        self.tree_mem.pack(fill='both', expand=True, padx=8, pady=(0, 8))

    # ── Tab: Historial ───────────────────────────────────────────────
    def _build_tab_historial(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  📜 Historial  ")

        toolbar = tk.Frame(tab, bg=P.BG_DEEP)
        toolbar.pack(fill='x', padx=8, pady=(8, 4))

        self.hist_search_var = tk.StringVar()
        self.hist_search_var.trace('w', lambda *a: self._filtrar_historial())
        sf = tk.Frame(toolbar, bg=P.BG_INPUT, highlightbackground=P.BORDER, highlightthickness=1)
        sf.pack(side='left', ipady=4)
        tk.Entry(sf, textvariable=self.hist_search_var, bg=P.BG_INPUT, fg=P.TEXT_PRIMARY,
                 font=('Segoe UI', 9), insertbackground=P.TEXT_PRIMARY, relief=tk.FLAT, bd=0,
                 width=30).pack(side='left', padx=8)

        # Filtro de estado
        self.hist_estado_var = tk.StringVar(value="Todos")
        estados = ["Todos", "Interno Completado", "Externo Completado"]
        estado_menu = ttk.Combobox(toolbar, textvariable=self.hist_estado_var, values=estados,
                                   state='readonly', width=20)
        estado_menu.pack(side='left', padx=8)
        estado_menu.bind('<<ComboboxSelected>>', lambda e: self._filtrar_historial())

        GhostButton(toolbar, "📄 Exportar CSV", self._exportar_csv).pack(side='right', padx=4)
        GhostButton(toolbar, "🧹 Limpiar antiguos (90d)", self._limpiar_historial).pack(side='right', padx=4)

        self.tree_hist = ModernTreeview(tab, ('Fecha', 'Memoria', 'Unidad', 'GB', 'Precio', 'Estado'))
        self.tree_hist.heading('Fecha', text='Fecha/Hora')
        self.tree_hist.heading('Memoria', text='Memoria')
        self.tree_hist.heading('Unidad', text='Unidad')
        self.tree_hist.heading('GB', text='GB')
        self.tree_hist.heading('Precio', text='Precio')
        self.tree_hist.heading('Estado', text='Estado')
        self.tree_hist.column('Fecha', width=140, minwidth=100)
        self.tree_hist.column('Memoria', width=160, minwidth=100)
        self.tree_hist.column('Unidad', width=60, minwidth=50)
        self.tree_hist.column('GB', width=70, minwidth=50)
        self.tree_hist.column('Precio', width=80, minwidth=60)
        self.tree_hist.column('Estado', width=140, minwidth=100)
        self.tree_hist.pack(fill='both', expand=True, padx=8, pady=(0, 8))

    # ── Tab: Estadísticas ────────────────────────────────────────────
    def _build_tab_estadisticas(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  📊 Estadísticas  ")

        container = tk.Frame(tab, bg=P.BG_DEEP)
        container.pack(fill='both', expand=True, padx=8, pady=8)

        # Top memorias por ingresos
        left_col = tk.Frame(container, bg=P.BG_DEEP)
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 4))

        tk.Label(left_col, text="TOP MEMORIAS POR INGRESOS", bg=P.BG_DEEP, fg=P.TEXT_DIM,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', pady=(0, 6))
        self.txt_top_mem = tk.Text(left_col, bg=P.BG_CARD, fg=P.ACCENT_WARNING,
                                   font=('Consolas', 10), relief=tk.FLAT, bd=0,
                                   highlightbackground=P.BORDER, highlightthickness=1,
                                   height=18, state='disabled', wrap='none')
        self.txt_top_mem.pack(fill='both', expand=True)

        # Resumen temporal
        right_col = tk.Frame(container, bg=P.BG_DEEP, width=350)
        right_col.pack(side='right', fill='y', padx=(4, 0))
        right_col.pack_propagate(False)

        tk.Label(right_col, text="RESUMEN TEMPORAL", bg=P.BG_DEEP, fg=P.TEXT_DIM,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', pady=(0, 6))

        self.stats_cards = []
        for titulo, color in [("Hoy", P.ACCENT_SECONDARY), ("Esta Semana", P.ACCENT_PRIMARY),
                               ("Total Histórico", P.ACCENT_WARNING)]:
            c = StatCard(right_col, titulo, "-", color)
            c.pack(fill='x', pady=2)
            self.stats_cards.append(c)

        # Sparkline semanal
        tk.Label(right_col, text="ACTIVIDAD SEMANAL", bg=P.BG_DEEP, fg=P.TEXT_DIM,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', pady=(16, 6))
        self.txt_sparkline = tk.Text(right_col, bg=P.BG_CARD, fg=P.ACCENT_SUCCESS,
                                     font=('Consolas', 10), relief=tk.FLAT, bd=0,
                                     highlightbackground=P.BORDER, highlightthickness=1,
                                     height=5, state='disabled', wrap='none')
        self.txt_sparkline.pack(fill='x')

        # Backups
        tk.Label(right_col, text="BACKUPS DISPONIBLES", bg=P.BG_DEEP, fg=P.TEXT_DIM,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', pady=(16, 6))
        self.txt_backups = tk.Text(right_col, bg=P.BG_CARD, fg=P.TEXT_SECONDARY,
                                   font=('Consolas', 9), relief=tk.FLAT, bd=0,
                                   highlightbackground=P.BORDER, highlightthickness=1,
                                   height=6, state='disabled', wrap='none')
        self.txt_backups.pack(fill='both', expand=True)

    # ── Terminal ─────────────────────────────────────────────────────
    def _build_terminal(self):
        frame = tk.Frame(self.root, bg=P.BG_TERMINAL, highlightbackground=P.BORDER,
                         highlightthickness=1)
        frame.pack(fill='x', side='bottom', padx=8, pady=(0, 4))

        header = tk.Frame(frame, bg=P.BG_ELEVATED, height=28)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text="  TERMINAL NEXUS", bg=P.BG_ELEVATED, fg=P.ACCENT_SUCCESS,
                 font=('Consolas', 8, 'bold'), anchor='w').pack(side='left', fill='x', expand=True)
        tk.Button(header, text="Limpiar", bg=P.BG_ELEVATED, fg=P.TEXT_DIM, relief=tk.FLAT,
                  font=('Consolas', 8), cursor='hand2',
                  command=lambda: self.terminal.config(state='normal', text=''),
                  bg=P.BG_ELEVATED).pack(side='right', padx=8)

        self.terminal = scrolledtext.ScrolledText(
            frame, bg=P.BG_TERMINAL, fg=P.ACCENT_SUCCESS, font=("Consolas", 9),
            insertbackground=P.ACCENT_SUCCESS, relief=tk.FLAT, bd=0, height=5,
            selectbackground=P.ACCENT_PRIMARY, selectforeground=P.TEXT_ON_ACCENT
        )
        self.terminal.pack(fill='x', padx=1, pady=(0, 1))
        self.terminal.config(state='disabled')

        # Tags de color
        self.terminal.tag_config("info", foreground=P.ACCENT_SECONDARY)
        self.terminal.tag_config("success", foreground=P.ACCENT_SUCCESS)
        self.terminal.tag_config("warning", foreground=P.ACCENT_WARNING)
        self.terminal.tag_config("error", foreground=P.ACCENT_DANGER)
        self.terminal.tag_config("magic", foreground=P.ACCENT_PRIMARY)
        self.terminal.tag_config("dim", foreground=P.TEXT_DIM)

    # ── Status Bar ───────────────────────────────────────────────────
    def _build_statusbar(self):
        self.statusbar = tk.Frame(self.root, bg=P.BG_ELEVATED, height=24)
        self.statusbar.pack(fill='x', side='bottom')
        self.statusbar.pack_propagate(False)
        self.lbl_status = tk.Label(self.statusbar, text="Listo", bg=P.BG_ELEVATED,
                                   fg=P.TEXT_DIM, font=('Segoe UI', 8), anchor='w')
        self.lbl_status.pack(side='left', padx=8)
        self.lbl_hora = tk.Label(self.statusbar, text="", bg=P.BG_ELEVATED,
                                 fg=P.TEXT_DIM, font=('Consolas', 8))
        self.lbl_hora.pack(side='right', padx=8)
        self._update_clock()

    def _update_clock(self):
        try:
            self.lbl_hora.config(text=datetime.datetime.now().strftime("%H:%M:%S"))
            self.root.after(1000, self._update_clock)
        except Exception:
            pass

    # ── Logging ──────────────────────────────────────────────────────
    def _log(self, msg: str, tag: str = "info"):
        try:
            self.terminal.config(state='normal')
            ts = timestamp_corto()
            self.terminal.insert('end', f"[{ts}] {msg}\n", tag)
            self.terminal.see('end')
            self.terminal.config(state='disabled')
        except Exception:
            pass

    def _set_status(self, msg: str):
        try:
            self.lbl_status.config(text=msg)
        except Exception:
            pass

    # ── USB Monitoring ───────────────────────────────────────────────
    def _get_usb_drives(self) -> List[dict]:
        drives = []
        for p in psutil.disk_partitions():
            if 'removable' in p.opts:
                try:
                    u = psutil.disk_usage(p.mountpoint)
                    drives.append({
                        'letra': p.mountpoint,
                        'total': bytes_a_gb(u.total),
                        'usado': bytes_a_gb(u.used),
                        'libre': bytes_a_gb(u.free)
                    })
                except Exception:
                    pass
        return drives

    def _refresh_usb(self):
        self.tree_usb.delete(*self.tree_usb.get_children())
        drives = self._get_usb_drives()

        if not drives:
            self.tree_usb.insert('', 'end', values=('—', 'Sin dispositivos', '—', '—', '—'))
            self._set_status("No hay memorias USB conectadas")
            return

        for d in drives:
            mid, mdata = self.memory.obtener_por_unidad(d['letra'])
            nombre = mdata.get('nombre', 'Nueva') if mdata else 'Nueva'
            self.tree_usb.insert('', 'end', values=(
                d['letra'], nombre, f"{d['total']:.2f}", f"{d['usado']:.2f}", f"{d['libre']:.2f}"
            ), tags=(d['letra'],))

        # Resetear radar baselines para las unidades actuales
        for d in drives:
            self.radar.reset_drive(d['letra'])

        self._set_status(f"{len(drives)} dispositivo(s) conectado(s)")
        self._log(f"Sincronización: {len(drives)} USB(s) detectada(s)", "info")

    def _refresh_usb_loop(self):
        """Refresca la lista de USBs cada 5 segundos."""
        try:
            self._refresh_usb()
            self.root.after(5000, self._refresh_usb_loop)
        except Exception:
            pass

    def _on_usb_select(self, event):
        sel = self.tree_usb.selection()
        if not sel:
            return
        vals = self.tree_usb.item(sel[0], 'values')
        if vals[0] in ('—', 'Sin dispositivos'):
            self.unidad_sel = None
            return

        self.unidad_sel = vals[0]
        mid, mdata = self.memory.obtener_por_unidad(vals[0])

        # Si es nueva, pedir nombre
        if mdata is None:
            dlg = DialogoNombre(self.root, vals[0])
            self.root.wait_window(dlg)
            nombre = dlg.resultado or f"USB_{vals[0].replace(':', '').upper()}"
            mid, mdata = self.memory.identificar(vals[0], nombre)

        self.mem_id_sel = mid
        self.mem_data_sel = mdata

        # Actualizar info panel
        self.lbl_sel_nombre.config(text=mdata.get('nombre', 'Sin nombre'))
        veces = mdata.get('veces_usada', 0)
        total_gb = mdata.get('total_gb', 0)
        self.lbl_sel_detalle.config(text=f"{vals[0]}  ·  {veces} conexiones  ·  {total_gb:.2f} GB históricos")

        try:
            libre = float(vals[4])
        except (ValueError, IndexError):
            libre = 0
        precio = calcular_precio(libre)
        self.lbl_sel_precio.config(text=formato_moneda(precio, self.config.moneda))
        self._set_status(f"Seleccionada: {mdata.get('nombre')} en {vals[0]}")

    # ── Copia Interna ────────────────────────────────────────────────
    def _abrir_copia(self):
        if not self.unidad_sel:
            PopupNotificacion(self.root, "Sin selección",
                              "Conecta y selecciona una memoria USB primero.",
                              P.ACCENT_WARNING, icono="⚠")
            return
        if self.mem_data_sel is None:
            return

        drives = self._get_usb_drives()
        gb_libre = 0
        for d in drives:
            if d['letra'] == self.unidad_sel:
                gb_libre = d['libre']
                break

        if gb_libre <= 0:
            PopupNotificacion(self.root, "Sin espacio",
                              "La memoria no tiene espacio disponible.",
                              P.ACCENT_DANGER, icono="✕")
            return

        dlg = DialogoCopia(self.root, self.mem_data_sel.get('nombre', 'USB'),
                          self.unidad_sel, gb_libre, self.config)
        self.root.wait_window(dlg)

        if dlg.resultado:
            self._ejecutar_copia_interna(dlg.resultado)

    def _ejecutar_copia_interna(self, datos: dict):
        gb = datos['gb']
        precio = datos['precio']
        nombre = self.mem_data_sel.get('nombre', 'USB')

        # Pausar radar para no detectar esta copia como externa
        self.radar.pause()

        registro = {
            'nombre_memoria': nombre,
            'unidad': self.unidad_sel,
            'gb_copiados': gb,
            'precio': precio,
            'hora': timestamp_corto(),
            'estado': 'Interno Completado'
        }
        self.history.agregar(registro)
        self.memory.registrar_copia(self.mem_id_sel, gb, precio)

        # Reactivar radar después de 5 segundos
        self.root.after(5000, self.radar.resume)

        # Notificar
        PopupNotificacion(self.root, "Copia Registrada",
                          f"💾 {nombre}\n📊 {gb} GB  ·  💰 {formato_moneda(precio, self.config.moneda)}",
                          P.ACCENT_SUCCESS, icono="✓")

        if PLYER and self.config.get("mostrar_notificaciones"):
            try:
                notification.notify(
                    title="Kalm-Nexus: Copia Registrada",
                    message=f"{nombre}: {gb}GB → {formato_moneda(precio, self.config.moneda)}",
                    timeout=5
                )
            except Exception:
                pass

        self._log(f"Copia interna: {nombre} → {gb}GB → {formato_moneda(precio, self.config.moneda)}", "success")

        # Actualizar todo
        self._update_all_views()

    # ── Copia Externa (callback del radar) ───────────────────────────
    def _on_copia_externa(self, unidad: str, gb: float, precio: float):
        try:
            mid, mdata = self.memory.identificar(unidad)
            nombre = mdata.get('nombre', 'Desconocida')

            registro = {
                'nombre_memoria': f"{nombre} (Externo)",
                'unidad': unidad,
                'gb_copiados': gb,
                'precio': precio,
                'hora': timestamp_corto(),
                'estado': 'Externo Completado'
            }
            self.history.agregar(registro)
            self.memory.registrar_copia(mid, gb, precio)

            self._log(f"👁️ RADAR: Copia externa en '{nombre}': {gb}GB → {formato_moneda(precio, self.config.moneda)}", "magic")

            PopupNotificacion(self.root, "Radar: Copia Externa",
                              f"💾 {nombre}\n📊 {gb} GB detectados\n💰 Cobrar: {formato_moneda(precio, self.config.moneda)}",
                              P.ACCENT_PRIMARY, icono="👁", duracion_ms=6000)

            if PLYER and self.config.get("mostrar_notificaciones"):
                try:
                    notification.notify(
                        title="Kalm-Nexus: Radar Externo",
                        message=f"Copia en {nombre}: {gb}GB → {formato_moneda(precio, self.config.moneda)}",
                        timeout=8
                    )
                except Exception:
                    pass

            self.root.after(0, self._update_all_views)
        except Exception as e:
            self._log(f"Error procesando copia externa: {e}", "error")

    # ── Actualización de vistas ──────────────────────────────────────
    def _update_all_views(self):
        self._update_stats_dia()
        self._update_historial_view()
        self._update_memorias_view()
        self._update_stats_tab()
        self._refresh_usb()

    def _update_stats_dia(self):
        resumen = self.history.resumen_dia()
        self.card_copias.set_valor(str(resumen['registros']),
                                   f"Internas: {resumen['internos']} · Externas: {resumen['externos']}")
        self.card_gb.set_valor(f"{resumen['total_gb']:.2f}")
        self.card_ingresos.set_valor(formato_moneda(resumen['total_precio'], self.config.moneda))
        # Pulse
        self.card_copias.pulse()
        self.card_gb.pulse()
        self.card_ingresos.pulse()

    def _update_historial_view(self):
        self.tree_hist.delete(*self.tree_hist.get_children())
        estado = self.hist_estado_var.get() if hasattr(self, 'hist_estado_var') else "Todos"
        busqueda = self.hist_search_var.get() if hasattr(self, 'hist_search_var') else ""
        regs = self.history.filtrar(estado=estado if estado != "Todos" else None,
                                    busqueda=busqueda if busqueda else None, limite=200)
        for r in regs:
            fecha = r.get('fecha', '')[:16].replace('T', ' ')
            self.tree_hist.insert('', 'end', values=(
                fecha,
                r.get('nombre_memoria', ''),
                r.get('unidad', ''),
                f"{r.get('gb_copiados', 0):.2f}",
                f"${r.get('precio', 0):.2f}",
                r.get('estado', '')
            ))

    def _filtrar_historial(self):
        self._update_historial_view()

    def _update_memorias_view(self):
        self.tree_mem.delete(*self.tree_mem.get_children())
        busqueda = self.mem_search_var.get().lower() if hasattr(self, 'mem_search_var') else ""
        for mid, m in self.memory.listar():
            if busqueda and busqueda not in m.get('nombre', '').lower():
                continue
            ultima = ""
            if m.get('ultima_conexion'):
                try:
                    ultima = datetime.datetime.fromisoformat(m['ultima_conexion']).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    ultima = m['ultima_conexion'][:16]
            self.tree_mem.insert('', 'end', values=(
                m.get('nombre', ''),
                m.get('veces_usada', 0),
                f"{m.get('total_gb', 0):.2f}",
                f"${m.get('total_ingresos', 0):.2f}",
                ultima
            ))

    def _filtrar_memorias(self):
        self._update_memorias_view()

    def _update_stats_tab(self):
        # Top memorias
        top = sorted(self.memory.data.items(),
                     key=lambda x: x[1].get('total_ingresos', 0), reverse=True)[:10]
        datos = [(m.get('nombre', '?')[:15], m.get('total_ingresos', 0)) for _, m in top]
        chart = AsciiChart.barras_horizontales(datos, ancho=25)
        self.txt_top_mem.config(state='normal')
        self.txt_top_mem.delete('1.0', 'end')
        self.txt_top_mem.insert('1.0', chart if datos else "  Sin datos aún")
        self.txt_top_mem.config(state='disabled')

        # Resúmenes temporales
        dia = self.history.resumen_dia()
        semana = self.history.resumen_semana()
        total_gb = sum(m.get('total_gb', 0) for m in self.memory.data.values())
        total_p = sum(m.get('total_ingresos', 0) for m in self.memory.data.values())

        self.stats_cards[0].set_valor(str(dia['registros']),
                                      f"{dia['total_gb']:.1f} GB · {formato_moneda(dia['total_precio'], self.config.moneda)}")
        self.stats_cards[1].set_valor(str(semana['registros']),
                                      f"{semana['total_gb']:.1f} GB · {formato_moneda(semana['total_precio'], self.config.moneda)}")
        self.stats_cards[2].set_valor(str(len(self.history.data)),
                                      f"{total_gb:.1f} GB · {formato_moneda(total_p, self.config.moneda)}")

        # Sparkline semanal
        hoy = datetime.datetime.now().date()
        valores = []
        for i in range(6, -1, -1):
            dia_str = (hoy - datetime.timedelta(days=i)).isoformat()
            r = self.history.resumen_dia(dia_str)
            valores.append(r['total_precio'])
        spark = AsciiChart.sparkline(valores, ancho=30)
        dias_labels = " ".join([(hoy - datetime.timedelta(days=i)).strftime("%a")[:2]
                                for i in range(6, -1, -1)])
        self.txt_sparkline.config(state='normal')
        self.txt_sparkline.delete('1.0', 'end')
        self.txt_sparkline.insert('1.0', f" {dias_labels}\n {spark}")
        self.txt_sparkline.config(state='disabled')

        # Backups
        backups = self.backup.listar_backups()
        self.txt_backups.config(state='normal')
        self.txt_backups.delete('1.0', 'end')
        if backups:
            for b in backups[:5]:
                self.txt_backups.insert('end', f" {b['fecha']}  {b['nombre']}\n")
        else:
            self.txt_backups.insert('1.0', "  Sin backups")
        self.txt_backups.config(state='disabled')

    # ── Acciones ─────────────────────────────────────────────────────
    def _abrir_config_precio(self):
        dlg = DialogoPrecio(self.root, self.config)
        self.root.wait_window(dlg)
        self._update_all_views()
        self._log("Configuración de precios actualizada.", "warning")

    def _exportar_csv(self):
        ruta = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile=f"kalm_historial_{fecha_iso()}.csv"
        )
        if ruta:
            self.history.exportar_csv(ruta)
            self._log(f"Historial exportado a: {ruta}", "success")
            PopupNotificacion(self.root, "Exportado", f"Guardado en:\n{ruta}",
                              P.ACCENT_SUCCESS, icono="📄")

    def _crear_backup_manual(self):
        ruta = self.backup.crear_backup()
        if ruta:
            self._log(f"Backup creado: {ruta}", "success")
            PopupNotificacion(self.root, "Backup Creado", f"Respaldo guardado correctamente.",
                              P.ACCENT_SUCCESS, icono="📦")
            self._update_stats_tab()
        else:
            self._log("Error al crear backup.", "error")

    def _limpiar_historial(self):
        if messagebox.askyesno("Limpiar Historial",
                               "¿Eliminar registros anteriores a 90 días?"):
            antes = len(self.history.data)
            self.history.limpiar_antiguos(90)
            eliminados = antes - len(self.history.data)
            self._log(f"Historial limpiado: {eliminados} registros eliminados.", "warning")
            self._update_all_views()

    def _renombrar_memoria(self):
        sel = self.tree_mem.selection()
        if not sel:
            return
        vals = self.tree_mem.item(sel[0], 'values')
        nombre_actual = vals[0]
        nuevo = tk.simpledialog.askstring("Renombrar", f"Nuevo nombre para '{nombre_actual}':",
                                          parent=self.root)
        if nuevo:
            # Encontrar el mid correspondiente
            for mid, m in self.memory.data.items():
                if m.get('nombre') == nombre_actual:
                    self.memory.renombrar(mid, nuevo)
                    self._log(f"Memoria renombrada: '{nombre_actual}' → '{nuevo}'", "info")
                    break
            self._update_all_views()

    def _eliminar_memoria(self):
        sel = self.tree_mem.selection()
        if not sel:
            return
        vals = self.tree_mem.item(sel[0], 'values')
        nombre = vals[0]
        if messagebox.askyesno("Eliminar", f"¿Eliminar '{nombre}' del registro?"):
            for mid, m in list(self.memory.data.items()):
                if m.get('nombre') == nombre:
                    self.memory.eliminar(mid)
                    self._log(f"Memoria eliminada: '{nombre}'", "warning")
                    break
            self._update_all_views()

    # ── Autostart ────────────────────────────────────────────────────
    def _set_autostart(self, activar: bool):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            if activar:
                ruta = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, "KalmUSBKopy", 0, winreg.REG_SZ, f'"{ruta}"')
            else:
                try:
                    winreg.DeleteValue(key, "KalmUSBKopy")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            self._log(f"Error configurando autostart: {e}", "error")

    # ── Backup automático ────────────────────────────────────────────
    def _schedule_backup(self):
        intervalo = self.config.get("backup_interval_horas", 6) * 3600 * 1000
        try:
            self.backup.crear_backup()
            self._log("Backup automático creado.", "dim")
        except Exception:
            pass
        try:
            self.root.after(intervalo, self._schedule_backup)
        except Exception:
            pass

    # ── Carga inicial ────────────────────────────────────────────────
    def _load_initial_state(self):
        self._refresh_usb()
        self._update_stats_dia()
        self._update_historial_view()
        self._update_memorias_view()
        self._update_stats_tab()

    # ── Ventana / Cierre ─────────────────────────────────────────────
    def _show_window(self):
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def _on_close(self):
        if self.config.get("minimizar_bandeja") and PYSTRAY:
            self.tray.hide()
            self._log("Interfaz minimizada a bandeja. Nexus operando en segundo plano.", "magic")
        else:
            self._exit_app()

    def _exit_app(self):
        try:
            self.radar.stop()
            self.tray.stop()
        except Exception:
            pass
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)


# ══════════════════════════════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════
def main():
    if BOOTSTRAP:
        root = tb.Window(themename="cyborg")
    else:
        root = tk.Tk()
    root.configure(bg=P.BG_DEEP)

    # Intentar aplicar icono
    try:
        icon_paths = ["kalm_icon.png",
                      os.path.join(os.path.dirname(sys.argv[0]), "kalm_icon.png"),
                      os.path.join(os.getcwd(), "kalm_icon.png")]
        for p in icon_paths:
            if os.path.exists(p):
                img = Image.open(p).resize((32, 32), Image.Resampling.LANCZOS)
                ico_path = os.path.join(tempfile.gettempdir(), "kalm_icon.ico")
                img.save(ico_path, format='ICO', sizes=[(32, 32)])
                root.iconbitmap(ico_path)
                break
    except Exception:
        pass

    app = KalmNexus(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.radar.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
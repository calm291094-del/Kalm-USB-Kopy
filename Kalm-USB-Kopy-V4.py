"""
Kalm-USB-Kopy - Nexus de Gestión USB Autónoma
Versión: 5.0.0 (CyberFantasy + External Radar Edition)
Estética: Dark Fantasy Anime + Hacker
Creador: Carlos A. Lorenzo Marro
"""
import os, sys, json, shutil, datetime, threading, time, subprocess, winreg, hashlib, tempfile
from pathlib import Path
from tkinter import *
from tkinter import ttk, messagebox, scrolledtext, filedialog
import psutil
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont

# Intentar importar librerías externas
try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    BOOTSTRAP_AVAILABLE = True
except ImportError:
    BOOTSTRAP_AVAILABLE = False
    print("⚠️ ttkbootstrap no instalado. pip install ttkbootstrap")

try:
    from plyer import notification
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False

try:
    import pystray
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

# ==================== CONFIGURACIÓN Y ESTÉTICA ====================
APP_NAME = "Kalm-USB-Kopy"
APP_VERSION = "5.0.0"
CREATOR = "Carlos A. Lorenzo Marro"

CONFIG_FILE = "config_kalm.json"
HISTORY_FILE = "historial_kalm.json"
MEMORY_DB = "memorias_kalm.db"

# PALETA CYBERFANTASY
VOID_BG = "#09090e"
PANEL_BG = "#13131c"
NEON_PURPLE = "#b026ff"
NEON_GREEN = "#00ff41"
NEON_CYAN = "#00f0ff"
NEON_RED = "#ff003c"
TEXT_MAIN = "#e0e0e0"
TEXT_DIM = "#7a7a8c"

DEFAULT_CONFIG = {
    "precio_por_gb": 5.0,
    "moneda": "CUP",
    "iniciar_con_windows": True,       # ACTIVADO POR DEFECTO
    "tema": "cyborg",
    "auto_detectar": True,
    "mostrar_notificaciones": True,    # ACTIVADO POR DEFECTO
    "minimizar_bandeja": True,         # ACTIVADO POR DEFECTO
    "max_historial": 10000,
    "notificaciones_duracion": 5
}

# ==================== LÓGICA DE PRECIOS INTELIGENTE ====================
def calcular_precio_inteligente(gb):
    """Calcula el precio basado en los tramos escalonados de fantasía"""
    tramos = {1: 5, 2: 10, 4: 25, 8: 50, 16: 100, 32: 200, 64: 400, 
              128: 800, 256: 1600, 512: 3200, 1024: 6400}
    if gb in tramos:
        return tramos[gb]
    if gb < 4:
        return gb * 5.0
    else:
        return gb * 6.25

# ==================== GESTORES DE DATOS ====================
class ConfigManager:
    def __init__(self):
        self.config = {}
        self.cargar_config()
    def cargar_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f: self.config = json.load(f)
            else:
                self.config = DEFAULT_CONFIG.copy()
                self.guardar_config()
        except: self.config = DEFAULT_CONFIG.copy()
    def guardar_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(self.config, f, indent=4, ensure_ascii=False)
        except: pass
    def obtener(self, clave, valor_por_defecto=None): return self.config.get(clave, valor_por_defecto)
    def establecer(self, clave, valor):
        self.config[clave] = valor
        self.guardar_config()
    def obtener_precio(self): return float(self.config.get("precio_por_gb", 5.0))

class HistoryManager:
    def __init__(self):
        self.historial = []
        self.cargar_historial()
    def cargar_historial(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f: self.historial = json.load(f)
        except: self.historial = []
    def guardar_historial(self):
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f: json.dump(self.historial, f, indent=4, ensure_ascii=False)
        except: pass
    def agregar_registro(self, registro):
        if 'fecha' not in registro: registro['fecha'] = datetime.datetime.now().isoformat()
        self.historial.append(registro)
        self.guardar_historial()

class MemoryManager:
    def __init__(self):
        self.memorias = {}
        self.cargar_memorias()
    def cargar_memorias(self):
        try:
            if os.path.exists(MEMORY_DB):
                with open(MEMORY_DB, 'r', encoding='utf-8') as f: self.memorias = json.load(f)
        except: self.memorias = {}
    def guardar_memorias(self):
        try:
            with open(MEMORY_DB, 'w', encoding='utf-8') as f: json.dump(self.memorias, f, indent=4, ensure_ascii=False)
        except: pass
    def identificar_memoria(self, unidad, nombre=None):
        try:
            import win32api
            drive = win32api.GetVolumeInformation(unidad)
            serial = str(drive[1])
        except: serial = hashlib.md5(unidad.encode()).hexdigest()[:8]
        for mem_id, data in self.memorias.items():
            if data.get('serial') == serial: return mem_id, data
        if nombre is None: nombre = f"Memoria_{len(self.memorias) + 1}"
        mem_id = f"MEM_{int(time.time())}_{serial[:4]}"
        self.memorias[mem_id] = {
            'id': mem_id, 'nombre': nombre, 'serial': serial, 'unidad': unidad,
            'fecha_registro': datetime.datetime.now().isoformat(), 'veces_usada': 0,
            'total_gb_copiados': 0, 'total_ingresos': 0, 'historico': []
        }
        self.guardar_memorias()
        return mem_id, self.memorias[mem_id]
    def registrar_copia(self, mem_id, gb, precio):
        if mem_id in self.memorias:
            self.memorias[mem_id]['historico'].append({'fecha': datetime.datetime.now().isoformat(), 'gb': gb, 'precio': precio})
            self.memorias[mem_id]['veces_usada'] += 1
            self.memorias[mem_id]['total_gb_copiados'] += gb
            self.memorias[mem_id]['total_ingresos'] += precio
            self.guardar_memorias()

# ==================== RADAR DE COPIAS EXTERNAS ====================
class ExternalCopyRadar:
    """Monitorea cambios en el espacio usado de las USBs para detectar copias de otros programas"""
    def __init__(self, app):
        self.app = app
        self.running = False
        self.hilo = None
        self.baselines = {}
        self.last_known = {}
        self.session_deltas = {}
        self.idle_timers = {}

    def iniciar(self):
        self.running = True
        self.hilo = threading.Thread(target=self._radar_loop, daemon=True)
        self.hilo.start()

    def detener(self):
        self.running = False

    def _radar_loop(self):
        while self.running:
            try:
                current_drives = self._get_removable_drives()
                
                # Limpiar unidades desconectadas
                for d in list(self.baselines.keys()):
                    if d not in current_drives:
                        self.baselines.pop(d, None)
                        self.last_known.pop(d, None)
                        self.session_deltas.pop(d, None)
                        self.idle_timers.pop(d, None)

                for d in current_drives:
                    try:
                        usage = psutil.disk_usage(d)
                        used_gb = usage.used / (1024**3)

                        if d not in self.baselines:
                            self.baselines[d] = used_gb
                            self.last_known[d] = used_gb
                            self.session_deltas[d] = 0.0
                            self.idle_timers[d] = 0
                            continue

                        delta = used_gb - self.last_known[d]
                        
                        # Ignorar cambios menores a 5MB (Antivirus/Indexación de Windows)
                        if delta > 0.005: 
                            self.session_deltas[d] += delta
                            self.idle_timers[d] = 0
                        else:
                            self.idle_timers[d] += 2  # Sumamos 2 seg (el tiempo del sleep)

                        self.last_known[d] = used_gb

                        # Si hubo copia y lleva 5 segundos sin cambiar, la copia terminó
                        if self.session_deltas[d] > 0.01 and self.idle_timers[d] >= 5:
                            if not self.app.internal_copy_active: # Evitar doble conteo
                                total_gb = round(self.session_deltas[d], 2)
                                precio = calcular_precio_inteligente(total_gb)
                                
                                # Identificar memoria
                                mem_id, data = self.app.memory.identificar_memoria(d)
                                nombre = data.get('nombre', 'Entidad Externa')
                                
                                # Registrar
                                registro = {
                                    'nombre_memoria': f"{nombre} (Externo)",
                                    'unidad': d, 'gb_copiados': total_gb, 'precio': precio,
                                    'hora': datetime.datetime.now().strftime("%H:%M:%S"), 
                                    'estado': 'Externo Completado'
                                }
                                self.app.history.agregar_registro(registro)
                                self.app.memory.registrar_copia(mem_id, total_gb, precio)
                                
                                # Notificar y Loguear
                                self.app.root.after(0, lambda g=total_gb, p=precio, n=nombre: self._notificar_copia_externa(n, g, p))
                                self.app.root.after(0, self.app.actualizar_stats_rapidas)
                                self.app.root.after(0, self.app.actualizar_crono)
                                self.app.root.after(0, self.app.actualizar_lista_memorias)
                            
                            # Resetear para la siguiente copia
                            self.session_deltas[d] = 0.0
                            self.idle_timers[d] = 0

                    except Exception:
                        pass
                time.sleep(2)
            except Exception:
                time.sleep(2)

    def _get_removable_drives(self):
        drives = []
        for p in psutil.disk_partitions():
            if 'removable' in p.opts: drives.append(p.mountpoint)
        return drives

    def _notificar_copia_externa(self, nombre, gb, precio):
        self.app.log_terminal(f"👁️ RADAR: Copia externa detectada en '{nombre}'. {gb}GB -> ${precio}", "magic")
        if NOTIFICATION_AVAILABLE and self.app.config.obtener("mostrar_notificaciones"):
            try:
                notification.notify(
                    title="⚔️ Kalm-Nexus: Radar Externo",
                    message=f"Se detectó una copia externa.\n\n💾 Memoria: {nombre}\n📊 GB Copiados: {gb}\n💰 Cobrar: ${precio} CUP",
                    timeout=8
                )
            except: pass

# ==================== GESTOR DE BANDEJA (CORREGIDO Y ROBUSTO) ====================
class SystemTrayManager:
    def __init__(self, app, root):
        self.app = app
        self.root = root
        self.tray_icon = None
        self.tray_thread = None
        self.tray_running = False
        self.icon_image = self._crear_icono_neon()

    def _crear_icono_neon(self):
        """Genera el icono en memoria para que no dependa de archivos externos"""
        try:
            img = Image.new('RGBA', (64, 64), (9, 9, 14, 255)) # Void BG
            draw = ImageDraw.Draw(img)
            try: font = ImageFont.truetype("arial.ttf", 42)
            except: font = ImageFont.load_default()
            
            # Dibujar K con sombra neón
            draw.text((14, 6), "K", fill=(176, 38, 255, 255), font=font) # Púrpura Neón
            return img
        except:
            return Image.new('RGBA', (64, 64), (176, 38, 255, 255))

    def iniciar_bandeja(self):
        if not PYSTRAY_AVAILABLE or self.tray_running: return False
        try:
            menu = pystray.Menu(
                pystray.MenuItem("🔄 Mostrar Nexus", self.mostrar_ventana, default=True),
                pystray.MenuItem("📊 Generar Informe", lambda: self.app.generar_informe()),
                pystray.MenuItem("❌ Salir", self.salir_aplicacion)
            )
            self.tray_icon = pystray.Icon("KalmNexus", self.icon_image, "Kalm-Nexus v5.0", menu)
            self.tray_running = True
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
            return True
        except Exception as e:
            print(f"Error bandeja: {e}")
            return False

    def mostrar_ventana(self, icon=None, item=None):
        self.root.after(0, self._do_show)

    def _do_show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def ocultar_ventana(self):
        self.root.withdraw()

    def salir_aplicacion(self, icon=None, item=None):
        self.tray_running = False
        if self.tray_icon: self.tray_icon.stop()
        if self.app.radar: self.app.radar.detener()
        self.root.quit()
        sys.exit(0)

# ==================== CLASE PRINCIPAL: KALM-USB-KOPY ====================
class KalmUSBKopy:
    def __init__(self, root):
        self.root = root
        self.config = ConfigManager()
        self.history = HistoryManager()
        self.memory = MemoryManager()
        
        self.root.title(f"⚔️ {APP_NAME} v{APP_VERSION} | Nexus Autónomo")
        self.root.geometry("1280x850")
        self.root.minsize(1100, 750)
        self.root.configure(bg=VOID_BG)
        
        self.aplicar_estilo_cyber()
        
        self.unidad_sel = None
        self.memoria_sel_id = None
        self.memoria_sel_data = None
        self.internal_copy_active = False # Flag para el radar externo
        
        self.crear_interfaz_nexus()
        self.cargar_estado_inicial()
        
        # Iniciar Sistemas Autónomos
        self.radar = ExternalCopyRadar(self)
        self.radar.iniciar()
        
        self.tray_manager = SystemTrayManager(self, self.root)
        if self.config.obtener("minimizar_bandeja"):
            self.tray_manager.iniciar_bandeja()
            
        if self.config.obtener("iniciar_con_windows"):
            self.agregar_inicio_windows()
            
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    def aplicar_estilo_cyber(self):
        if BOOTSTRAP_AVAILABLE:
            self.style = tb.Style("cyborg")
            self.style.configure('.', background=VOID_BG, foreground=TEXT_MAIN, fieldbackground=PANEL_BG)
            self.style.configure('TFrame', background=VOID_BG)
            self.style.configure('TLabel', background=VOID_BG, foreground=TEXT_MAIN, font=('Segoe UI', 10))
            self.style.configure('Header.TLabel', font=('Segoe UI', 24, 'bold'), foreground=NEON_PURPLE)
            self.style.configure('SubHeader.TLabel', font=('Segoe UI', 11), foreground=NEON_CYAN)
            self.style.configure('TButton', background=PANEL_BG, foreground=NEON_CYAN, borderwidth=1)
            self.style.map('TButton', background=[('active', NEON_PURPLE), ('pressed', NEON_PURPLE)])
            self.style.configure('Neon.TButton', background=NEON_PURPLE, foreground="white", font=('Segoe UI', 10, 'bold'))
            self.style.map('Neon.TButton', background=[('active', '#d04fff'), ('pressed', '#8a1cc7')])
            self.style.configure('Treeview', background=PANEL_BG, foreground=TEXT_MAIN, fieldbackground=PANEL_BG, rowheight=28)
            self.style.configure('Treeview.Heading', background="#1a1a24", foreground=NEON_CYAN, font=('Segoe UI', 10, 'bold'))
            self.style.map('Treeview', background=[('selected', NEON_PURPLE)])
            self.style.configure('TNotebook', background=VOID_BG, borderwidth=0)
            self.style.configure('TNotebook.Tab', background=PANEL_BG, foreground=NEON_CYAN, padding=[15, 8], font=('Segoe UI', 10, 'bold'))
            self.style.map('TNotebook.Tab', background=[('selected', NEON_PURPLE)], foreground=[('selected', 'white')])

    def crear_interfaz_nexus(self):
        header = tk.Frame(self.root, bg="#0d0d14", height=80)
        header.pack(fill=X, side=TOP)
        header.pack_propagate(False)
        tk.Label(header, text="⚔️ KALM-NEXUS", font=('Segoe UI', 28, 'bold'), bg="#0d0d14", fg=NEON_PURPLE).pack(side=LEFT, padx=20, pady=15)
        
        # Indicador de Radar Activo
        self.lbl_radar = tk.Label(header, text="👁️ RADAR EXTERNO: ACTIVO", font=('Consolas', 10, 'bold'), bg="#0d0d14", fg=NEON_GREEN)
        self.lbl_radar.pack(side=LEFT, padx=20, pady=35)
        
        self.lbl_precio_status = tk.Label(header, text=f"💰 Tarifa Base: ${self.config.obtener_precio()}/GB", 
                                          font=('Consolas', 12, 'bold'), bg="#0d0d14", fg=NEON_CYAN)
        self.lbl_precio_status.pack(side=RIGHT, padx=20, pady=25)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=5)
        self.tab_principal = ttk.Frame(self.notebook)
        self.tab_memorias = ttk.Frame(self.notebook)
        self.tab_crono = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_principal, text=" 🌌 NEXUS PRINCIPAL ")
        self.notebook.add(self.tab_memorias, text=" 💾 BASE DE MEMORIAS ")
        self.notebook.add(self.tab_crono, text=" 📜 CRONO-REGISTRO ")
        self.crear_tab_principal()
        self.crear_tab_memorias()
        self.crear_tab_crono()
        self.crear_terminal_hacker()

    def crear_tab_principal(self):
        left_frame = ttk.Frame(self.tab_principal)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)
        ttk.Label(left_frame, text="🔮 NEXUS DE MEMORIAS (Uplink)", style='SubHeader.TLabel').pack(anchor=W, pady=(0,5))
        self.tree_usb = ttk.Treeview(left_frame, columns=('Letra', 'Nombre', 'Libre'), show='headings', height=6)
        self.tree_usb.heading('Letra', text='Unidad'); self.tree_usb.heading('Nombre', text='Identidad'); self.tree_usb.heading('Libre', text='Espacio Libre (GB)')
        self.tree_usb.column('Letra', width=60); self.tree_usb.column('Nombre', width=150); self.tree_usb.column('Libre', width=100)
        self.tree_usb.pack(fill=BOTH, expand=True)
        self.tree_usb.bind('<<TreeviewSelect>>', self.on_seleccionar_usb)
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=X, pady=10)
        ttk.Button(btn_frame, text="🔄 Sincronizar Uplink", command=self.actualizar_unidades).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="🚀 INICIAR COPIA INTERNA", command=self.iniciar_copia, style='Neon.TButton').pack(side=RIGHT, padx=5)

        right_frame = ttk.Frame(self.tab_principal)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)
        ttk.Label(right_frame, text="⚡ NÚCLEO DE COPIA", style='SubHeader.TLabel').pack(anchor=W)
        stats_frame = ttk.Frame(right_frame)
        stats_frame.pack(fill=X, pady=10)
        self.card_copias = self.crear_card_stat(stats_frame, "📋 Copias Hoy", "0", NEON_CYAN)
        self.card_copias.pack(side=LEFT, fill=X, expand=True, padx=5)
        self.card_gb = self.crear_card_stat(stats_frame, "💾 GB Procesados", "0.00", NEON_GREEN)
        self.card_gb.pack(side=LEFT, fill=X, expand=True, padx=5)
        self.card_ingresos = self.crear_card_stat(stats_frame, "💰 Ingresos", "$0.00", NEON_PURPLE)
        self.card_ingresos.pack(side=LEFT, fill=X, expand=True, padx=5)
        
        info_frame = ttk.LabelFrame(right_frame, text=" Datos de Transferencia ", padding=10)
        info_frame.pack(fill=X, pady=10)
        self.lbl_memoria_sel = ttk.Label(info_frame, text="Memoria: [ Ninguna Seleccionada ]", font=('Consolas', 11, 'bold'))
        self.lbl_memoria_sel.pack(anchor=W, pady=5)
        self.lbl_precio_est = ttk.Label(info_frame, text="Costo Estimado: $0.00 CUP", font=('Consolas', 14, 'bold'), foreground=NEON_GREEN)
        self.lbl_precio_est.pack(anchor=W, pady=5)

    def crear_card_stat(self, parent, titulo, valor, color):
        frame = tk.Frame(parent, bg=PANEL_BG, highlightbackground=color, highlightthickness=2)
        tk.Label(frame, text=titulo, bg=PANEL_BG, fg=TEXT_DIM, font=('Segoe UI', 9)).pack(pady=(10,0))
        lbl_val = tk.Label(frame, text=valor, bg=PANEL_BG, fg=color, font=('Consolas', 18, 'bold'))
        lbl_val.pack(pady=(0,10))
        frame.lbl_val = lbl_val
        return frame

    def crear_tab_memorias(self):
        ttk.Label(self.tab_memorias, text="💾 ARCHIVOS DEL NEXUS", style='SubHeader.TLabel').pack(anchor=W, padx=10, pady=10)
        self.tree_memorias = ttk.Treeview(self.tab_memorias, columns=('Nombre', 'Veces', 'GB', 'Ingresos'), show='headings', height=15)
        self.tree_memorias.heading('Nombre', text='Identidad'); self.tree_memorias.heading('Veces', text='Conexiones')
        self.tree_memorias.heading('GB', text='Total GB'); self.tree_memorias.heading('Ingresos', text='Ingresos ($)')
        self.tree_memorias.pack(fill=BOTH, expand=True, padx=10, pady=5)

    def crear_tab_crono(self):
        ttk.Label(self.tab_crono, text="📜 CRONO-REGISTRO (Historial)", style='SubHeader.TLabel').pack(anchor=W, padx=10, pady=10)
        self.tree_crono = ttk.Treeview(self.tab_crono, columns=('Fecha', 'Memoria', 'GB', 'Precio', 'Estado'), show='headings', height=15)
        self.tree_crono.heading('Fecha', text='Timestamp'); self.tree_crono.heading('Memoria', text='Identidad')
        self.tree_crono.heading('GB', text='GB'); self.tree_crono.heading('Precio', text='Precio'); self.tree_crono.heading('Estado', text='Estado')
        self.tree_crono.pack(fill=BOTH, expand=True, padx=10, pady=5)

    def crear_terminal_hacker(self):
        term_frame = tk.Frame(self.root, bg="#000000", height=150)
        term_frame.pack(fill=X, side=BOTTOM, padx=10, pady=(0, 10))
        tk.Label(term_frame, text=">>> SYSTEM_TERMINAL // KALM-NEXUS RADAR", bg="#000000", fg=NEON_GREEN, font=('Consolas', 9, 'bold')).pack(anchor=W, padx=5, pady=2)
        self.terminal = scrolledtext.ScrolledText(term_frame, bg="#050505", fg=NEON_GREEN, font=("Consolas", 9), insertbackground=NEON_GREEN, relief=FLAT, borderwidth=0, height=6)
        self.terminal.pack(fill=BOTH, expand=True, padx=5, pady=2)
        self.terminal.config(state=DISABLED)
        self.terminal.tag_config("info", foreground=NEON_CYAN)
        self.terminal.tag_config("success", foreground=NEON_GREEN)
        self.terminal.tag_config("magic", foreground=NEON_PURPLE)
        self.terminal.tag_config("error", foreground=NEON_RED)

    def log_terminal(self, msg, tag="info"):
        self.terminal.config(state=NORMAL)
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.terminal.insert(END, f"[{timestamp}] {msg}\n", tag)
        self.terminal.see(END)
        self.terminal.config(state=DISABLED)

    # ==================== LÓGICA DE NEGOCIO ====================
    def actualizar_unidades(self):
        for i in self.tree_usb.get_children(): self.tree_usb.delete(i)
        unidades = []
        for p in psutil.disk_partitions():
            if 'removable' in p.opts:
                try:
                    uso = psutil.disk_usage(p.mountpoint)
                    unidades.append({'letra': p.mountpoint, 'libre_gb': round(uso.free / (1024**3), 2)})
                except: pass
        if not unidades:
            self.tree_usb.insert('', 0, values=('N/A', 'Sin Uplink Activo', '0.00'))
            return
        for u in unidades:
            mem_id, data = self.memory.identificar_memoria(u['letra'])
            nombre = data.get('nombre', 'Nueva Entidad')
            self.tree_usb.insert('', END, values=(u['letra'], nombre, f"{u['libre_gb']:.2f}"))
        self.log_terminal(f"Uplink sincronizado. {len(unidades)} entidades en radar.", "success")

    def on_seleccionar_usb(self, event):
        sel = self.tree_usb.selection()
        if not sel: return
        vals = self.tree_usb.item(sel[0], 'values')
        if vals[0] == 'N/A': return
        self.unidad_sel = vals[0]
        mem_id, data = self.memory.identificar_memoria(vals[0], vals[1])
        self.memoria_sel_id = mem_id
        self.memoria_sel_data = data
        self.lbl_memoria_sel.config(text=f"Memoria: [ {vals[1]} ] :: {vals[0]}")
        libre = float(vals[2])
        precio_max = calcular_precio_inteligente(libre)
        self.lbl_precio_est.config(text=f"Costo Máximo ({libre}GB): ${precio_max:.2f} CUP")

    def iniciar_copia(self):
        if not self.unidad_sel:
            messagebox.showwarning("Alerta del Nexus", "Selecciona una entidad primero.")
            return
        win = tk.Toplevel(self.root)
        win.title("⚡ Protocolo de Transferencia Interna")
        win.geometry("450x350")
        win.configure(bg=VOID_BG)
        win.transient(self.root)
        win.grab_set()
        tk.Label(win, text="⚡ PROTOCOLO INTERNO", bg=VOID_BG, fg=NEON_PURPLE, font=('Segoe UI', 14, 'bold')).pack(pady=15)
        try: uso = psutil.disk_usage(self.unidad_sel)
        except: uso = None
        libre = round(uso.free / (1024**3), 2) if uso else 0
        tk.Label(win, text=f"Entidad: {self.memoria_sel_data.get('nombre', 'N/A')}", bg=VOID_BG, fg=TEXT_MAIN).pack(anchor=W, padx=30)
        tk.Label(win, text=f"Espacio Disponible: {libre} GB", bg=VOID_BG, fg=NEON_CYAN).pack(anchor=W, padx=30, pady=5)
        tk.Label(win, text="Cantidad de GB a transferir:", bg=VOID_BG, fg=TEXT_MAIN).pack(anchor=W, padx=30, pady=(15,0))
        gb_var = tk.StringVar(value=f"{min(libre, 4):.2f}")
        tk.Entry(win, textvariable=gb_var, bg=PANEL_BG, fg=NEON_GREEN, font=('Consolas', 14), insertbackground=NEON_GREEN, relief=FLAT).pack(fill=X, padx=30, pady=5, ipady=5)
        lbl_precio = tk.Label(win, text="Costo: $0.00 CUP", bg=VOID_BG, fg=NEON_GREEN, font=('Consolas', 16, 'bold'))
        lbl_precio.pack(pady=15)
        def actualizar_precio(*args):
            try:
                gb = float(gb_var.get())
                precio = calcular_precio_inteligente(gb)
                lbl_precio.config(text=f"Costo: ${precio:.2f} CUP")
            except: lbl_precio.config(text="Costo: $0.00 CUP")
        gb_var.trace('w', actualizar_precio)
        actualizar_precio()
        def confirmar():
            try:
                gb = float(gb_var.get())
                if gb <= 0 or gb > libre:
                    messagebox.showerror("Error", "Cantidad inválida o espacio insuficiente.")
                    return
                precio = calcular_precio_inteligente(gb)
                self.internal_copy_active = True # Pausar radar externo
                registro = {
                    'nombre_memoria': self.memoria_sel_data.get('nombre'),
                    'unidad': self.unidad_sel, 'gb_copiados': gb, 'precio': precio,
                    'hora': datetime.datetime.now().strftime("%H:%M:%S"), 'estado': 'Interno Completado'
                }
                self.history.agregar_registro(registro)
                self.memory.registrar_copia(self.memoria_sel_id, gb, precio)
                win.destroy()
                self.log_terminal(f"Transferencia interna exitosa: {gb}GB -> ${precio} CUP", "success")
                self.actualizar_stats_rapidas()
                self.actualizar_crono()
                self.actualizar_lista_memorias()
                if NOTIFICATION_AVAILABLE and self.config.obtener("mostrar_notificaciones"):
                    notification.notify(title="Kalm-Nexus", message=f"Copia interna de {gb}GB completada.\nCosto: ${precio} CUP", timeout=5)
                self.root.after(5000, self._reactivar_radar) # Reactivar radar tras 5 seg
            except ValueError:
                messagebox.showerror("Error", "Ingresa un número válido.")
        tk.Button(win, text="🚀 EJECUTAR TRANSFERENCIA", bg=NEON_PURPLE, fg="white", font=('Segoe UI', 11, 'bold'), relief=FLAT, command=confirmar).pack(pady=10, ipady=5, ipadx=20)

    def _reactivar_radar(self):
        self.internal_copy_active = False

    def actualizar_stats_rapidas(self):
        hoy = datetime.datetime.now().date().isoformat()
        regs = [r for r in self.history.historial if r['fecha'].startswith(hoy)]
        total_gb = sum(r.get('gb_copiados', 0) for r in regs)
        total_p = sum(r.get('precio', 0) for r in regs)
        self.card_copias.lbl_val.config(text=str(len(regs)))
        self.card_gb.lbl_val.config(text=f"{total_gb:.2f}")
        self.card_ingresos.lbl_val.config(text=f"${total_p:.2f}")

    def actualizar_crono(self):
        for i in self.tree_crono.get_children(): self.tree_crono.delete(i)
        for r in reversed(self.history.historial[-50:]):
            fecha = datetime.datetime.fromisoformat(r['fecha']).strftime("%Y-%m-%d %H:%M")
            self.tree_crono.insert('', 0, values=(fecha, r.get('nombre_memoria'), r.get('gb_copiados'), f"${r.get('precio')}", r.get('estado')))

    def actualizar_lista_memorias(self):
        for i in self.tree_memorias.get_children(): self.tree_memorias.delete(i)
        for mid, data in self.memory.memorias.items():
            self.tree_memorias.insert('', END, values=(
                data.get('nombre'), data.get('veces_usada'), 
                f"{data.get('total_gb_copiados', 0):.2f}", f"${data.get('total_ingresos', 0):.2f}"
            ))

    def cargar_estado_inicial(self):
        self.actualizar_stats_rapidas()
        self.actualizar_crono()
        self.actualizar_lista_memorias()
        self.actualizar_unidades()
        self.log_terminal("Nexus inicializado. Radar Externo escaneando el flujo de datos...", "success")

    def on_close(self):
        if self.config.obtener("minimizar_bandeja") and PYSTRAY_AVAILABLE:
            self.tray_manager.ocultar_ventana()
            self.log_terminal("Interfaz ocultada. Nexus y Radar operando en segundo plano...", "magic")
        else:
            self.tray_manager.salir_aplicacion()

    def agregar_inicio_windows(self):
        try:
            ruta = sys.executable if sys.executable.endswith('.exe') else os.path.abspath(sys.argv[0])
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "KalmUSBKopy", 0, winreg.REG_SZ, f'"{ruta}"')
            winreg.CloseKey(key)
        except: pass

    def generar_informe(self):
        messagebox.showinfo("Informe", "Generando informe del Nexus... (Función de ejemplo)")

# ==================== MAIN ====================
def main():
    root = tb.Window(themename="cyborg") if BOOTSTRAP_AVAILABLE else tk.Tk()
    if not BOOTSTRAP_AVAILABLE: root.configure(bg=VOID_BG)
    app = KalmUSBKopy(root)
    try: root.mainloop()
    except KeyboardInterrupt:
        if app.radar: app.radar.detener()
        sys.exit(0)

if __name__ == "__main__":
    main()
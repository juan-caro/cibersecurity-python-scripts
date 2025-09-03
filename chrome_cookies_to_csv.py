import os
import sqlite3
import csv
import shutil
import base64
import json
import win32crypt
from datetime import datetime
from Crypto.Cipher import AES

def get_chrome_master_key(local_state_path):
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    encrypted_key = encrypted_key[5:]
    master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    return master_key

def decrypt_chrome_value(encrypted_value, master_key):
    """Descifra el valor de la cookie, sea AES-GCM (v10) o DPAPI. Otros formatos se marcan como no descifrables."""
    try:
        if encrypted_value is None:
            return ""
        if encrypted_value[:3] == b'v10':  # AES-GCM
            iv = encrypted_value[3:15]
            payload = encrypted_value[15:-16]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            return cipher.decrypt(payload).decode()
        elif encrypted_value[:3] == b'v11' or encrypted_value[:3] == b'v20':
            return "[No descifrado: formato v11/v20]"
        else:  # DPAPI
            return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
    except Exception as e:
        return f"[Error descifrado: {e}]"


def find_cookies_file(profile_path):
    """Busca recursivamente un archivo llamado 'Cookies' dentro del perfil."""
    for root, dirs, files in os.walk(profile_path):
        if "Cookies" in files:
            return os.path.join(root, "Cookies")
    return None

def export_chrome_cookies(profile_name, output_file):
    chrome_user_data = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    profile_path = os.path.join(chrome_user_data, profile_name)
    local_state_path = os.path.join(chrome_user_data, "Local State")

    if not os.path.exists(profile_path):
        print(f"[!] No existe la carpeta del perfil: {profile_name}")
        return
    if not os.path.exists(local_state_path):
        print("[!] No se encontró el archivo Local State de Chrome.")
        return

    cookies_path = find_cookies_file(profile_path)
    if not cookies_path:
        print(f"[!] No se encontró el archivo Cookies en el perfil: {profile_name}")
        return

    master_key = get_chrome_master_key(local_state_path)
    temp_db = os.path.join(os.environ['TEMP'], f"Chrome_{profile_name}_Cookies_temp.db")
    shutil.copy2(cookies_path, temp_db)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Cabecera sin Cookie Name
        writer.writerow(['Profile', 'Domain', 'Creation Date', 'Last Access Date'])

        try:
            cursor.execute("SELECT host_key, creation_utc, last_access_utc FROM cookies")
            filas = cursor.fetchall()
            print(f"[+] {len(filas)} cookies encontradas en el perfil '{profile_name}'")
            for host, creation, last_access in filas:
                try:
                    creation_dt = datetime.utcfromtimestamp((creation/1000000)-11644473600)
                except:
                    creation_dt = ""
                try:
                    last_access_dt = datetime.utcfromtimestamp((last_access/1000000)-11644473600)
                except:
                    last_access_dt = ""
                writer.writerow([profile_name, host, creation_dt, last_access_dt])
        except Exception as e:
            print(f"[!] Error leyendo cookies: {e}")


    conn.close()
    os.remove(temp_db)
    print(f"✅ Exportación completada: {output_file}")

if __name__ == "__main__":
    perfil = input("Introduce el nombre del perfil de Chrome (ej: Default, Profile 1, Profile 2): ").strip()
    output_csv = f"chrome_cookies_{perfil}.csv"
    export_chrome_cookies(perfil, output_csv)

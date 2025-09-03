import os
import sqlite3
import csv
from datetime import datetime

def export_firefox_cookies(profile_path, output_file):
    db_path = os.path.join(profile_path, "cookies.sqlite")

    if not os.path.exists(db_path):
        print(f"[!] No se encontró la base de datos de cookies en: {db_path}")
        return

    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    cursor = conn.cursor()

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Profile', 'Domain', 'Cookie Name', 'Value', 'Creation Date', 'Last Access Date'])

        try:
            cursor.execute("SELECT host, name, value, creationTime, lastAccessed FROM moz_cookies")
            filas = cursor.fetchall()
            print(f"[+] {len(filas)} cookies encontradas en el perfil '{profile_path}'")

            for host, name, value, creation, last_access in filas:
                try:
                    creation_dt = datetime.utcfromtimestamp(creation/1000000)
                except:
                    creation_dt = ""
                try:
                    last_access_dt = datetime.utcfromtimestamp(last_access/1000000)
                except:
                    last_access_dt = ""
                writer.writerow([os.path.basename(profile_path), host, name, value, creation_dt, last_access_dt])
        except Exception as e:
            print(f"[!] Error leyendo cookies: {e}")

    conn.close()
    print(f"✅ Exportación completada: {output_file}")


if __name__ == "__main__":
    base_path = os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
    if not os.path.exists(base_path):
        print("[!] No se encontró la carpeta de perfiles de Firefox.")
    else:
        perfiles = os.listdir(base_path)
        print("[+] Perfiles disponibles:")
        for i, p in enumerate(perfiles):
            print(f"   {i+1}. {p}")

        idx = int(input("Selecciona el número del perfil: ")) - 1
        profile_path = os.path.join(base_path, perfiles[idx])
        output_csv = f"firefox_cookies_{perfiles[idx]}.csv"
        export_firefox_cookies(profile_path, output_csv)

import paho.mqtt.client as mqtt
import mysql.connector
import json
from datetime import datetime

#1. Konfigurasi
MQTT_BROKER = "broker.mqtt-dashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/data/iot_uts"

# Konfigurasi Database (Sesuaikan dengan DB kamu)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'oop',
    'database': 'uts_db'
}

# --- 2. Fungsi untuk Menyimpan ke Database ---
def save_to_db(suhu, kelembaban, kecerahan):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Dapatkan timestamp SAAT INI
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Query SQL untuk memasukkan data
        query = "INSERT INTO data_sensor (suhu, humidity, lux, timestamp) VALUES (%s, %s, %s, %s)"
        values = (suhu, kelembaban, kecerahan, timestamp)
        
        cursor.execute(query, values)
        conn.commit() # Simpan perubahan
        
        print(f"[DB] Data disimpan: Suhu={suhu}, Humid={kelembaban}, Lux={kecerahan}, Time={timestamp}")

    except mysql.connector.Error as err:
        print(f"[DB ERROR] {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

#3. Fungsi Callback MQTT

# Fungsi ini dipanggil saat berhasil terhubung ke broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Berhasil terhubung ke broker {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC)
        print(f"[MQTT] Subscribe ke topik: {MQTT_TOPIC}")
    else:
        print(f"[MQTT] Gagal terhubung, return code {rc}")

# Fungsi ini dipanggil setiap ada PESAN MASUK dari Wokwi
def on_message(client, userdata, msg):
    print(f"[MQTT] Pesan diterima dari topik {msg.topic}: {msg.payload.decode()}")
    
    try:
        data = json.loads(msg.payload.decode())
        
        # Ambil data sensor dari JSON
        suhu = data.get('suhu')
        kelembaban = data.get('humidity') 
        kecerahan = data.get('lux')      
        
        # Panggil fungsi untuk simpan ke DB
        if suhu is not None and kelembaban is not None and kecerahan is not None:
            save_to_db(suhu, kelembaban, kecerahan)
        else:
            print("[JSON ERROR] Data JSON tidak lengkap (suhu/humidity/lux tidak ada)")
            
    except json.JSONDecodeError:
        print("[JSON ERROR] Gagal parsing JSON dari MQTT")
    except Exception as e:
        print(f"[ERROR LAIN] {e}")

#4. Fungsi Utama
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        print("[SISTEM] Menjalankan Subscriber. Program ini akan terus mendengarkan data dari Wokwi...")
        client.loop_forever()

    except KeyboardInterrupt:
        print("[SISTEM] Program dihentikan.")
        client.disconnect()
    except Exception as e:
        print(f"[KONEKSI ERROR] Gagal terhubung ke {MQTT_BROKER}. Pastikan internet menyala. Error: {e}")

if __name__ == '__main__':
    main()
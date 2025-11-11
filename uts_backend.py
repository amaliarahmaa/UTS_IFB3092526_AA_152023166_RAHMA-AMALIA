from flask import Flask, jsonify, render_template
import mysql.connector
from decimal import Decimal
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Konfigurasi Database (Pastikan sama dengan 'subscriber.py')
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'oop',
    'database': 'uts_db' # <-- Kamu pakai 'uts_db' di kode sebelumnya
}

# --- INI FUNGSI YANG SUDAH DIPERBAIKI ---
def get_sensor_summary():
    json_output = {
        "suhumax": 0,
        "suhumin": 0,
        "suhurata": 0.0,
        "nilai_suhu_max_humid_max": [],
        "month_year_max": []
    }

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 1. AMBIL DATA AGREGAT
        cursor.execute("SELECT MAX(suhu) as max_suhu, MIN(suhu) as min_suhu, AVG(suhu) as avg_suhu FROM data_sensor")
        agregat = cursor.fetchone()

        # Cek apakah tabelnya berisi data
        if agregat and agregat['max_suhu'] is not None:
            # Mengisi nilai agregat ke struktur JSON
            json_output["suhumax"] = agregat['max_suhu']
            json_output["suhumin"] = agregat['min_suhu']
            
            avg_val = agregat['avg_suhu']
            if avg_val is not None:
                 json_output["suhurata"] = round(float(avg_val), 2)
            else:
                 json_output["suhurata"] = 0.0

            
            # 2. AMBIL DATA DETAIL (QUERY SUDAH DIPERBAIKI)
            # Query ini "lebih pintar" dan aman untuk tipe data FLOAT
            query_detail = """
                SELECT id, suhu, humidity, lux, timestamp 
                FROM data_sensor 
                WHERE suhu = (SELECT MAX(suhu) FROM data_sensor)
            """
            
            cursor.execute(query_detail)
            rows = cursor.fetchall()

            # 3. Looping hasil data detail
            for row in rows:
                ts_str = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                
                # Masukkan ke array 'nilai_suhu_max_humid_max'
                json_output["nilai_suhu_max_humid_max"].append({
                    "idx": row['id'],
                    "suhu": row['suhu'],
                    "humid": row['humidity'],
                    "kecerahan": row['lux'],
                    "timestamp": ts_str
                })

                # Masukkan ke array 'month_year_max'
                month_year_str = row['timestamp'].strftime('%m-%Y')
                json_output["month_year_max"].append({
                    "month_year": month_year_str
                })

        cursor.close()
        conn.close()
        return json_output

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return {"error": str(err)}
    except Exception as e:
        print(f"Error Lain: {e}")
        return {"error": str(e)}

# --- ROUTE API (Untuk diambil Frontend) ---
@app.route('/api/data-json')
def api_data():
    data = get_sensor_summary()
    return jsonify(data)

# --- ROUTE WEB (Untuk Halaman index.html) ---
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        # Jika file index.html atau folder 'templates' tidak ada
        print(f"Error rendering template: {e}")
        return "Error: Pastikan file 'index.html' ada di dalam folder 'templates'."

if __name__ == '__main__':
    # Jalankan server Flask
    app.run(debug=True, port=5000)
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# Functie om verbinding te maken met de database
def get_db_connection():
    conn = sqlite3.connect('markers.db')
    conn.row_factory = sqlite3.Row  # Maakt het mogelijk om rijen als dictionary's te krijgen
    return conn

# Maak een tabel voor de coördinaten als deze nog niet bestaat
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS markers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        latitude REAL,
        longitude REAL,
        tpms_id TEXT,
        model TEXT,
        type TEXT,
        flags TEXT,
        pressure REAL,
        temperature REAL,
        status TEXT,
        integrity TEXT
    );
    ''')
    conn.commit()
    conn.close()

# Functie om een marker toe te voegen
def add_marker(name, latitude, longitude, tpms_data=None):
    conn = get_db_connection()
    c = conn.cursor()

    # Parse TPMS data
    tpms_id = tpms_data.get('id') if tpms_data else None
    model = tpms_data.get('model') if tpms_data else None
    tpms_type = tpms_data.get('type') if tpms_data else None
    flags = tpms_data.get('flags') if tpms_data else None
    pressure = tpms_data.get('Pressure') if tpms_data else None
    temperature = tpms_data.get('Temperature') if tpms_data else None
    status = tpms_data.get('status') if tpms_data else None
    integrity = tpms_data.get('Integrity') if tpms_data else None

    # Voeg data toe aan de database
    c.execute('''
    INSERT INTO markers (name, latitude, longitude, tpms_id, model, type, flags, pressure, temperature, status, integrity)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, latitude, longitude, tpms_id, model, tpms_type, flags, pressure, temperature, status, integrity))

    conn.commit()
    conn.close()

# Functie om alle markers uit te lezen
def get_all_markers():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM markers')
    markers = c.fetchall()
    conn.close()
    return markers

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/markers', methods=['GET', 'POST'])
def api_markers():
    if request.method == 'POST':
        data = request.get_json()
        if 'lat' in data and 'lng' in data and 'name' in data:
            tpms_data = data.get('tpms_data')  # Voeg TPMS-data toe als beschikbaar
            add_marker(data['name'], data['lat'], data['lng'], tpms_data)
            return jsonify({"message": "Marker toegevoegd!", "marker": data}), 201
        else:
            return jsonify({"error": "Foutieve data"}), 400
    # Haal alle markers op uit de database en geef ze terug als JSON
    markers = get_all_markers()
    return jsonify([{
        "name": marker["name"],
        "lat": marker["latitude"],
        "lng": marker["longitude"],
        "tpms_data": {
            "id": marker["tpms_id"],
            "model": marker["model"],
            "type": marker["type"],
            "flags": marker["flags"],
            "pressure": marker["pressure"],
            "temperature": marker["temperature"],
            "status": marker["status"],
            "integrity": marker["integrity"]
        }
    } for marker in markers])

if __name__ == '__main__':
    init_db()  # Zorg ervoor dat de database en tabel wordt aangemaakt bij opstarten
    app.run(debug=True)

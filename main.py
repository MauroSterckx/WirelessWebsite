from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import sqlite3
import matplotlib.pyplot as plt
from io import BytesIO

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

@app.route('/api/markers/<int:marker_id>', methods=['DELETE'])
def delete_marker(marker_id):
    conn = get_db_connection()
    c = conn.cursor()

    # Controleer of de marker bestaat
    c.execute('SELECT * FROM markers WHERE id = ?', (marker_id,))
    marker = c.fetchone()

    if marker is None:
        conn.close()
        return jsonify({"error": "Marker niet gevonden"}), 404

    # Verwijder de marker
    c.execute('DELETE FROM markers WHERE id = ?', (marker_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Marker met ID {marker_id} verwijderd"}), 200

#### Grafieken

@app.route('/graph')
def generate_graph():
    # Data ophalen uit de database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, pressure, temperature FROM markers')
    data = c.fetchall()
    conn.close()

    # Extract data
    indices = [row['id'] for row in data]  # ID's als x-as
    pressures = [row['pressure'] for row in data if row['pressure'] is not None and 50 <= row['pressure'] <= 1000]  # Filter uitschieters
    temperatures = [row['temperature'] for row in data if row['temperature'] is not None]

    # Controle op lege datasets
    if not pressures or not temperatures:
        return "Geen data beschikbaar om te visualiseren", 400

    # Berekeningen voor statistieken
    avg_pressure = sum(pressures) / len(pressures) if pressures else 0
    avg_temperature = sum(temperatures) / len(temperatures) if temperatures else 0

    # Grafiek maken
    plt.figure(figsize=(12, 8))
    plt.plot(indices[:len(pressures)], pressures, label='Druk (kPa)', color='blue', marker='o', linestyle='-')
    plt.plot(indices[:len(temperatures)], temperatures, label='Temperatuur (°C)', color='red', marker='x', linestyle='--')

    # Duidelijke titel en labels
    plt.title('TPMS Data: Druk en Temperatuur Over Tijd', fontsize=16)
    plt.xlabel('Data ID (of Tijd)', fontsize=12)
    plt.ylabel('Waarden', fontsize=12)

    # Voeg gemiddelde waarden toe aan de grafiek
    plt.axhline(y=avg_pressure, color='blue', linestyle=':', label=f'Gemiddelde Druk: {avg_pressure:.2f} kPa')
    plt.axhline(y=avg_temperature, color='red', linestyle=':', label=f'Gemiddelde Temperatuur: {avg_temperature:.2f}°C')

    # Voeg grid en legende toe
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend(fontsize=12, loc='center left', bbox_to_anchor=(1, 0.5))  # Legende naar de zijkant

    # Annotatie voor maximale druk en temperatuur
    if pressures:
        max_pressure = max(pressures)
        max_index = indices[pressures.index(max_pressure)]
        plt.annotate(f'Max druk: {max_pressure} kPa', xy=(max_index, max_pressure),
                     xytext=(max_index + 2, max_pressure + 10),
                     arrowprops=dict(facecolor='blue', arrowstyle='->'),
                     fontsize=10)

    if temperatures:
        max_temp = max(temperatures)
        max_index = indices[temperatures.index(max_temp)]
        plt.annotate(f'Max temp: {max_temp}°C', xy=(max_index, max_temp),
                     xytext=(max_index + 2, max_temp + 1),
                     arrowprops=dict(facecolor='red', arrowstyle='->'),
                     fontsize=10)

    # Grafiek opslaan in memory
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')  # bbox_inches='tight' zorgt voor een strakkere lay-out
    buf.seek(0)
    plt.close()

    # Grafiek retourneren als afbeelding
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    init_db()  # Zorg ervoor dat de database en tabel wordt aangemaakt bij opstarten
    app.run(debug=True, host='0.0.0.0', port=5000)

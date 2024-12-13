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
        longitude REAL
    )
    ''')
    conn.commit()
    conn.close()

# Functie om een marker toe te voegen
def add_marker(name, latitude, longitude):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
    INSERT INTO markers (name, latitude, longitude)
    VALUES (?, ?, ?)
    ''', (name, latitude, longitude))
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
            # Voeg marker toe aan de database
            add_marker(data['name'], data['lat'], data['lng'])
            return jsonify({"message": "Marker toegevoegd!", "marker": data}), 201
        else:
            return jsonify({"error": "Foutieve data"}), 400
    # Haal alle markers op uit de database en geef ze terug als JSON
    markers = get_all_markers()
    # return jsonify([dict(marker) for marker in markers])
    return jsonify([{
        "name": marker["name"],
        "lat": marker["latitude"],
        "lng": marker["longitude"]
    } for marker in markers])

if __name__ == '__main__':
    init_db()  # Zorg ervoor dat de database en tabel wordt aangemaakt bij opstarten
    app.run(debug=True)

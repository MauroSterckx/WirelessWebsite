from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Lijst om markers op te slaan
markers = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/markers', methods=['GET', 'POST'])
def api_markers():
    global markers
    if request.method == 'POST':
        data = request.get_json()
        if 'lat' in data and 'lng' in data and 'name' in data:
            marker = {
                'lat': data['lat'],
                'lng': data['lng'],
                'name': data['name']
            }
            markers.append(marker)
            return jsonify({"message": "Marker toegevoegd!", "marker": marker}), 201
        else:
            return jsonify({"error": "Foutieve data"}), 400
    return jsonify(markers)

if __name__ == '__main__':
    app.run(debug=True)

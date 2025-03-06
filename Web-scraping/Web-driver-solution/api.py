from flask import Flask, jsonify, request, session
from flask_session import Session
from main import extract_prices
from urllib.parse import urlparse
import os
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/api/extract-price', methods=['GET'])
def extract_price():
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Validate URL
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return jsonify({'error': 'Invalid URL format'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid URL'}), 400

        # Extract prices
        prices = extract_prices(url)

        if not prices:
            return jsonify({'error': 'No prices found'}), 404

        # Format response
        response = {
            'url': url,
            'count': len(prices),
            'prices': [
                {
                    'price': item['price'],
                    'tag': item['tag_name'],
                    'attributes': item['attributes']
                }
                for item in prices
            ]
        }

        # Save interaction in session
        if 'interactions' not in session:
            session['interactions'] = []
        session['interactions'].append(response)

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/interactions', methods=['GET'])
def get_interactions():
    return jsonify(session.get('interactions', []))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
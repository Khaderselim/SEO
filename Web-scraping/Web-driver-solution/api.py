from threading import Thread

from flask import Flask, jsonify, request, session

from compare import compare_product
from flask_session import Session
from main import extract_pattern
from urllib.parse import urlparse
import os
from price import DOMPriceExtractor

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
extractor = DOMPriceExtractor()
@app.route('/api/extract-patterns', methods=['GET'])
def extract_patterns():
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
        prices,description,stock = extract_pattern(url)

        if not prices:
            return jsonify({'error': 'No prices found'}), 404

        # Format response
        response = {
            'url': url,
            'description': [{
                'text_content': item['text_content'],
                'tag': item['tag_name'],
                'attributes': item['attributes']
            }
            for item in description],
            'prices': [
                {
                    'price': item['price'],
                    'tag': item['tag_name'],
                    'attributes': item['attributes']
                }
                for item in prices
            ],
            'stock': [
                {
                    'stock': item['text_content'],
                    'tag': item['tag_name'],
                    'attributes': item['attributes']
                }
                for item in stock
            ]
        }

        # Save interaction in session
        if 'interactions' not in session:
            session['interactions'] = []
        session['interactions'].append(response)

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-price', methods=['GET'])
def extract_price():
    try:
        url = request.args.get('url')
        param = request.args.get('param')
        descr_param = request.args.get('descr_param')
        stock_param = request.args.get('stock_param')
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Validate URL
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return jsonify({'error': 'Invalid URL format'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid URL'}), 400


        # Extract price
        if not param:
            price, title, description, stock = extractor.extract_prices(url)
        elif param and not descr_param:
            if (stock_param):
                price, title, description, stock = extractor.extract_prices(url, param, stock_param)
            else:
                price, title, description, stock = extractor.extract_prices(url, param)
        else:
            if (stock_param):
                price, title, description, stock = extractor.extract_prices(url, param, descr_param, stock_param)
            else:
                price, title, description, stock = extractor.extract_prices(url, param, descr_param)

        if not price:
            return jsonify({'error': 'No price found'}), 404

        # Save interaction in session
        if 'interactions' not in session:
            session['interactions'] = []
# Before saving to session, ensure data is serializable
        session['interactions'].append({
            'url': url,
            'title': str(title) if title else '',
            'price': str(price) if price else ''
        })
        return jsonify({
            'success': True,
            'title': title,
            'price': price.replace("TTC", ""),
            'description': description,
            'descr_param': descr_param,
            'stock': stock,
            'url': url
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/interactions', methods=['GET'])
def get_interactions():
    return jsonify(session.get('interactions', []))

@app.route('/api/compare', methods=['GET'])
def compare():
    try:
        host = request.args.get('host')
        user = request.args.get('user')
        password = request.args.get('passwd')
        database = request.args.get('database')
        id_target = request.args.get('id_target')
        database_prefix = request.args.get('database_prefix')

        result = compare_product(host, user, password, database, id_target, database_prefix)
        return jsonify({'success': True, 'result': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
from flask import Flask, jsonify, request
from price import DOMPriceExtractor
from urllib.parse import urlparse

app = Flask(__name__)
extractor = DOMPriceExtractor()

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

        # Extract price
        price = extractor.extract_prices(url)

        if not price:
            return jsonify({'error': 'No price found'}), 404

        return jsonify({
            'success': True,
            'price': price,
            'url': url
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
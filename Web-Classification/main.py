import requests
from bs4 import BeautifulSoup
import torch
from transformers import BertForSequenceClassification, BertTokenizerFast
import pickle
from flask import Flask, request, jsonify
# Function to fetch and clean the content of a website
with open('label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

app = Flask(__name__)

model = BertForSequenceClassification.from_pretrained('website_classifier_model')
tokenizer = BertTokenizerFast.from_pretrained('website_classifier_tokenizer')

def fetch_content(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'lxml')
    for tag in soup(['script', 'style', 'noscript', 'iframe', 'meta', 'link', 'comment', 'footer']):
        tag.decompose()
    return soup.get_text(separator=' ', strip=True)


@app.route('/', methods=['GET'])
def predict():
    test_url = request.args.get('url')
    content = fetch_content(test_url)

    tokenized_content = tokenizer(content, padding=True, truncation=True, return_tensors='pt')
    model.eval()
    with torch.no_grad():
        outputs = model(**tokenized_content)
        predictions = torch.argmax(outputs.logits, dim=-1)

    predicted_label = label_encoder.inverse_transform(predictions.numpy())[0]
    return jsonify({'predicted_label': predicted_label})

if __name__ == '__main__':
    app.run(debug=True)
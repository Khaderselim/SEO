import cloudscraper
from bs4 import BeautifulSoup
import torch
from transformers import BertForSequenceClassification, BertTokenizerFast
import pickle
from flask import Flask, request, jsonify
import nltk
from nltk.stem import SnowballStemmer
import spacy
from nltk.corpus import stopwords
nltk.download('stopwords')
french_stopwords = set(stopwords.words('french'))
english_stopwords = set(stopwords.words('english'))
stemmer = SnowballStemmer(language='french')
french_stopwords.update(["ajout", "pani", "tous", "recherche", "achet", "tnd","wishlist", "span","euro"])
english_stopwords.update(["add", "pani", "all", "search", "buy", "tnd","wishlist"])
nlp = spacy.load("fr_core_news_lg")
# Function to fetch and clean the content of a website
with open('label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

app = Flask(__name__)

model = BertForSequenceClassification.from_pretrained('website_classifier_model')
tokenizer = BertTokenizerFast.from_pretrained('website_classifier_tokenizer')
scraper = cloudscraper.create_scraper()
def fetch_content(url):
    try:
        r = scraper.get(url, timeout=10)
        soup = BeautifulSoup(r.content, 'lxml')
        metas = soup.find_all("meta")
        description = (" ".join([meta["content"] if "description" in str(meta) else "" for meta in metas])).strip()
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'link', 'comment', 'footer', 'header','meta','span']):
            tag.decompose()
        combined_text = soup.get_text(separator=' ', strip=True)
        filtered_words = [word for word in combined_text.split() if word.lower() not in french_stopwords and word.lower() not in english_stopwords]
        stemmed_words = {stemmer.stem(word) for word in filtered_words}  # Use a set to remove duplicates
        doc = nlp(" ".join(stemmed_words).strip()+" "+description)
        return (" ".join([token.lemma_ for token in doc if not token.is_stop])).strip()
    except Exception as e:
        return



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
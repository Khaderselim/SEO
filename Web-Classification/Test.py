import requests
from bs4 import BeautifulSoup
import torch
from transformers import BertForSequenceClassification, BertTokenizerFast
import pickle
# Function to fetch and clean the content of a website
def fetch_content(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'lxml')
    for tag in soup(['script', 'style', 'noscript', 'iframe', 'meta', 'link', 'comment', 'footer']):
        tag.decompose()
    return soup.get_text(separator=' ', strip=True)

# URL of the website to test
test_url = 'https://www.monoprix.tn/'

# Fetch and preprocess the content
content = fetch_content(test_url)

# Load the trained model and tokenizer
model = BertForSequenceClassification.from_pretrained('website_classifier_model')
tokenizer = BertTokenizerFast.from_pretrained('website_classifier_tokenizer')

# Tokenize and encode the content
tokenized_content = tokenizer(content, padding=True, truncation=True, return_tensors='pt')

# Make a prediction
model.eval()
with torch.no_grad():
    outputs = model(**tokenized_content)
    predictions = torch.argmax(outputs.logits, dim=-1)
with open('label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)
# Decode the prediction
predicted_label = label_encoder.inverse_transform(predictions.numpy())[0]
print(f'The predicted label for the website is: {predicted_label}')
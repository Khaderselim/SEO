import pandas as pd
import requests
from bs4 import BeautifulSoup
from transformers import BertTokenizerFast
from sklearn.preprocessing import LabelEncoder
import torch
from torch.utils.data import Dataset
import pickle
# Read the CSV file
df = pd.read_csv('cleaned_results.csv')

# Example dataset
data = {
    'url': df['URL'].tolist(),
    'label': df['Classification'].tolist()
}

# Fetch and clean the content of the websites
def fetch_content(url):
    try:
        r = requests.get(url, verify=True)
        soup = BeautifulSoup(r.content, 'lxml')
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'meta', 'link', 'comment', 'footer']):
            tag.decompose()
        return soup.get_text(separator=' ', strip=True)
    except:
        print(f"Failed to fetch content from {url}")
        return ""

df = pd.DataFrame(data)
df['content'] = df['url'].apply(fetch_content)

# Filter out rows with empty content
df = df[df['content'].str.strip().astype(bool)]

# Tokenize and Encode Data
tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased')
tokenized_data = tokenizer(df['content'].tolist(), padding=True, truncation=True, return_tensors='pt')

# Encode labels
label_encoder = LabelEncoder()
encoded_labels = label_encoder.fit_transform(df['label'])
encoded_labels = torch.tensor(encoded_labels, dtype=torch.long)  # Convert to torch.LongTensor
with open('label_encoder.pkl', 'wb') as f:
    pickle.dump(label_encoder, f)
# Define the Model
from transformers import BertForSequenceClassification, Trainer, TrainingArguments

model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=len(label_encoder.classes_))

# Train the Model
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=100,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
)

class WebsiteDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: val[idx] for key, val in self.encodings.items()}
        item['labels'] = self.labels[idx]
        return item

    def __len__(self):
        return len(self.labels)

dataset = WebsiteDataset(tokenized_data, encoded_labels)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

trainer.train()

# Save the Model
model.save_pretrained('website_classifier_model')
tokenizer.save_pretrained('website_classifier_tokenizer')

# Step 7: Load the Model
from transformers import BertForSequenceClassification, BertTokenizerFast
# Step 1: Prepare the Test Data
test_data = {
    'url': ['https://www.scoop.com.tn/', 'https://parapharmacieplus.tn/','https://isetn.rnu.tn/', 'https://www.tunisianet.com.tn/','https://www.zanimax.tn','https://animalzone.tn','https://www.monoprix.tn','https://mg.tn'],
    'label': ['Informatique', 'Parapharmacie', 'Université', 'Informatique', 'Animal', 'Animal', 'Supermarché', 'Supermarché']
}

df_test = pd.DataFrame(test_data)
df_test['content'] = df_test['url'].apply(fetch_content)

# Step 2: Tokenize and Encode Test Data
tokenized_test_data = tokenizer(df_test['content'].tolist(), padding=True, truncation=True, return_tensors='pt')

encoded_test_labels = label_encoder.transform(df_test['label'])
encoded_test_labels = torch.tensor(encoded_test_labels, dtype=torch.long)

# Step 3: Load the Trained Model
model = BertForSequenceClassification.from_pretrained('website_classifier_model')
tokenizer = BertTokenizerFast.from_pretrained('website_classifier_tokenizer')

# Step 4: Evaluate the Model
test_dataset = WebsiteDataset(tokenized_test_data, encoded_test_labels)

trainer = Trainer(
    model=model,
    args=training_args,
    eval_dataset=test_dataset,
)

# Evaluate the model
results = trainer.evaluate()
print(results)
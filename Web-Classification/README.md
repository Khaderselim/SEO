
# Web-Classification

## Project Overview
This project uses a BERT model to classify websites based on their content. The model is trained to categorize the content of websites into various predefined labels.

## Installation Instructions
1. Clone the repository:
```bash
git clone https://github.com/Khaderselim/SEO.git
cd SEO/Web-Classification
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Project Details
The project leverages the BERT model for sequence classification. The steps involved in the process include:

1. Fetching and cleaning website content.
2. Tokenizing and encoding the content using BERT tokenizer.
3. Training the BERT model on the encoded data.
4. Saving the trained model and tokenizer for future use.

The main scripts involved are:
- `Train.py`: Script to train the BERT model.
- `main.py`: Script to load the model and make predictions using a Flask API.
- `Test.py`: Script to test the model on a sample website.

For more details, please refer to the individual scripts in the `Web-Classification` folder.

You can view the repository contents [here](https://github.com/Khaderselim/SEO/tree/main/Web-Classification).
```

You can create a new file named `README.md` in the `Web-Classification` folder and add the above content to it.

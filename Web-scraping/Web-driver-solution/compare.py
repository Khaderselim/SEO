import re
import mysql.connector
import pandas as pd  # Import pandas
from sentence_transformers import SentenceTransformer  # Import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity  # Import cosine_similarity
import numpy as np  # Import numpy
import os
def compare_product(host , user , passwd , database , id_target, database_prefix):
    db = mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', host),
        user=os.environ.get(user),
        password=os.environ.get(passwd),
        database=os.environ.get('MYSQL_DATABASE', database))
    cursor = db.cursor()

    # Retrieve target products
    cursor.execute("SELECT * FROM "+database_prefix+"target_product WHERE id_target = %s", (id_target,))
    products = cursor.fetchall()

    # Convert to pandas DataFrame
    df = pd.DataFrame(products, columns=[i[0] for i in cursor.description])

    # Check if target products exist
    if df.empty:
        print(f"No target products found for id_target: {id_target}")
        return

    # Retrieve price history
    cursor.execute("select p.* , c.id_target from "+database_prefix+"price_history p LEFT JOIN "+database_prefix+"competitor_target c on p.id_competitor = c.id_competitor WHERE c.id_target = %s", (id_target,))
    product = cursor.fetchall()
    dfs = pd.DataFrame(product, columns=[i[0] for i in cursor.description])

    # Check if price history exists
    if dfs.empty:
        print(f"No price history found for id_target: {id_target}")
        return

    # Initialize the SentenceTransformer model
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    # Embed the product names, descriptions, and prices for df
    df['name_description_price'] = (
    df['name'].str.lower().apply(lambda x: re.sub(r'[^\w\s]', ' ', str(x))) + ' ' +
    df['name'].str.lower().apply(lambda x: re.sub(r'[^\w\s]', ' ', str(x))) + ' ' +
    df['name'].str.lower().apply(lambda x: re.sub(r'[^\w\s]', ' ', str(x))) + ' ' +
    df['description'].str.lower().apply(lambda x: re.sub(r'[^\w\s]', ' ', str(x))) + ' ' +
    df['price'].astype(str)
    )
    df_embeddings = model.encode(df['name_description_price'].tolist())

    # Embed the product names, descriptions, and prices for dfs
    dfs['name_description_price'] = (
    dfs['product_title'].str.lower().apply(lambda x: re.sub(r'[^\w\s]', ' ', str(x))) + ' ' +
    dfs['product_title'].str.lower().apply(lambda x: re.sub(r'[^\w\s]', ' ', str(x))) + ' ' +
    dfs['product_title'].str.lower().apply(lambda x: re.sub(r'[^\w\s]', ' ', str(x))) + ' ' +
    dfs['product_description'].str.lower().apply(lambda x: re.sub(r'[^\w\s]', ' ', str(x))) + ' ' +
    dfs['price_raw'].astype(str)
    )
    dfs_embeddings = model.encode(dfs['name_description_price'].tolist())

    # Calculate cosine similarity between the embeddings of df and dfs
    similarities = cosine_similarity(df_embeddings, dfs_embeddings)

    # Add the similarity scores to the DataFrame
    dfs['similarity'] = similarities.max(axis=0)

    # Find the most similar product for each product in df
    most_similar_indices = similarities.argmax(axis=0)

    # Ensure no two products share the same most similar product
    assigned_indices = set()
    for i in range(len(most_similar_indices)):
        if most_similar_indices[i] in assigned_indices:
            sorted_similarities = np.argsort(-similarities[:, i])
            for idx in sorted_similarities:
                if idx not in assigned_indices:
                    most_similar_indices[i] = idx
                    assigned_indices.add(idx)
                    break
        else:
            assigned_indices.add(most_similar_indices[i])

    x = pd.DataFrame({
        'most_similar_product_id': df['id_product'].iloc[most_similar_indices].values,
        'most_similar_history_id': dfs['id_history'].values,
        'product_name': df['name'].iloc[most_similar_indices].values,
        'history_name': dfs['product_title'].values,
        'product_price': df['price'].iloc[most_similar_indices].values,
        'history_price': dfs['price_raw'].values,
        'product_url': df['url'].iloc[most_similar_indices].values,
        'history_url': dfs['product_url'].values,
        'similarity': similarities.max(axis=0)
    })
    # Save most_similar_product_id and most_similar_history_id in the table "+database_prefix+"product_history_relation
    for index, row in x.iterrows():
        cursor.execute("""
            INSERT INTO """+database_prefix+"""product_history_relation (id_product, id_history)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
            id_product = VALUES(id_product)
        """, (int(row['most_similar_product_id']), int(row['most_similar_history_id'])))
    db.commit()



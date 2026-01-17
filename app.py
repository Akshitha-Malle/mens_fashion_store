from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Load Data
df = pd.read_csv("data/styles.csv", on_bad_lines='skip')
df = df[df['gender'] == 'Men'].head(50) # Start with 50 items

@app.route('/')
def home():
    # Convert dataframe to a list of dictionaries for HTML
    products = df.to_dict(orient='records')
    return render_template('index.html', products=products)

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    results = df[df['productDisplayName'].str.contains(query, case=False, na=False)]
    return jsonify(results.to_dict(orient='records'))
from flask import send_from_directory

@app.route('/data/images/<path:filename>')
def custom_static(filename):
    return send_from_directory('data/images', filename)
@app.route('/category/<cat_name>')
def category_page(cat_name):
    # Filter products where articleType matches the category clicked
    filtered_products = df[df['articleType'] == cat_name].to_dict(orient='records')
    return render_template('category.html', products=filtered_products, category=cat_name)
from recommender import get_recommendations

@app.route('/product/<int:product_id>')
def product_details(product_id):
    # Fetch product
    product_data = df[df['id'] == product_id].to_dict(orient='records')
    if not product_data:
        return "Product Not Found", 404
        
    # Get similar items based on current product tags
    related_items = get_recommendations(product_id, df).head(4).to_dict(orient='records')
    
    return render_template('product.html', product=product_data[0], related=related_items)
@app.route('/product/<int:product_id>')
def product_details(product_id):
    # Find the specific product
    product_data = df[df['id'] == product_id].to_dict(orient='records')
    if not product_data:
        return "Product Not Found", 404
    
    product = product_data[0]
    
    # Get similar items for the "You Might Also Like" section
    from recommender import get_recommendations
    related_df = get_recommendations(product_id, df)
    related = related_df.head(4).to_dict(orient='records') if not related_df.empty else []
    
    return render_template('product.html', product=product, related=related)
if __name__ == '__main__':
    app.run(debug=True)
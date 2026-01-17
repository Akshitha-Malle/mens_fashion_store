from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import os
import random  # Added for fallback discovery
from recommender import get_content_recommendations

app = FastAPI(title="Vogue Vedic Industry Backend")

# Mount static folder (ensure your images are in data/images/)
app.mount("/static", StaticFiles(directory="data"), name="static")

templates = Jinja2Templates(directory="templates")

# Load and clean data
df = pd.read_csv("data/styles.csv", on_bad_lines='skip')
df['id'] = df['id'].astype(str)

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/category/{cat_name}", response_class=HTMLResponse)
async def category_page(request: Request, cat_name: str, sort: str = Query("default")):
    search_term = cat_name.lower().replace(" ", "").replace("-", "")
    mask = df['articleType'].str.lower().str.replace(" ", "").str.replace("-", "").str.contains(search_term, na=False)
    filtered = df[mask].copy()
    
    filtered['price'] = filtered['id'].astype(int) % 500 + 499
    
    if sort == "low":
        filtered = filtered.sort_values(by='price', ascending=True)
    elif sort == "high":
        filtered = filtered.sort_values(by='price', ascending=False)
        
    products_list = filtered.head(40).to_dict(orient='records')
    
    return templates.TemplateResponse("category.html", {
        "request": request, 
        "category": cat_name, 
        "products": products_list,
        "current_sort": sort
    })

@app.get("/product/{product_id}", response_class=HTMLResponse)
async def product_page(request: Request, product_id: str):
    product_data = df[df['id'] == product_id].to_dict(orient='records')
    if not product_data:
        return HTMLResponse(content="Product Not Found", status_code=404)
    
    # 2. Situational Recommendation Algorithm
    similar_products = get_content_recommendations(product_id, df)
    
    # Fallback: If recommender is empty, grab 4 random items
    if not similar_products:
        discovery_items = df.sample(4).to_dict(orient='records')
    else:
        discovery_items = similar_products[:4]
    
    return templates.TemplateResponse("product.html", {
        "request": request, 
        "product": product_data[0], 
        "discovery": discovery_items # Variable name matched to product.html
    })

@app.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request):
    return templates.TemplateResponse("cart.html", {"request": request})

@app.get("/search", response_class=HTMLResponse)
async def search_products(request: Request, q: str = Query("")):
    query = q.lower()
    mask = (
        df['productDisplayName'].str.lower().str.contains(query, na=False) |
        df['articleType'].str.lower().str.contains(query, na=False) |
        df['baseColour'].str.lower().str.contains(query, na=False)
    )
    results = df[mask].head(40).to_dict(orient='records')
    return templates.TemplateResponse("category.html", {
        "request": request,
        "category": f"Results for '{q}'",
        "products": results,
        "current_sort": "default"
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
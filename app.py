import os
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER_PACKING = 'Packing'
UPLOAD_FOLDER_PRODUCT = 'Product'
app.config['UPLOAD_FOLDER_PACKING'] = UPLOAD_FOLDER_PACKING
app.config['UPLOAD_FOLDER_PRODUCT'] = UPLOAD_FOLDER_PRODUCT

# Ensure upload folders exist
os.makedirs(UPLOAD_FOLDER_PACKING, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_PRODUCT, exist_ok=True)

df = pd.read_csv("all_gem_sku.csv")
df = df[['internal_id', 'SKU', 'old_SKU', 'sort','color', 'size']]

def check_photo_exists(folder, filename):
    return os.path.isfile(os.path.join(folder, f'{filename}.jpeg'))

@app.route('/')
def index():
    # Check for existing photos and update DataFrame
    df['Packing Photo'] = df['internal_id'].apply(lambda x: check_photo_exists(UPLOAD_FOLDER_PACKING, x))
    df['Product Photo'] = df['internal_id'].apply(lambda x: check_photo_exists(UPLOAD_FOLDER_PRODUCT, x))

    # Filter out rows where both photos exist
    filtered_df = df[~(df['Packing Photo'] & df['Product Photo'])]

    # Define a function to sort by SKU prefix
    def sort_sku(sku):
        if sku.startswith('faceted-'):
            prefix_order = 0
        elif sku.startswith('cab-'):
            prefix_order = 1
        elif sku.startswith('orb-'):
            prefix_order = 2
        else:
            prefix_order = 3
        return prefix_order

    # Apply sorting
    filtered_df['prefix_order'] = filtered_df['SKU'].apply(sort_sku)

    # Ensure 'sort', 'color', 'size' columns exist and are of appropriate types for sorting
    filtered_df['sort'] = filtered_df['sort'].astype(str)
    filtered_df['color'] = filtered_df['color'].astype(str)
    filtered_df['size'] = filtered_df['size'].astype(str)

    # Sort by prefix_order, 'sort', 'color', and 'size'
    sorted_df = filtered_df.sort_values(by=['prefix_order', 'sort', 'color', 'size']).drop(columns='prefix_order')

    return render_template('index.html', tables=sorted_df.to_dict(orient='records'))

@app.route('/upload/<photo_type>/<int:internal_id>', methods=['POST'])
def upload_file(photo_type, internal_id):
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        if photo_type == 'packing':
            file.save(os.path.join(app.config['UPLOAD_FOLDER_PACKING'], f'{internal_id}.jpeg'))
        elif photo_type == 'product':
            file.save(os.path.join(app.config['UPLOAD_FOLDER_PRODUCT'], f'{internal_id}.jpeg'))
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5025)

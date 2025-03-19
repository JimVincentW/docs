import requests
from pprint import pprint
from requests.auth import HTTPBasicAuth
import os

# 🔹 CONFIGURE THESE SETTINGS
NEXTCLOUD_URL = "https://cloud.open-politics.org"
USERNAME = "Jim"
PASSWORD = "KXrKS-GxE5i-Lrtzx-RtgbS-3Xyz3"

# What you want to fetch
TABLE_NAME = "Documentation"
COLUMNS_TO_FETCH = ["Title", "Content", "Category"]

def api_request(endpoint, auth=True):
    """Make a request to the Nextcloud Tables API"""
    headers = {"OCS-APIRequest": "true"}
    url = f"{NEXTCLOUD_URL}/index.php/apps/tables/api/1/{endpoint}"
    
    try:
        if auth:
            response = requests.get(url, headers=headers, auth=HTTPBasicAuth(USERNAME, PASSWORD))
        else:
            response = requests.get(url, headers=headers)
        
        return response.json()
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return None

def fetch_table_data():
    """Main function to fetch and display table data"""
    # Get all tables
    tables = api_request("tables")
    if not tables:
        print("❌ Failed to retrieve tables")
        return
    
    # Find our target table
    target_table = next((table for table in tables if table["title"] == TABLE_NAME), None)
    if not target_table:
        print(f"❌ Table '{TABLE_NAME}' not found. Available tables:")
        for table in tables:
            print(f"  • {table['title']}")
        return
    
    table_id = target_table["id"]
    print(f"📊 Found table: {TABLE_NAME} (ID: {table_id})")
    
    # Get column information
    columns_info = api_request(f"tables/{table_id}/columns")
    if not columns_info:
        print("❌ Failed to retrieve column information")
        return
    
    # Create column ID to name mapping
    column_map = {col["id"]: col["title"] for col in columns_info 
                 if isinstance(col, dict) and "id" in col and "title" in col}
    
    # Get table data
    table_data = api_request(f"tables/{table_id}/rows")
    if not table_data:
        print("❌ Failed to retrieve table data")
        return
    
    # Display the data for requested columns
    print(f"\n📋 Data for {TABLE_NAME}:")
    print(f"   Columns: {', '.join(COLUMNS_TO_FETCH)}")
    print("─" * 50)
    
    # Create snippets directory if it doesn't exist
    snippets_dir = "snippets"
    os.makedirs(snippets_dir, exist_ok=True)
    
    for row in table_data:
        filtered_row = {}
        for cell in row["data"]:
            col_name = column_map.get(cell["columnId"])
            if col_name in COLUMNS_TO_FETCH:
                filtered_row[col_name] = cell["value"]
        
        if filtered_row:  # Only process rows that have data in our desired columns
            pprint(filtered_row)
            
            # Create a slug from category and title
            title = filtered_row.get("Title", "")
            category = filtered_row.get("Category", "")
            
            title_slug = slugify(title)
            category_slug = slugify(category)
            
            # Combine category and title for the slug
            if category_slug and title_slug:
                slug = f"{category_slug}-{title_slug}"
            elif title_slug:
                slug = title_slug
            elif category_slug:
                slug = category_slug
            else:
                print(f"⚠️ Skipping entry with empty title and category: {filtered_row}")
                continue
                
            # Write content to file
            content = filtered_row.get("Content", "")
            filename = f"{snippets_dir}/{slug}.mdx"
            
            with open(filename, "w") as f:
                f.write(content)
            
            print(f"✅ Wrote snippet to {filename}")

def slugify(text):
    """Convert text to slug format (lowercase, hyphens instead of spaces)"""
    import re
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().replace(" ", "-")
    # Remove any characters that aren't alphanumeric or hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug

if __name__ == "__main__":
    fetch_table_data()



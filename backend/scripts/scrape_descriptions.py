"""
Script pour récupérer les descriptions techniques des produits TUS
Extrait les descriptions depuis les meta tags et le contenu de la page
"""
import asyncio
import aiohttp
import os
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv('/app/backend/.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

BASE_URL = "https://tus.com.tn"

stats = {
    "total": 0,
    "updated": 0,
    "no_description": 0,
    "failed": 0,
    "skipped": 0
}


async def fetch_page(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch page HTML"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        }
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                return await response.text()
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
    return None


def extract_description(html: str) -> dict:
    """Extract description from product page HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    result = {
        "meta_description": None,
        "full_description": None,
        "specs": []
    }
    
    # 1. Get meta description (usually contains specs summary)
    meta_desc = soup.select_one('meta[name="description"]')
    if meta_desc:
        content = meta_desc.get('content', '').strip()
        if content and len(content) > 20:
            result["meta_description"] = content
    
    # 2. Get og:description
    og_desc = soup.select_one('meta[property="og:description"]')
    if og_desc:
        content = og_desc.get('content', '').strip()
        if content and len(content) > 20:
            if not result["meta_description"] or len(content) > len(result["meta_description"]):
                result["meta_description"] = content
    
    # 3. Get product description from WooCommerce tab
    desc_tab = soup.select_one('#tab-description')
    if desc_tab:
        # Get text content, clean up
        text = desc_tab.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 50:
            result["full_description"] = text
    
    # 4. Get product short description
    short_desc = soup.select_one('.woocommerce-product-details__short-description')
    if short_desc:
        text = short_desc.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 30 and (not result["full_description"] or len(text) > len(result["full_description"])):
            result["full_description"] = text
    
    # 5. Extract specs from tables or lists
    spec_tables = soup.select('.woocommerce-product-attributes, .shop_attributes, table.specs')
    for table in spec_tables:
        rows = table.select('tr')
        for row in rows:
            label = row.select_one('th, td:first-child')
            value = row.select_one('td:last-child')
            if label and value:
                spec_name = label.get_text(strip=True)
                spec_value = value.get_text(strip=True)
                if spec_name and spec_value:
                    result["specs"].append({"name": spec_name, "value": spec_value})
    
    # 6. Look for any structured specs in the content
    content_div = soup.select_one('.entry-content, .product-content, .product-description')
    if content_div:
        # Extract text
        text = content_div.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 100 and not result["full_description"]:
            result["full_description"] = text[:2000]  # Limit to 2000 chars
    
    return result


async def process_product(session: aiohttp.ClientSession, db, product: dict) -> bool:
    """Process a single product: fetch page, extract description, update DB"""
    product_id = product.get('id')
    source_url = product.get('source_url')
    current_desc = product.get('description', '') or ''
    
    if not source_url:
        stats["failed"] += 1
        return False
    
    # Skip if already has good description
    if len(current_desc) >= 200:
        stats["skipped"] += 1
        return True
    
    # Fetch product page
    html = await fetch_page(session, source_url)
    if not html:
        stats["failed"] += 1
        return False
    
    # Extract description
    desc_data = extract_description(html)
    
    # Choose best description
    new_description = None
    if desc_data["full_description"] and len(desc_data["full_description"]) > len(current_desc):
        new_description = desc_data["full_description"]
    elif desc_data["meta_description"] and len(desc_data["meta_description"]) > len(current_desc):
        new_description = desc_data["meta_description"]
    
    if not new_description:
        stats["no_description"] += 1
        return False
    
    # Update database
    update_data = {
        "description": new_description,
        "description_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Add specs if found
    if desc_data["specs"]:
        update_data["specs_scraped"] = desc_data["specs"]
    
    db.products.update_one(
        {"id": product_id},
        {"$set": update_data}
    )
    
    stats["updated"] += 1
    return True


async def scrape_tus_descriptions(limit: int = None, min_desc_length: int = 50):
    """Main function to scrape TUS product descriptions"""
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Find TUS products with short descriptions
    products = list(db.products.find(
        {
            "fournisseur": "TUS",
            "source_url": {"$exists": True, "$ne": ""},
            "$expr": {"$lt": [{"$strLenCP": {"$ifNull": ["$description", ""]}}, min_desc_length]}
        },
        {"id": 1, "name": 1, "source_url": 1, "description": 1}
    ))
    
    if limit:
        products = products[:limit]
    
    stats["total"] = len(products)
    logger.info(f"🚀 Scraping descriptions for {len(products)} TUS products with short descriptions")
    
    connector = aiohttp.TCPConnector(limit=5, limit_per_host=3)
    async with aiohttp.ClientSession(connector=connector) as session:
        for i, product in enumerate(products):
            await process_product(session, db, product)
            
            if (i + 1) % 20 == 0:
                progress = ((i + 1) / len(products)) * 100
                logger.info(f"📊 Progress: {i + 1}/{len(products)} ({progress:.1f}%) - ✅ {stats['updated']} | 🔍 {stats['no_description']} | ❌ {stats['failed']}")
            
            # Rate limiting
            await asyncio.sleep(0.3)
    
    client.close()
    
    logger.info("=" * 50)
    logger.info("📈 RÉSUMÉ SCRAPE DESCRIPTIONS TUS")
    logger.info(f"   Total traités: {stats['total']}")
    logger.info(f"   ✅ Mis à jour: {stats['updated']}")
    logger.info(f"   🔍 Pas de description trouvée: {stats['no_description']}")
    logger.info(f"   ⏭️ Déjà OK: {stats['skipped']}")
    logger.info(f"   ❌ Échecs: {stats['failed']}")
    logger.info("=" * 50)
    
    return stats


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(scrape_tus_descriptions(limit=limit))

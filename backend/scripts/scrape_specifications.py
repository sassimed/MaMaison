"""
Script pour récupérer les spécifications techniques complètes des produits TUS
Extrait les tableaux de specs et les stocke de manière structurée
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
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv('/app/backend/.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

stats = {
    "total": 0,
    "updated": 0,
    "no_specs": 0,
    "failed": 0
}


async def fetch_page(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch page HTML"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        }
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                return await response.text()
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
    return None


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove email obfuscation
    text = re.sub(r'\[email[^\]]*\]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_specifications(html: str) -> dict:
    """Extract structured specifications from product page"""
    soup = BeautifulSoup(html, 'html.parser')
    
    result = {
        "specs_sections": [],  # [{name: "Camera", specs: [{key, value}, ...]}, ...]
        "specs_flat": {},      # {key: value, ...} for easy search
        "meta_description": None,
        "full_description": None
    }
    
    # Get meta description
    meta_desc = soup.select_one('meta[name="description"]')
    if meta_desc:
        result["meta_description"] = clean_text(meta_desc.get('content', ''))
    
    # Find the specs table in tab-description
    desc_tab = soup.select_one('#tab-description table')
    if not desc_tab:
        # Try alternate selectors
        desc_tab = soup.select_one('.woocommerce-Tabs-panel--description table')
    
    if desc_tab:
        current_section = None
        current_specs = []
        
        for row in desc_tab.select('tr'):
            cells = row.select('td')
            
            if len(cells) == 1:
                # This is a section header (like "Camera", "Lens", etc.)
                # Save previous section if exists
                if current_section and current_specs:
                    result["specs_sections"].append({
                        "name": current_section,
                        "specs": current_specs
                    })
                
                current_section = clean_text(cells[0].get_text())
                current_specs = []
                
            elif len(cells) >= 2:
                # This is a key-value pair
                key = clean_text(cells[0].get_text())
                value = clean_text(cells[-1].get_text())
                
                if key and value and key != value:
                    current_specs.append({"key": key, "value": value})
                    result["specs_flat"][key] = value
        
        # Don't forget last section
        if current_section and current_specs:
            result["specs_sections"].append({
                "name": current_section,
                "specs": current_specs
            })
    
    # Also get from additional_information tab
    additional_tab = soup.select_one('.woocommerce-product-attributes')
    if additional_tab:
        for row in additional_tab.select('tr'):
            th = row.select_one('th')
            td = row.select_one('td')
            if th and td:
                key = clean_text(th.get_text())
                value = clean_text(td.get_text())
                if key and value:
                    result["specs_flat"][key] = value
    
    # Build full description from specs
    if result["specs_sections"]:
        desc_parts = []
        for section in result["specs_sections"][:3]:  # First 3 sections
            for spec in section["specs"][:5]:  # First 5 specs per section
                desc_parts.append(f"{spec['key']}: {spec['value']}")
        result["full_description"] = ". ".join(desc_parts)
    
    return result


async def process_product(session: aiohttp.ClientSession, db, product: dict) -> bool:
    """Process a single product"""
    product_id = product.get('id')
    source_url = product.get('source_url')
    
    if not source_url:
        stats["failed"] += 1
        return False
    
    # Fetch product page
    html = await fetch_page(session, source_url)
    if not html:
        stats["failed"] += 1
        return False
    
    # Extract specifications
    spec_data = extract_specifications(html)
    
    if not spec_data["specs_sections"] and not spec_data["specs_flat"]:
        stats["no_specs"] += 1
        return False
    
    # Prepare update
    update_data = {
        "specifications_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if spec_data["specs_sections"]:
        update_data["specifications"] = spec_data["specs_sections"]
    
    if spec_data["specs_flat"]:
        update_data["specs"] = spec_data["specs_flat"]
    
    # Update description if current is short
    current_desc = product.get('description', '') or ''
    if spec_data["full_description"] and len(spec_data["full_description"]) > len(current_desc):
        update_data["description"] = spec_data["full_description"]
    elif spec_data["meta_description"] and len(spec_data["meta_description"]) > len(current_desc):
        update_data["description"] = spec_data["meta_description"]
    
    # Update database
    db.products.update_one(
        {"id": product_id},
        {"$set": update_data}
    )
    
    stats["updated"] += 1
    return True


async def scrape_tus_specifications(limit: int = None):
    """Main function to scrape TUS product specifications"""
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Find TUS products with source URLs
    query = {
        "fournisseur": "TUS",
        "source_url": {"$exists": True, "$ne": ""}
    }
    
    # Skip products that already have specifications
    # query["specifications"] = {"$exists": False}
    
    products = list(db.products.find(query, {
        "id": 1, "name": 1, "source_url": 1, "description": 1
    }))
    
    if limit:
        products = products[:limit]
    
    stats["total"] = len(products)
    logger.info(f"🚀 Scraping specifications for {len(products)} TUS products")
    
    connector = aiohttp.TCPConnector(limit=5, limit_per_host=3)
    async with aiohttp.ClientSession(connector=connector) as session:
        for i, product in enumerate(products):
            await process_product(session, db, product)
            
            if (i + 1) % 20 == 0:
                progress = ((i + 1) / len(products)) * 100
                logger.info(f"📊 Progress: {i + 1}/{len(products)} ({progress:.1f}%) - ✅ {stats['updated']} | 🔍 {stats['no_specs']} | ❌ {stats['failed']}")
            
            # Rate limiting
            await asyncio.sleep(0.3)
    
    client.close()
    
    logger.info("=" * 50)
    logger.info("📈 RÉSUMÉ SCRAPE SPECIFICATIONS TUS")
    logger.info(f"   Total traités: {stats['total']}")
    logger.info(f"   ✅ Specs trouvées: {stats['updated']}")
    logger.info(f"   🔍 Pas de specs: {stats['no_specs']}")
    logger.info(f"   ❌ Échecs: {stats['failed']}")
    logger.info("=" * 50)
    
    return stats


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(scrape_tus_specifications(limit=limit))

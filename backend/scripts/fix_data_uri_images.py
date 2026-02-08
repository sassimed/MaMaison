"""
Script pour corriger les data URIs malformés et les convertir en fichiers images
"""
import os
import base64
import hashlib
from pathlib import Path
from pymongo import MongoClient
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
PRODUCTS_DIR = Path("/app/uploads/products")
PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)

def fix_data_uri_images():
    """Corrige les data URIs malformés et sauvegarde les images"""
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Find products with malformed data URIs
    query = {"primary_image_url": {"$regex": "data:image"}}
    products = list(db.products.find(query))
    
    print(f"🔍 Trouvé {len(products)} produits avec data URI à corriger")
    
    stats = {"success": 0, "failed": 0}
    
    for i, product in enumerate(products):
        try:
            product_id = product.get('id', str(product.get('_id', '')))
            url = product.get('primary_image_url', '')
            
            # Extract the actual data URI part
            # Format: https://tus.com.tndata:image/png;base64,XXXX
            # We need: data:image/png;base64,XXXX
            
            if 'data:image' in url:
                # Find where the data URI starts
                data_start = url.find('data:image')
                data_uri = url[data_start:]
                
                # Parse the data URI
                # Format: data:image/TYPE;base64,DATA
                if ';base64,' in data_uri:
                    header, b64_data = data_uri.split(';base64,', 1)
                    
                    # Determine extension
                    if 'png' in header:
                        ext = '.png'
                    elif 'jpeg' in header or 'jpg' in header:
                        ext = '.jpg'
                    elif 'gif' in header:
                        ext = '.gif'
                    elif 'webp' in header:
                        ext = '.webp'
                    else:
                        ext = '.png'  # default
                    
                    # Decode base64
                    try:
                        image_data = base64.b64decode(b64_data)
                        
                        if len(image_data) < 100:
                            print(f"  ⚠️ Image trop petite pour {product_id}")
                            stats["failed"] += 1
                            continue
                        
                        # Generate filename
                        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                        filename = f"{product_id}_{url_hash}{ext}"
                        file_path = PRODUCTS_DIR / filename
                        
                        # Save file
                        with open(file_path, 'wb') as f:
                            f.write(image_data)
                        
                        # Update database
                        local_url = f"/api/upload/products/{filename}"
                        db.products.update_one(
                            {"id": product_id},
                            {"$set": {
                                "primary_image_url": local_url,
                                "image_url": local_url,
                                "image": local_url,
                                "original_image_url": url[:200],  # Keep truncated original
                                "image_migrated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        
                        stats["success"] += 1
                        
                    except Exception as e:
                        print(f"  ❌ Erreur décodage base64 pour {product_id}: {e}")
                        stats["failed"] += 1
                else:
                    print(f"  ⚠️ Format data URI invalide pour {product_id}")
                    stats["failed"] += 1
            else:
                print(f"  ⚠️ Pas de data URI trouvé pour {product_id}")
                stats["failed"] += 1
                
        except Exception as e:
            print(f"  ❌ Erreur pour produit {product.get('id', 'unknown')}: {e}")
            stats["failed"] += 1
        
        # Progress
        if (i + 1) % 100 == 0:
            print(f"📊 Progression: {i + 1}/{len(products)} - ✅ {stats['success']} | ❌ {stats['failed']}")
    
    client.close()
    
    print("=" * 50)
    print("📈 RÉSUMÉ")
    print(f"   ✅ Succès: {stats['success']}")
    print(f"   ❌ Échecs: {stats['failed']}")
    print("=" * 50)
    
    return stats


if __name__ == "__main__":
    fix_data_uri_images()

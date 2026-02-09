#!/usr/bin/env python3
"""
Backend API Testing for MaMaison E-commerce Platform Migration
Tests the new universal product model with multi-source affiliation support
"""

import requests
import sys
import json
from datetime import datetime

class MaMaisonAPITester:
    def __init__(self, base_url="https://logement-app-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASS - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        if 'products' in response_data:
                            print(f"   Products count: {len(response_data['products'])}")
                        if 'total' in response_data:
                            print(f"   Total items: {response_data['total']}")
                        if 'items' in response_data:
                            print(f"   Items count: {len(response_data['items'])}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAIL - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text[:200]}")
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'url': url
                })
                return False, {}

        except Exception as e:
            print(f"❌ FAIL - Exception: {str(e)}")
            self.failed_tests.append({
                'name': name,
                'error': str(e),
                'url': url
            })
            return False, {}

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@mamaison.tn", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   ✅ Admin logged in successfully")
            return True
        return False

    def test_products_api_structure(self):
        """Test /api/products endpoint with new structure"""
        success, response = self.run_test(
            "Products API - New Structure",
            "GET",
            "products",
            200
        )
        
        if success and response:
            # Check for new structure fields
            products = response.get('products', response.get('items', []))
            if products:
                product = products[0]
                print(f"   Sample product structure:")
                
                # Check for new v3 fields
                new_fields = ['prices', 'specs', 'tags', 'scores', 'media', 'ai_data', 'meta']
                found_fields = []
                for field in new_fields:
                    if field in product:
                        found_fields.append(field)
                        print(f"   ✅ {field}: {type(product[field])}")
                
                # Check prices structure
                if 'prices' in product and product['prices']:
                    prices = product['prices']
                    print(f"   Prices structure: sources={len(prices.get('sources', []))}")
                
                # Check legacy compatibility
                legacy_fields = ['price', 'category', 'image_url', 'specifications']
                for field in legacy_fields:
                    if field in product:
                        print(f"   📋 Legacy {field}: ✓")
                
                return len(found_fields) > 0
        return False

    def test_products_pagination(self):
        """Test products pagination with limit=10"""
        success, response = self.run_test(
            "Products Pagination (limit=10)",
            "GET",
            "products?limit=10",
            200
        )
        
        if success and response:
            products = response.get('products', response.get('items', []))
            total = response.get('total', 0)
            print(f"   Retrieved {len(products)} products out of {total} total")
            return len(products) <= 10 and total > 0
        return False

    def test_products_search(self):
        """Test product search by name"""
        success, response = self.run_test(
            "Product Search by Name",
            "GET",
            "products?q=camera",
            200
        )
        
        if success and response:
            products = response.get('products', response.get('items', []))
            print(f"   Found {len(products)} products matching 'camera'")
            if products:
                # Check if results are relevant
                first_product = products[0]
                name = first_product.get('name', '').lower()
                category = first_product.get('category', '').lower()
                relevant = 'camera' in name or 'camera' in category or 'vidéo' in name
                print(f"   First result: {first_product.get('name', 'N/A')}")
                print(f"   Relevance: {'✅' if relevant else '❓'}")
                return True
        return False

    def test_product_detail(self):
        """Test individual product detail endpoint"""
        # First get a product ID
        success, response = self.run_test(
            "Get Product List for Detail Test",
            "GET",
            "products?limit=1",
            200
        )
        
        if success and response:
            products = response.get('products', response.get('items', []))
            if products:
                product_id = products[0].get('id')
                if product_id:
                    success, detail_response = self.run_test(
                        f"Product Detail ({product_id})",
                        "GET",
                        f"products/{product_id}",
                        200
                    )
                    
                    if success and detail_response:
                        print(f"   Product name: {detail_response.get('name', 'N/A')}")
                        print(f"   Has specifications: {'✅' if detail_response.get('specifications') else '❌'}")
                        print(f"   Has prices: {'✅' if detail_response.get('prices') else '❌'}")
                        return True
        return False

    def test_admin_dashboard_stats(self):
        """Test admin dashboard statistics"""
        if not self.token:
            print("❌ Skipping admin tests - not logged in")
            return False
            
        success, response = self.run_test(
            "Admin Dashboard Stats",
            "GET",
            "admin/dashboard/stats",
            200
        )
        
        if success and response:
            print(f"   Stats keys: {list(response.keys())}")
            if 'products_count' in response:
                print(f"   Products count: {response['products_count']}")
            return True
        return False

    def test_admin_products_management(self):
        """Test admin products management endpoint"""
        if not self.token:
            print("❌ Skipping admin tests - not logged in")
            return False
            
        success, response = self.run_test(
            "Admin Products Management",
            "GET",
            "admin/products-manage?limit=5",
            200
        )
        
        if success and response:
            items = response.get('items', [])
            total = response.get('total', 0)
            print(f"   Retrieved {len(items)} products for management")
            print(f"   Total products: {total}")
            
            # Check if we have the expected 2737 products
            if total == 2737:
                print(f"   ✅ Confirmed: 2737 products migrated successfully")
            else:
                print(f"   ⚠️  Expected 2737 products, found {total}")
            
            return total > 0
        return False

    def test_categories_api(self):
        """Test categories API"""
        success, response = self.run_test(
            "Categories API",
            "GET",
            "categories",
            200
        )
        
        if success and response:
            categories = response.get('categories', response if isinstance(response, list) else [])
            print(f"   Found {len(categories)} categories")
            if categories:
                sample_cat = categories[0]
                print(f"   Sample category: {sample_cat.get('label', sample_cat.get('name', 'N/A'))}")
            return len(categories) > 0
        return False

def main():
    print("🏠 MaMaison E-commerce Platform - Backend API Testing")
    print("=" * 60)
    
    tester = MaMaisonAPITester()
    
    # Test sequence
    print("\n📋 Testing Authentication...")
    tester.test_admin_login()
    
    print("\n📋 Testing Product APIs...")
    tester.test_products_api_structure()
    tester.test_products_pagination()
    tester.test_products_search()
    tester.test_product_detail()
    
    print("\n📋 Testing Categories...")
    tester.test_categories_api()
    
    print("\n📋 Testing Admin Features...")
    tester.test_admin_dashboard_stats()
    tester.test_admin_products_management()
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 TEST SUMMARY")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ FAILED TESTS ({len(tester.failed_tests)}):")
        for i, test in enumerate(tester.failed_tests, 1):
            print(f"  {i}. {test['name']}")
            if 'expected' in test:
                print(f"     Expected: {test['expected']}, Got: {test['actual']}")
            if 'error' in test:
                print(f"     Error: {test['error']}")
            print(f"     URL: {test['url']}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
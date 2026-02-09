"""
Tests de Performance et Charge - MyDar API
Utilise des requêtes concurrentes pour mesurer les performances
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict
import json

API_BASE_URL = "http://localhost:8001/api"


@dataclass
class RequestResult:
    """Résultat d'une requête"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error: str = None


@dataclass
class LoadTestResult:
    """Résultats agrégés d'un test de charge"""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    min_response_ms: float
    max_response_ms: float
    avg_response_ms: float
    median_response_ms: float
    p95_response_ms: float
    p99_response_ms: float
    requests_per_second: float
    total_time_seconds: float
    error_rate: float


class LoadTester:
    """Testeur de charge asynchrone"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.results: List[RequestResult] = []
    
    async def make_request(
        self, 
        session: aiohttp.ClientSession, 
        method: str, 
        endpoint: str,
        json_data: Dict = None
    ) -> RequestResult:
        """Effectue une requête et mesure le temps de réponse"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.perf_counter()
        
        try:
            if method.upper() == "GET":
                async with session.get(url) as response:
                    await response.text()
                    status_code = response.status
            elif method.upper() == "POST":
                async with session.post(url, json=json_data) as response:
                    await response.text()
                    status_code = response.status
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = (time.perf_counter() - start_time) * 1000
            success = 200 <= status_code < 400
            
            return RequestResult(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time,
                success=success
            )
        
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            return RequestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time_ms=response_time,
                success=False,
                error=str(e)
            )
    
    async def run_concurrent_requests(
        self,
        method: str,
        endpoint: str,
        num_requests: int,
        concurrency: int,
        json_data: Dict = None
    ) -> LoadTestResult:
        """Exécute des requêtes concurrentes"""
        results: List[RequestResult] = []
        
        connector = aiohttp.TCPConnector(limit=concurrency, limit_per_host=concurrency)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            start_time = time.perf_counter()
            
            # Create batches of concurrent requests
            for batch_start in range(0, num_requests, concurrency):
                batch_size = min(concurrency, num_requests - batch_start)
                tasks = [
                    self.make_request(session, method, endpoint, json_data)
                    for _ in range(batch_size)
                ]
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
            
            total_time = time.perf_counter() - start_time
        
        # Calculate statistics
        response_times = [r.response_time_ms for r in results]
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        sorted_times = sorted(response_times)
        
        return LoadTestResult(
            endpoint=endpoint,
            total_requests=len(results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            min_response_ms=min(response_times) if response_times else 0,
            max_response_ms=max(response_times) if response_times else 0,
            avg_response_ms=statistics.mean(response_times) if response_times else 0,
            median_response_ms=statistics.median(response_times) if response_times else 0,
            p95_response_ms=sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0,
            p99_response_ms=sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0,
            requests_per_second=len(results) / total_time if total_time > 0 else 0,
            total_time_seconds=total_time,
            error_rate=(len(failed) / len(results) * 100) if results else 0
        )


def print_result(result: LoadTestResult, title: str = ""):
    """Affiche les résultats formatés"""
    print(f"\n{'='*60}")
    print(f"  {title or result.endpoint}")
    print(f"{'='*60}")
    print(f"  Total Requests:     {result.total_requests}")
    print(f"  Successful:         {result.successful_requests} ({100 - result.error_rate:.1f}%)")
    print(f"  Failed:             {result.failed_requests} ({result.error_rate:.1f}%)")
    print(f"  {'─'*56}")
    print(f"  Min Response:       {result.min_response_ms:.2f} ms")
    print(f"  Max Response:       {result.max_response_ms:.2f} ms")
    print(f"  Avg Response:       {result.avg_response_ms:.2f} ms")
    print(f"  Median Response:    {result.median_response_ms:.2f} ms")
    print(f"  P95 Response:       {result.p95_response_ms:.2f} ms")
    print(f"  P99 Response:       {result.p99_response_ms:.2f} ms")
    print(f"  {'─'*56}")
    print(f"  Throughput:         {result.requests_per_second:.2f} req/s")
    print(f"  Total Time:         {result.total_time_seconds:.2f} s")
    print(f"{'='*60}")


async def run_load_tests():
    """Exécute la suite complète de tests de charge"""
    tester = LoadTester()
    results = []
    
    print("\n" + "🚀 " * 20)
    print("     TESTS DE PERFORMANCE ET CHARGE - MyDar API")
    print("🚀 " * 20)
    
    # Test configurations
    tests = [
        # Light load tests (100 requests, 10 concurrent)
        {"name": "🔹 Health Check (Light)", "method": "GET", "endpoint": "/health", "requests": 100, "concurrency": 10},
        {"name": "🔹 Categories List (Light)", "method": "GET", "endpoint": "/categories", "requests": 100, "concurrency": 10},
        {"name": "🔹 Products List (Light)", "method": "GET", "endpoint": "/products?limit=20", "requests": 100, "concurrency": 10},
        
        # Medium load tests (500 requests, 50 concurrent)
        {"name": "🔸 Products List (Medium)", "method": "GET", "endpoint": "/products?limit=20", "requests": 500, "concurrency": 50},
        {"name": "🔸 Categories (Medium)", "method": "GET", "endpoint": "/categories", "requests": 500, "concurrency": 50},
        {"name": "🔸 Product Search (Medium)", "method": "GET", "endpoint": "/products?q=camera&limit=10", "requests": 500, "concurrency": 50},
        
        # Heavy load tests (1000 requests, 100 concurrent)
        {"name": "🔴 Products (Heavy Load)", "method": "GET", "endpoint": "/products?limit=20", "requests": 1000, "concurrency": 100},
        {"name": "🔴 Analytics Stats (Heavy)", "method": "GET", "endpoint": "/analytics/admin/stats?range=7d", "requests": 500, "concurrency": 50},
        
        # Analytics tracking (fire-and-forget test)
        {"name": "📊 Analytics Track (Light)", "method": "POST", "endpoint": "/analytics/track", "requests": 200, "concurrency": 20,
         "json": {"event_type": "page_view", "page_url": "https://test.com/load-test"}},
        {"name": "📊 Analytics Track (Heavy)", "method": "POST", "endpoint": "/analytics/track", "requests": 1000, "concurrency": 100,
         "json": {"event_type": "page_view", "page_url": "https://test.com/load-test"}},
    ]
    
    for test in tests:
        print(f"\n⏳ Running: {test['name']}...")
        result = await tester.run_concurrent_requests(
            method=test["method"],
            endpoint=test["endpoint"],
            num_requests=test["requests"],
            concurrency=test["concurrency"],
            json_data=test.get("json")
        )
        results.append({"name": test["name"], "result": result})
        print_result(result, test["name"])
    
    # Summary
    print("\n" + "=" * 60)
    print("                    📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    print(f"{'Endpoint':<40} {'Avg(ms)':<10} {'P95(ms)':<10} {'RPS':<10} {'Err%':<8}")
    print("-" * 60)
    
    for item in results:
        r = item["result"]
        name = item["name"][:38]
        print(f"{name:<40} {r.avg_response_ms:<10.1f} {r.p95_response_ms:<10.1f} {r.requests_per_second:<10.1f} {r.error_rate:<8.1f}")
    
    print("=" * 60)
    
    # Performance grade
    avg_p95 = statistics.mean([item["result"].p95_response_ms for item in results])
    avg_rps = statistics.mean([item["result"].requests_per_second for item in results])
    avg_err = statistics.mean([item["result"].error_rate for item in results])
    
    print(f"\n📈 Performance globale:")
    print(f"   • P95 moyen: {avg_p95:.1f} ms")
    print(f"   • RPS moyen: {avg_rps:.1f} req/s")
    print(f"   • Taux d'erreur moyen: {avg_err:.2f}%")
    
    if avg_p95 < 100 and avg_err < 1:
        grade = "🏆 EXCELLENT"
    elif avg_p95 < 200 and avg_err < 5:
        grade = "✅ BON"
    elif avg_p95 < 500 and avg_err < 10:
        grade = "⚠️ ACCEPTABLE"
    else:
        grade = "❌ NÉCESSITE OPTIMISATION"
    
    print(f"\n   Note: {grade}")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_load_tests())

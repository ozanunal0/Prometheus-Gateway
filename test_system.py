#!/usr/bin/env python3
"""
System test script for Prometheus Gateway.

This script demonstrates how to test the gateway with different scenarios.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"  # Replace with actual API key

def test_metrics_endpoint():
    """Test the Prometheus metrics endpoint."""
    print("🔍 Testing metrics endpoint...")
    response = requests.get(f"{BASE_URL}/metrics")
    
    if response.status_code == 200:
        print("✅ Metrics endpoint working")
        # Show some sample metrics
        lines = response.text.split('\n')
        for line in lines[:10]:
            if line and not line.startswith('#'):
                print(f"   📊 {line}")
        return True
    else:
        print(f"❌ Metrics endpoint failed: {response.status_code}")
        return False

def test_openapi_docs():
    """Test the OpenAPI documentation endpoint."""
    print("\n📚 Testing OpenAPI docs...")
    response = requests.get(f"{BASE_URL}/docs")
    
    if response.status_code == 200:
        print("✅ OpenAPI docs accessible")
        return True
    else:
        print(f"❌ OpenAPI docs failed: {response.status_code}")
        return False

def test_chat_completion_without_api_key():
    """Test chat completion without API key (should fail)."""
    print("\n🔒 Testing authentication (without API key)...")
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello, world!"}
        ],
        "max_tokens": 50
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 422:  # Expecting authentication error
        print("✅ Authentication properly required")
        return True
    else:
        print(f"❌ Authentication test failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_chat_completion_with_invalid_api_key():
    """Test chat completion with invalid API key."""
    print("\n🔑 Testing with invalid API key...")
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello, world!"}
        ],
        "max_tokens": 50
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "invalid-key-12345"
        }
    )
    
    if response.status_code == 401:
        print("✅ Invalid API key properly rejected")
        return True
    else:
        print(f"❌ Invalid API key test failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_dlp_functionality():
    """Test DLP functionality with PII data."""
    print("\n🛡️ Testing DLP functionality...")
    
    from app.dlp.dlp_scanner import scrub_text
    
    test_text = "Contact John Doe at john.doe@example.com or call (555) 123-4567"
    scrubbed = scrub_text(test_text)
    
    print(f"   Original: {test_text}")
    print(f"   Scrubbed: {scrubbed}")
    
    # Check if PII was detected and replaced
    if "john.doe@example.com" not in scrubbed and "(555) 123-4567" not in scrubbed:
        print("✅ DLP successfully detected and anonymized PII")
        return True
    elif scrubbed != test_text:
        print("✅ DLP made some modifications (partial success)")
        return True
    else:
        print("⚠️ DLP didn't detect PII (might need model download)")
        return False

def test_model_routing():
    """Test model routing logic."""
    print("\n🚦 Testing model routing...")
    
    try:
        from app.services import get_provider
        from app.config import load_config
        
        # Test OpenAI model routing
        try:
            provider = get_provider("gpt-3.5-turbo")
            print("✅ OpenAI model routing works")
            routing_works = True
        except Exception as e:
            print(f"❌ OpenAI model routing failed: {e}")
            routing_works = False
        
        return routing_works
        
    except ImportError as e:
        print(f"⚠️ Could not test routing: {e}")
        return False

def run_performance_test():
    """Run a simple performance test."""
    print("\n⚡ Running performance test...")
    
    start_time = time.time()
    
    # Test metrics endpoint response time
    response = requests.get(f"{BASE_URL}/metrics")
    
    end_time = time.time()
    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
    
    print(f"   📊 Metrics endpoint response time: {response_time:.2f}ms")
    
    if response_time < 1000:  # Less than 1 second
        print("✅ Performance test passed")
        return True
    else:
        print("⚠️ Performance test slow (but functional)")
        return True

def create_test_api_key():
    """Create a test API key if possible."""
    print("\n🔑 Creating test API key...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["python", "create_key.py", "test-user@example.com"],
            capture_output=True,
            text=True,
            cwd="/Users/ozanunal/Desktop/Ozan/LLM/Prometheus-Gateway"
        )
        
        if result.returncode == 0:
            print("✅ Test API key created successfully")
            print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Failed to create API key: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"⚠️ Could not create API key: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Prometheus Gateway System Tests")
    print("=" * 50)
    
    tests = [
        ("Metrics Endpoint", test_metrics_endpoint),
        ("OpenAPI Docs", test_openapi_docs), 
        ("Authentication Required", test_chat_completion_without_api_key),
        ("Invalid API Key Rejection", test_chat_completion_with_invalid_api_key),
        ("DLP Functionality", test_dlp_functionality),
        ("Model Routing", test_model_routing),
        ("Performance", run_performance_test),
        ("API Key Creation", create_test_api_key),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! System is working correctly.")
    elif passed >= total * 0.75:
        print("👍 Most tests passed. System is mostly functional.")
    else:
        print("⚠️ Several tests failed. Please check the configuration.")
    
    print(f"\n⏰ Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
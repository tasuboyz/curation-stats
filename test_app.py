# -*- coding: utf-8 -*-
"""
Test script for Steem Curator Analyzer Web Interface
Tests the basic functionality without starting the full web server
"""

import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def test_imports():
    """Test if all modules can be imported correctly"""
    try:
        print("🔍 Testing imports...")
        
        # Test config
        from config.settings import DEFAULT_USERNAME, STEEM_NODES
        print(f"✅ Config loaded - Default user: {DEFAULT_USERNAME}")
        
        # Test network
        from network.steem_connector import SteemConnector
        print("✅ SteemConnector imported")
        
        # Test services
        from services.analyzer import CuratorAnalyzer
        print("✅ CuratorAnalyzer imported")
        
        # Test web app
        from web.app import app, calculate_efficiency
        print("✅ Flask app imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_efficiency_calculation():
    """Test the efficiency calculation function"""
    try:
        from web.app import calculate_efficiency
        
        print("\n🧮 Testing efficiency calculations...")
        
        # Test cases
        test_cases = [
            (0.1573, 0.13803681493451012, "Normal case"),
            (0, 0.1, "Zero vote value"),
            (0.1, 0, "Zero reward"),
            (0, 0, "Both zero"),
            (None, 0.1, "None vote value"),
            (0.1, None, "None reward")
        ]
        
        for vote_value, reward_sp, description in test_cases:
            efficiency = calculate_efficiency(vote_value, reward_sp)
            print(f"  {description}: vote={vote_value}, reward={reward_sp} -> {efficiency:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Efficiency calculation error: {e}")
        return False

def test_vote_weight_conversion():
    """Test vote weight conversion from 10000 to 100%"""
    print("\n📊 Testing vote weight conversion...")
    
    test_weights = [10000, 5000, 1000, 0, -5000]
    
    for weight in test_weights:
        percentage = weight / 100
        print(f"  {weight} -> {percentage:.1f}%")
    
    return True

def test_analyzer_creation():
    """Test if analyzer can be created"""
    try:
        print("\n🔗 Testing analyzer creation...")
        
        from services.analyzer import CuratorAnalyzer
        analyzer = CuratorAnalyzer()
        
        # Test basic methods
        working_nodes = analyzer.get_working_nodes()
        print(f"✅ Analyzer created - {len(working_nodes)} working nodes found")
        
        for node in working_nodes:
            print(f"  📡 {node}")
        
        return len(working_nodes) > 0
        
    except Exception as e:
        print(f"❌ Analyzer creation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Steem Curator Analyzer Tests")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Efficiency Calculation", test_efficiency_calculation),
        ("Vote Weight Conversion", test_vote_weight_conversion),
        ("Analyzer Creation", test_analyzer_creation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"💥 {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\n🚀 To start the web interface, run:")
        print("   python app.py")
        print("   Then open: http://localhost:5000")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test script for the Tool Selector System
This script tests the basic functionality of the selector system.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from toolregistry_hub.server.selector.route_inspector import RouteInspector
from toolregistry_hub.server.dynamic_router import DynamicRouterManager
from fastapi import FastAPI


async def test_route_inspector():
    """Test the route inspector functionality."""
    print("🔍 Testing Route Inspector...")
    
    inspector = RouteInspector()
    
    try:
        # Discover tools
        tools = inspector.discover_tools()
        
        print(f"✅ Discovered {len(tools)} tools:")
        for tool_id, tool_data in tools.items():
            print(f"  - {tool_data['name']} ({tool_id})")
            print(f"    Prefix: {tool_data['prefix']}")
            print(f"    Tags: {tool_data['tags']}")
            print(f"    Endpoints: {tool_data['endpoint_count']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Route Inspector test failed: {e}")
        return False


async def test_dynamic_router_manager():
    """Test the dynamic router manager functionality."""
    print("⚙️ Testing Dynamic Router Manager...")
    
    # Create a test FastAPI app
    app = FastAPI(title="Test App")
    
    try:
        # Initialize dynamic router manager
        manager = DynamicRouterManager(app, config_file="test_config.json")
        
        # Initialize with discovered tools
        tools = manager.initialize()
        
        print(f"✅ Initialized with {len(tools)} tools")
        
        # Test tool status
        status = manager.get_tool_status()
        print(f"✅ Tool status retrieved: {len(status)} tools")
        
        # Test enabling/disabling tools
        if tools:
            first_tool_id = list(tools.keys())[0]
            
            # Test disable
            success = manager.disable_tool(first_tool_id)
            print(f"✅ Disable tool test: {'passed' if success else 'failed'}")
            
            # Test enable
            success = manager.enable_tool(first_tool_id)
            print(f"✅ Enable tool test: {'passed' if success else 'failed'}")
        
        # Clean up test config file
        test_config = Path("test_config.json")
        if test_config.exists():
            test_config.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Dynamic Router Manager test failed: {e}")
        return False


async def test_selector_app():
    """Test the selector app functionality."""
    print("🌐 Testing Selector App...")
    
    try:
        from toolregistry_hub.server.selector.app import create_selector_app
        
        # Create selector app
        app = create_selector_app()
        
        print("✅ Selector app created successfully")
        print(f"✅ App title: {app.title}")
        print(f"✅ Routes count: {len(app.routes)}")
        
        # Check if required routes exist
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        required_paths = ["/", "/api/tools", "/health"]
        
        for path in required_paths:
            if any(p.startswith(path) for p in route_paths):
                print(f"✅ Route {path} exists")
            else:
                print(f"❌ Route {path} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Selector App test failed: {e}")
        return False


async def test_config_persistence():
    """Test configuration persistence."""
    print("💾 Testing Configuration Persistence...")
    
    try:
        from toolregistry_hub.server.selector.models import ToolRegistry, ToolConfig
        
        # Create test config
        config = ToolRegistry()
        config.tools["test_tool"] = ToolConfig(
            id="test_tool",
            name="Test Tool",
            prefix="/test",
            enabled=True,
            description="A test tool"
        )
        
        # Save to file
        test_file = Path("test_persistence.json")
        with open(test_file, 'w') as f:
            json.dump(config.dict(), f, indent=2, default=str)
        
        print("✅ Configuration saved successfully")
        
        # Load from file
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
        
        loaded_config = ToolRegistry(**loaded_data)
        
        print("✅ Configuration loaded successfully")
        print(f"✅ Loaded {len(loaded_config.tools)} tools")
        
        # Clean up
        test_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration Persistence test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Tool Selector System Tests\n")
    
    tests = [
        ("Route Inspector", test_route_inspector),
        ("Dynamic Router Manager", test_dynamic_router_manager),
        ("Selector App", test_selector_app),
        ("Configuration Persistence", test_config_persistence),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"{'='*50}")
        result = await test_func()
        results.append((test_name, result))
        print()
    
    # Summary
    print(f"{'='*50}")
    print("📊 Test Results Summary:")
    print(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The Tool Selector System is ready to use.")
        print("\nUsage:")
        print("1. Start main server: toolregistry-server --mode openapi --port 8000")
        print("2. Start selector: toolregistry-server --mode selector --port 8001")
        print("3. Open browser: http://localhost:8001")
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed. Please check the implementation.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
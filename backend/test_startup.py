#!/usr/bin/env python
"""
Test script to diagnose startup issues with the API
"""
import sys
import asyncio
import signal
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_app_startup():
    """Test if the app can be imported and started"""
    try:
        logger.info("Attempting to import API...")
        from api import app
        logger.info("✓ API imported successfully")
        
        logger.info("Testing app configuration...")
        logger.info(f"  Routes: {len(app.routes)}")
        logger.info(f"  Middleware: {len(app.user_middleware)}")
        logger.info(f"  Exception handlers: {len(app.exception_handlers)}")
        
        # Test if the app can handle a request
        from fastapi.testclient import TestClient
        logger.info("Creating test client...")
        client = TestClient(app)
        
        logger.info("Testing /api/health endpoint...")
        response = client.get("/api/health")
        logger.info(f"  Status: {response.status_code}")
        logger.info(f"  Response: {response.json()}")
        
        logger.info("✓ All tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_app_startup())
    sys.exit(0 if success else 1)

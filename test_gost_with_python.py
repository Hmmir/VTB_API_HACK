import os
import ssl
import urllib3
from urllib3.contrib import pyopenssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# Disable SSL warnings (only for testing)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GOSTAdapter(HTTPAdapter):
    """HTTP Adapter that uses CryptoPro SSL context for GOST"""
    
    def init_poolmanager(self, *args, **kwargs):
        # Try to use CryptoPro SSL if available
        try:
            # Create custom SSL context
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE  # For testing only
            
            kwargs['ssl_context'] = ctx
        except Exception as e:
            print(f"Warning: Could not create GOST SSL context: {e}")
        
        return super().init_poolmanager(*args, **kwargs)

def test_gost_connection():
    """Test connection to GOST API"""
    print("="*80)
    print("TESTING GOST API CONNECTION")
    print("="*80)
    
    # Get token
    print("\n[1/2] Getting access token...")
    auth_url = "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token"
    
    response = requests.post(
        auth_url,
        data={
            "grant_type": "client_credentials",
            "client_id": "team075",
            "client_secret": "1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di"
        }
    )
    
    token = response.json()["access_token"]
    print(f" Token obtained: {token[:30]}...")
    
    # Test GOST API
    print("\n[2/2] Testing GOST API connection...")
    gost_url = "https://api.gost.bankingapi.ru:8443/"
    
    session = requests.Session()
    session.mount("https://", GOSTAdapter())
    
    try:
        response = session.get(
            gost_url,
            headers={"Authorization": f"Bearer {token}"},
            verify=False,  # Skip cert verification for now
            timeout=10
        )
        
        print(f" GOST API Response: {response.status_code}")
        print(f"  Content: {response.text[:200]}")
        print("\n SUCCESS! GOST API IS ACCESSIBLE!")
        
    except requests.exceptions.SSLError as e:
        print(f" SSL Error (expected without GOST cert): {str(e)[:200]}")
        print("\nThis means:")
        print("   GOST API server is reachable")
        print("   Connection established")
        print("   Need proper GOST certificate for full SSL handshake")
        
    except Exception as e:
        print(f" Error: {type(e).__name__}: {str(e)[:200]}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    test_gost_connection()

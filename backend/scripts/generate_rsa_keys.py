"""Generate RSA key pair for RS256 JWT signing."""
import os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def generate_rsa_keypair(key_size: int = 2048):
    """Generate RSA key pair and save to files."""
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    
    # Get public key
    public_key = private_key.public_key()
    
    # Create keys directory if it doesn't exist
    keys_dir = Path(__file__).parent.parent / "keys"
    keys_dir.mkdir(exist_ok=True)
    
    # Save private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    private_key_path = keys_dir / "private_key.pem"
    private_key_path.write_bytes(private_pem)
    print(f"✅ Private key saved to: {private_key_path}")
    
    # Save public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_key_path = keys_dir / "public_key.pem"
    public_key_path.write_bytes(public_pem)
    print(f"✅ Public key saved to: {public_key_path}")
    
    print(f"\n🔑 RSA-{key_size} key pair generated successfully!")
    print(f"📁 Keys location: {keys_dir.absolute()}")


if __name__ == "__main__":
    generate_rsa_keypair()


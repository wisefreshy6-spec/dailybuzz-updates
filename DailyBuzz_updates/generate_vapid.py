from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

# Generate EC key
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

# Encode keys in URL-safe base64
def encode_key(key_bytes):
    return base64.urlsafe_b64encode(key_bytes).rstrip(b'=').decode('utf-8')

private_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
public_bytes = public_key.public_numbers().x.to_bytes(32, 'big') + public_key.public_numbers().y.to_bytes(32, 'big')

print("VAPID_PUBLIC_KEY =", encode_key(public_bytes))
print("VAPID_PRIVATE_KEY =", encode_key(private_bytes))
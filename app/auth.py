import os
import hmac
import hashlib
from . import db

def hash_nfc_uid(raw_uid):
    """Hash NFC UID using HMAC-SHA256"""
    secret = os.getenv('NFC_HMAC_SECRET', 'change-me-32bytes-min')
    if len(secret) < 32:
        secret = secret.ljust(32, '0')  # Pad to 32 bytes
    
    # Convert secret to bytes
    secret_bytes = secret.encode('utf-8')[:32]
    
    # Hash the raw UID
    return hmac.new(secret_bytes, raw_uid.encode('utf-8'), hashlib.sha256).digest()

def verify_nfc_tag(raw_uid, user_id):
    """Verify if a raw UID belongs to a user"""
    uid_hash = hash_nfc_uid(raw_uid)
    
    tag = db.sql_one("""
        SELECT id, status FROM nfc_tags
        WHERE uid_hash = %s AND user_id = %s
    """, uid_hash, user_id)
    
    return tag is not None and tag[1] == 'active'

def create_nfc_tag(raw_uid, user_id, label=None, departments=None):
    """Create a new NFC tag for a user"""
    uid_hash = hash_nfc_uid(raw_uid)
    key_version = int(os.getenv('NFC_KEY_VERSION', '1'))
    
    # Check if UID already exists
    existing = db.sql_one("SELECT id FROM nfc_tags WHERE uid_hash = %s", uid_hash)
    if existing:
        raise ValueError("NFC tag already exists")
    
    # Create the tag
    tag_id = db.sql_one("""
        INSERT INTO nfc_tags (user_id, uid_hash, key_version, label)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, user_id, uid_hash, key_version, label)[0]
    
    # Assign departments if provided
    if departments:
        for dept_id in departments:
            db.sql_exec("""
                INSERT INTO tag_departments (tag_id, department_id)
                VALUES (%s, %s)
                ON CONFLICT (tag_id, department_id) DO NOTHING
            """, tag_id, dept_id)
    
    return tag_id

def revoke_nfc_tag(tag_id):
    """Revoke an NFC tag"""
    db.sql_exec("""
        UPDATE nfc_tags
        SET status = 'revoked', revoked_at = now()
        WHERE id = %s
    """, tag_id)

def get_user_by_nfc(raw_uid):
    """Get user ID by NFC UID"""
    uid_hash = hash_nfc_uid(raw_uid)
    
    result = db.sql_one("""
        SELECT u.id, t.id as tag_id
        FROM nfc_tags t
        JOIN users u ON t.user_id = u.id
        WHERE t.uid_hash = %s AND t.status = 'active'
    """, uid_hash)
    
    return result

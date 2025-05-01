"""
Gestisce l'interazione con il database SQLite locale crittografato (a livello applicativo).
"""

import sqlite3
import os
import json # For potential complex settings or token storage
from typing import Optional, List, Dict, Any, Tuple

# Import encryption utilities
from ..utils.crypto import encrypt_data, decrypt_data

DATABASE_FILE = "data/pswcursor_data.db"

# Set of setting keys that should be encrypted/decrypted
ENCRYPTED_SETTINGS = {'encrypted_client_secret', 'google_token_json'}

class DatabaseManager:
    """Gestisce la connessione e le operazioni CRUD sul database SQLite."""

    def __init__(self, db_path: str = DATABASE_FILE):
        """
        Inizializza il gestore del database.

        Args:
            db_path: Percorso del file del database SQLite.
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._connect()
        self._create_tables()

    def _connect(self):
        """Stabilisce la connessione al database."""
        try:
            # Connect, setting isolation level for better control if needed
            self.conn = sqlite3.connect(self.db_path, isolation_level=None) # Autocommit mode
            self.conn.row_factory = sqlite3.Row # Access columns by name
            print(f"[DatabaseManager] Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"[DatabaseManager] Error connecting to database: {e}")
            self.conn = None # Ensure conn is None on failure

    def _create_tables(self):
        """Crea le tabelle necessarie se non esistono."""
        if not self.conn:
            print("[DatabaseManager] Cannot create tables: No database connection.")
            return

        cursor = self.conn.cursor()
        try:
            # --- Settings Table (Key-Value Store) ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """)
            print("[DatabaseManager] 'settings' table checked/created.")

            # --- Profiles Table ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                last_name TEXT,
                url TEXT,
                username TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                encrypted_password TEXT, -- Store encrypted password here
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                -- Add other fields as needed, e.g., custom fields JSON?
            )
            """)
            # Trigger to update 'updated_at' timestamp automatically
            cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_profile_timestamp
            AFTER UPDATE ON profiles
            FOR EACH ROW
            BEGIN
                UPDATE profiles SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """)
            print("[DatabaseManager] 'profiles' table checked/created/updated.")
            
            # --- Credentials Table ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                app_name TEXT NOT NULL DEFAULT 'default',
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                username TEXT,
                encrypted_password TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            )
            """)
            # Index on profile_id for faster lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_credentials_profile_id ON credentials (profile_id)")
            # Trigger to update 'updated_at' timestamp automatically
            cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_credential_timestamp
            AFTER UPDATE ON credentials
            FOR EACH ROW
            BEGIN
                UPDATE credentials SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """)
            print("[DatabaseManager] 'credentials' table checked/created/updated (using app_name).")
            
            # --- Pre-populate default settings if table is newly created? ---
            cursor.execute("SELECT 1 FROM settings WHERE key = 'initialized'")
            if cursor.fetchone() is None:
                 print("[DatabaseManager] Populating default settings...")
                 # Define default values, ensuring boolean-like values are strings 'true'/'false'
                 default_settings = [
                     ('sync_enabled', 'false'),
                     ('sync_interval', '300'),
                     ('drive_folder_id', ''), # Use empty string for NULL-like
                     ('hotkey_config_str', 'Nessuno'),
                     ('hotkey_modifiers', '0'),
                     ('hotkey_vk_code', '0'),
                     ('client_id', ''),
                     ('encrypted_client_secret', ''), # Store encrypted secret
                     ('client_secret_encrypted', 'false'), # Flag if secret is encrypted
                     ('master_password_hash_b64', ''),
                     ('master_password_salt_b64', ''),
                     ('google_token_json', ''), # Store Google token JSON here
                     ('initialized', 'true') # Mark as initialized
                 ]
                 cursor.executemany("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", default_settings)

            # Use commit() expli
            # No explicit commit needed here due to isolation_level=None

        except sqlite3.Error as e:
            print(f"[DatabaseManager] Error creating tables: {e}")
            # Rollback is not needed with autocommit
        finally:
            cursor.close()

    def close(self):
        """Chiude la connessione al database."""
        if self.conn:
            print(f"[DatabaseManager] Closing database connection: {self.db_path}")
            self.conn.close()
            self.conn = None

    def get_connection(self) -> Optional[sqlite3.Connection]:
         """Returns the current database connection."""
         # Reconnect if connection was lost or closed
         if not self.conn:
             self._connect()
         return self.conn

    # --- CRUD Methods --- 

    def get_setting(self, key: str, default: Optional[str] = None, 
                    master_password: Optional[str] = None, 
                    salt: Optional[bytes] = None) -> Optional[str]:
        """Retrieves a setting value by key, decrypting if necessary."""
        conn = self.get_connection()
        if not conn:
            return default
            
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                encrypted_value = row['value']
                if key in ENCRYPTED_SETTINGS:
                    if not master_password or not salt:
                        print(f"[DatabaseManager.get_setting] WARNING: Password/salt needed to decrypt setting '{key}', but not provided.")
                        return None # Cannot decrypt
                    # print(f"DEBUG: Decrypting setting '{key}'") # Debug
                    decrypted_value = decrypt_data(encrypted_value, master_password, salt)
                    # print(f"DEBUG: Decryption result for '{key}': {'*'*len(decrypted_value) if decrypted_value else 'None'}")
                    return decrypted_value
                else:
                    # print(f"DEBUG: Returning non-encrypted setting '{key}': {encrypted_value}")
                    return encrypted_value # Not an encrypted setting
            else:
                # print(f"DEBUG: Setting '{key}' not found, returning default.")
                return default # Key not found
        except sqlite3.Error as e:
            print(f"[DatabaseManager.get_setting] Error retrieving setting '{key}': {e}")
            return default
        finally:
            cursor.close()

    def set_setting(self, key: str, value: Any, 
                    master_password: Optional[str] = None, 
                    salt: Optional[bytes] = None):
        """Sets a setting value, encrypting if necessary."""
        conn = self.get_connection()
        if not conn:
             print(f"[DatabaseManager.set_setting] Error: No database connection to set '{key}'.")
             return False # Indicate failure

        value_to_store = str(value) # Ensure value is a string for storage
        
        if key in ENCRYPTED_SETTINGS:
            if not master_password or not salt:
                print(f"[DatabaseManager.set_setting] WARNING: Password/salt needed to encrypt setting '{key}', but not provided. Storing empty.")
                value_to_store = "" # Store empty if encryption not possible
            else:
                 # print(f"DEBUG: Encrypting setting '{key}'")
                 encrypted = encrypt_data(value_to_store, master_password, salt)
                 if encrypted is None:
                      print(f"[DatabaseManager.set_setting] WARNING: Encryption failed for setting '{key}'. Storing empty.")
                      value_to_store = ""
                 else:
                      value_to_store = encrypted
                      # print(f"DEBUG: Storing encrypted value for '{key}': {value_to_store[:10]}...")
        # else: 
             # print(f"DEBUG: Storing non-encrypted setting '{key}': {value_to_store}")

        cursor = conn.cursor()
        try:
            # Use INSERT OR REPLACE (UPSERT)
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value_to_store))
            # print(f"[DatabaseManager.set_setting] Setting '{key}' set successfully.")
            # No commit needed due to isolation_level=None
            return True # Indicate success
        except sqlite3.Error as e:
            print(f"[DatabaseManager.set_setting] Error setting '{key}': {e}")
            return False # Indicate failure
        finally:
            cursor.close()

    # --- Profile CRUD Methods --- 
    def get_all_profiles(self, master_password: Optional[str], salt: Optional[bytes]) -> List[Dict[str, Any]]:
        """Retrieves all profiles, decrypting passwords."""
        conn = self.get_connection()
        profiles = []
        if not conn:
            return profiles
            
        cursor = conn.cursor()
        try:
            cursor.execute("""SELECT id, name, last_name, url, username, email, phone, address, 
                                 encrypted_password, notes, created_at, updated_at 
                             FROM profiles ORDER BY name ASC""")
            rows = cursor.fetchall()
            for row in rows:
                profile_dict = dict(row)
                # Decrypt password
                encrypted_pwd = profile_dict.pop('encrypted_password', None)
                if encrypted_pwd:
                    decrypted_pwd = decrypt_data(encrypted_pwd, master_password, salt)
                    if decrypted_pwd is None:
                        print(f"[DatabaseManager] WARNING: Failed to decrypt password for profile ID {profile_dict.get('id')}. Setting password to None.")
                        profile_dict['password'] = None # Indicate decryption failure
                    else:
                        profile_dict['password'] = decrypted_pwd
                else:
                    profile_dict['password'] = '' # No encrypted password stored
                    
                profiles.append(profile_dict)
            return profiles
        except sqlite3.Error as e:
            print(f"[DatabaseManager.get_all_profiles] Error retrieving profiles: {e}")
            return [] # Return empty list on error
        finally:
            cursor.close()

    def add_profile(self, profile_data: Dict[str, Any], master_password: Optional[str], salt: Optional[bytes]) -> Optional[int]:
        """Adds a new profile, encrypting the password. Returns the new profile ID or None."""
        conn = self.get_connection()
        if not conn:
            return None

        password_to_encrypt = profile_data.get('password', '')
        encrypted_pwd = encrypt_data(password_to_encrypt, master_password, salt) if password_to_encrypt and master_password and salt else ''
        # Handle potential encryption failure (encrypt_data returns None)
        if password_to_encrypt and master_password and salt and encrypted_pwd is None:
             print(f"[DatabaseManager.add_profile] ERROR: Failed to encrypt password. Aborting add.")
             return None

        # Aggiungi last_name a SQL e params
        sql = """INSERT INTO profiles (name, last_name, url, username, email, phone, address, encrypted_password, notes) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (
            profile_data.get('name'),
            profile_data.get('last_name'), # Nuovo campo
            profile_data.get('url'),
            profile_data.get('username'),
            profile_data.get('email'),
            profile_data.get('phone'),
            profile_data.get('address'),
            encrypted_pwd,
            profile_data.get('notes')
        )
        
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            new_id = cursor.lastrowid
            print(f"[DatabaseManager.add_profile] Profile added successfully with ID: {new_id}")
            return new_id
        except sqlite3.Error as e:
            print(f"[DatabaseManager.add_profile] Error adding profile: {e}")
            return None
        finally:
            cursor.close()
        
    def update_profile(self, profile_id: int, profile_data: Dict[str, Any], master_password: Optional[str], salt: Optional[bytes]) -> bool:
         """Updates an existing profile, encrypting the password."""
         conn = self.get_connection()
         if not conn:
            return False

         fields_to_update = []
         params = []
         
         # Prepara campi e parametri per l'aggiornamento
         if 'name' in profile_data: fields_to_update.append("name = ?"); params.append(profile_data['name'])
         if 'last_name' in profile_data: fields_to_update.append("last_name = ?"); params.append(profile_data['last_name']) # Nuovo campo
         if 'url' in profile_data: fields_to_update.append("url = ?"); params.append(profile_data['url'])
         if 'username' in profile_data: fields_to_update.append("username = ?"); params.append(profile_data['username'])
         if 'email' in profile_data: fields_to_update.append("email = ?"); params.append(profile_data['email'])
         if 'phone' in profile_data: fields_to_update.append("phone = ?"); params.append(profile_data['phone'])
         if 'address' in profile_data: fields_to_update.append("address = ?"); params.append(profile_data['address'])
         if 'notes' in profile_data: fields_to_update.append("notes = ?"); params.append(profile_data['notes'])
         
         # Gestisci crittografia password se fornita
         if 'password' in profile_data:
             password_to_encrypt = profile_data['password']
             encrypted_pwd = encrypt_data(password_to_encrypt, master_password, salt) if password_to_encrypt and master_password and salt else ''
             if password_to_encrypt and master_password and salt and encrypted_pwd is None:
                 print(f"[DatabaseManager.update_profile] ERROR: Failed to encrypt password for profile ID {profile_id}. Aborting update.")
                 return False
             fields_to_update.append("encrypted_password = ?")
             params.append(encrypted_pwd)
             
         if not fields_to_update:
             print("[DatabaseManager.update_profile] No fields provided for update.")
             return False # Nothing to update
             
         sql = f"UPDATE profiles SET {', '.join(fields_to_update)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
         params.append(profile_id) # Add the ID for the WHERE clause
         
         cursor = conn.cursor()
         try:
            cursor.execute(sql, tuple(params))
            updated_rows = cursor.rowcount
            if updated_rows > 0:
                 print(f"[DatabaseManager.update_profile] Profile ID {profile_id} updated successfully.")
                 return True
            else:
                 print(f"[DatabaseManager.update_profile] Profile ID {profile_id} not found for update.")
                 return False
         except sqlite3.Error as e:
            print(f"[DatabaseManager.update_profile] Error updating profile ID {profile_id}: {e}")
            return False
         finally:
            cursor.close()

    def delete_profile(self, profile_id: int) -> bool:
         """Deletes a profile by ID."""
         conn = self.get_connection()
         if not conn:
             return False
             
         sql = "DELETE FROM profiles WHERE id = ?"
         cursor = conn.cursor()
         try:
            cursor.execute(sql, (profile_id,))
            deleted_rows = cursor.rowcount
            if deleted_rows > 0:
                 print(f"[DatabaseManager.delete_profile] Profile ID {profile_id} deleted successfully.")
                 return True
            else:
                 print(f"[DatabaseManager.delete_profile] Profile ID {profile_id} not found for deletion.")
                 return False
         except sqlite3.Error as e:
            print(f"[DatabaseManager.delete_profile] Error deleting profile ID {profile_id}: {e}")
            return False
         finally:
            cursor.close()

    # --- Credentials CRUD Methods ---
    def get_credentials_for_profile(self, profile_id: int, master_password: Optional[str], salt: Optional[bytes]) -> List[Dict[str, Any]]:
        """Retrieves all credentials for a given profile ID, decrypting passwords."""
        conn = self.get_connection()
        credentials = []
        if not conn:
            return credentials

        # Aggiungi first_name, last_name, email alla SELECT
        sql = """SELECT id, profile_id, app_name, first_name, last_name, email, username, 
                      encrypted_password, notes, created_at, updated_at 
                 FROM credentials WHERE profile_id = ? ORDER BY app_name ASC"""
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (profile_id,))
            rows = cursor.fetchall()
            for row in rows:
                cred_dict = dict(row)
                # Decrypt password
                encrypted_pwd = cred_dict.pop('encrypted_password', None)
                if encrypted_pwd:
                    decrypted_pwd = decrypt_data(encrypted_pwd, master_password, salt)
                    if decrypted_pwd is None:
                        print(f"[DatabaseManager] WARNING: Failed to decrypt password for credential ID {cred_dict.get('id')}.")
                        cred_dict['password'] = None # Indicate decryption failure
                    else:
                        cred_dict['password'] = decrypted_pwd
                else:
                    cred_dict['password'] = '' # No encrypted password stored
                credentials.append(cred_dict)
            return credentials
        except sqlite3.Error as e:
            print(f"[DatabaseManager.get_credentials_for_profile] Error retrieving credentials for profile {profile_id}: {e}")
            return []
        finally:
            cursor.close()
            
    def add_credential(self, cred_data: Dict[str, Any], master_password: Optional[str], salt: Optional[bytes]) -> Optional[int]:
        """Adds a new credential, encrypting the password. Returns the new credential ID or None."""
        conn = self.get_connection()
        if not conn:
            return None

        password_to_encrypt = cred_data.get('password', '')
        encrypted_pwd = encrypt_data(password_to_encrypt, master_password, salt) if password_to_encrypt and master_password and salt else ''
        if password_to_encrypt and master_password and salt and encrypted_pwd is None:
            print(f"[DatabaseManager.add_credential] ERROR: Failed to encrypt password. Aborting add.")
            return None
            
        # Aggiungi first_name, last_name, email a SQL e params
        sql = """INSERT INTO credentials (profile_id, app_name, first_name, last_name, email, username, encrypted_password, notes) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (
            cred_data.get('profile_id'),
            cred_data.get('app_name', 'default'),
            cred_data.get('first_name'), # Nuovo
            cred_data.get('last_name'), # Nuovo
            cred_data.get('email'), # Nuovo
            cred_data.get('username'),
            encrypted_pwd,
            cred_data.get('notes')
        )

        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            new_id = cursor.lastrowid
            print(f"[DatabaseManager.add_credential] Credential added successfully with ID: {new_id}")
            return new_id
        except sqlite3.Error as e:
            print(f"[DatabaseManager.add_credential] Error adding credential: {e}")
            return None
        finally:
            cursor.close()

    def update_credential(self, credential_id: int, cred_data: Dict[str, Any], master_password: Optional[str], salt: Optional[bytes]) -> bool:
        """Updates an existing credential, encrypting the password if provided."""
        conn = self.get_connection()
        if not conn:
            return False
            
        fields_to_update = []
        params = []

        # Aggiungi i nuovi campi
        if 'app_name' in cred_data: fields_to_update.append("app_name = ?"); params.append(cred_data['app_name'])
        if 'first_name' in cred_data: fields_to_update.append("first_name = ?"); params.append(cred_data['first_name']) # Nuovo
        if 'last_name' in cred_data: fields_to_update.append("last_name = ?"); params.append(cred_data['last_name']) # Nuovo
        if 'email' in cred_data: fields_to_update.append("email = ?"); params.append(cred_data['email']) # Nuovo
        if 'username' in cred_data: fields_to_update.append("username = ?"); params.append(cred_data['username'])
        if 'notes' in cred_data: fields_to_update.append("notes = ?"); params.append(cred_data['notes'])

        # Gestisci crittografia password se fornita
        if 'password' in cred_data:
            password_to_encrypt = cred_data['password']
            encrypted_pwd = encrypt_data(password_to_encrypt, master_password, salt) if password_to_encrypt and master_password and salt else ''
            if password_to_encrypt and master_password and salt and encrypted_pwd is None:
                print(f"[DatabaseManager.update_credential] ERROR: Failed to encrypt password for credential ID {credential_id}. Aborting update.")
                return False
            fields_to_update.append("encrypted_password = ?")
            params.append(encrypted_pwd)

        if not fields_to_update:
            print("[DatabaseManager.update_credential] No fields provided for update.")
            return False # Nothing to update

        sql = f"UPDATE credentials SET {', '.join(fields_to_update)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        params.append(credential_id) # Add the ID for the WHERE clause

        cursor = conn.cursor()
        try:
            cursor.execute(sql, tuple(params))
            updated_rows = cursor.rowcount
            if updated_rows > 0:
                print(f"[DatabaseManager.update_credential] Credential ID {credential_id} updated successfully.")
                return True
            else:
                print(f"[DatabaseManager.update_credential] Credential ID {credential_id} not found for update.")
                return False
        except sqlite3.Error as e:
            print(f"[DatabaseManager.update_credential] Error updating credential ID {credential_id}: {e}")
            return False
        finally:
            cursor.close()
            
    def delete_credential(self, credential_id: int) -> bool:
        """Deletes a credential by ID."""
        conn = self.get_connection()
        if not conn:
            return False

        sql = "DELETE FROM credentials WHERE id = ?"
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (credential_id,))
            deleted_rows = cursor.rowcount
            if deleted_rows > 0:
                print(f"[DatabaseManager.delete_credential] Credential ID {credential_id} deleted successfully.")
                return True
            else:
                print(f"[DatabaseManager.delete_credential] Credential ID {credential_id} not found for deletion.")
                return False
        except sqlite3.Error as e:
            print(f"[DatabaseManager.delete_credential] Error deleting credential ID {credential_id}: {e}")
            return False
        finally:
            cursor.close()

# --- Singleton Instance ---
# Optional: Provide a way to get a single instance if needed across the app
_db_manager_instance: Optional[DatabaseManager] = None

def get_db_manager() -> DatabaseManager:
    """Returns a singleton instance of the DatabaseManager."""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
    # Ensure connection is still valid (or reconnect)
    if _db_manager_instance.get_connection() is None:
         print("[get_db_manager] WARNING: Database connection was lost. Re-initializing manager.")
         _db_manager_instance = DatabaseManager() # Re-initialize if connection lost
         if _db_manager_instance.get_connection() is None:
              raise ConnectionError("Failed to establish database connection.")

    return _db_manager_instance 
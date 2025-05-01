import secrets
import string

DEFAULT_PASSWORD_LENGTH = 32
MIN_PASSWORD_LENGTH = 16
MAX_PASSWORD_LENGTH = 64

def generate_secure_password(
    length: int = DEFAULT_PASSWORD_LENGTH,
    use_uppercase: bool = True,
    use_lowercase: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True
) -> str:
    """
    Generates a secure, random password with configurable character sets and length.

    Args:
        length: The desired length of the password. Clamped between MIN and MAX.
        use_uppercase: Include uppercase letters (A-Z).
        use_lowercase: Include lowercase letters (a-z).
        use_digits: Include digits (0-9).
        use_symbols: Include symbols (!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?).

    Returns:
        A securely generated password string.

    Raises:
        ValueError: If no character sets are selected.
    """
    length = max(MIN_PASSWORD_LENGTH, min(length, MAX_PASSWORD_LENGTH))
    
    character_set = ""
    if use_uppercase:
        character_set += string.ascii_uppercase
    if use_lowercase:
        character_set += string.ascii_lowercase
    if use_digits:
        character_set += string.digits
    if use_symbols:
        # Consider adding more symbols if needed
        character_set += "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?" 

    if not character_set:
        raise ValueError("At least one character set must be selected.")

    # Ensure the password contains at least one character from each selected set
    password_chars = []
    if use_uppercase:
        password_chars.append(secrets.choice(string.ascii_uppercase))
    if use_lowercase:
        password_chars.append(secrets.choice(string.ascii_lowercase))
    if use_digits:
        password_chars.append(secrets.choice(string.digits))
    if use_symbols:
        password_chars.append(secrets.choice("!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?"))

    # Fill the rest of the password length
    remaining_length = length - len(password_chars)
    for _ in range(remaining_length):
        password_chars.append(secrets.choice(character_set))

    # Shuffle the list to ensure randomness
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars) 
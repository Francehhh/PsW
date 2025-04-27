# PsW - Password Manager

🔐 A modern, secure, and easy-to-use password manager.

## Key Features

- **End-to-End Encryption**: Data protection with AES-256
- **Profile Management**: Organize your credentials in separate profiles
- **Cloud Synchronization**: Secure backup on Google Drive
- **Modern Interface**: Clean and intuitive design
- **Advanced Security**: Master password protection with Argon2
- **Cross-Platform**: Support for Windows, Linux, and macOS

## Installation

### Prerequisites
- Python 3.8+
- pip

### Steps
1. Clone the repository:
   ```bash
   git clone [https://github.com/Francehhh/PsW.git](https://github.com/Francehhh/PsW.git)
   cd PsW
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Usage

1. Upon first launch, create a secure master password
2. Use the master password to access the application
3. Create profiles to organize your credentials
4. Add and manage credentials within profiles

## Project Structure

PsW/
├── src/
│   ├── core/         # Business logic
│   ├── ui/           # User interface
│   └── utils/        # Utilities and helpers
├── data/             # Data storage (encrypted)
├── tests/            # Unit tests
└── docs/             # Documentation

## Security

- AES-256 encryption for data
- Key derivation with Argon2
- No default passwords
- Strict input validation
- Regular code audit

## Contributing

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/name`)
3. Commit your changes (`git commit -am 'Add feature'`)
4. Push to the branch (`git push origin feature/name`)
5. Create a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Specifications

- PySide6 for the GUI
- cryptography for encryption
- Google Drive API for synchronization

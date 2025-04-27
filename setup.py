from setuptools import setup, find_packages

setup(
    name="password-manager",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.5.0",
        "cryptography>=41.0.0",
        "argon2-cffi>=23.1.0",
        "google-api-python-client>=2.100.0",
        "google-auth-oauthlib>=1.0.0",
        "pillow>=10.0.0"
    ],
    entry_points={
        "console_scripts": [
            "password-manager=main:main"
        ]
    }
) 
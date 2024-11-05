import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.logger import logger

certs_dir = "../certs"
private_key_path = os.path.join(certs_dir, "jwt-private.pem")
public_key_path = os.path.join(certs_dir, "jwt-public.pem")

# Проверка существования ключей
if os.path.exists(private_key_path) and os.path.exists(public_key_path):
    logger.info("The certificates already exist. Generation is not required.")
else:
    os.makedirs(certs_dir, exist_ok=True)

    # Генерация приватного ключа
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Сохранение приватного ключа в файл
    with open(private_key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Генерация публичного ключа из приватного
    public_key = private_key.public_key()

    # Сохранение публичного ключа в файл
    with open(public_key_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

    logger.info("RSA keys have been successfully created and saved.")

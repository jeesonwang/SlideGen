import base64
from datetime import datetime

from gmssl import sm2, sm4

from config.conf import SM2_PRIVATE_KEY, SM2_PUBLIC_KEY, SM4_KEY


class SM2:
    def __init__(self):
        self.crypt = sm2.CryptSM2(private_key=SM2_PRIVATE_KEY, public_key=SM2_PUBLIC_KEY, mode=1)

    def encrypt(self, plaintext: str):
        """加密方法"""
        encrypt_bytes = self.crypt.encrypt(plaintext.encode(encoding="utf-8"))
        encrypt_b64_bytes = base64.b64encode(encrypt_bytes)
        ciphertext = encrypt_b64_bytes.decode("utf-8")
        return ciphertext

    def decrypt(self, ciphertext: str):
        """解密方法"""
        encrypt_b64_bytes = ciphertext.encode("utf-8")
        encrypt_bytes = base64.b64decode(encrypt_b64_bytes)
        plaintext = self.crypt.decrypt(encrypt_bytes).decode(encoding="utf-8")
        return plaintext


class SM4:
    def __init__(self):
        self.crypt = sm4.CryptSM4(SM4_KEY)  # 实例化

    def encrypt(self, plaintext: str):
        self.crypt.set_key(key=bytes.fromhex(SM4_KEY), mode=sm4.SM4_ENCRYPT)
        encrypt_value = self.crypt.crypt_ecb(plaintext.encode())
        return encrypt_value.hex()

    def decrypt(self, ciphertext: str):
        self.crypt.set_key(key=bytes.fromhex(SM4_KEY), mode=sm4.SM4_DECRYPT)
        decrypt_value = self.crypt.crypt_ecb(bytes.fromhex(ciphertext))  # ecb模式开始解密。bytes.fromhex():十六进制字符转为十六进制字节
        return decrypt_value.decode()


gm_sm2 = SM2()
gm_sm4 = SM4()


class TimeCodePack:
    @staticmethod
    def encode(obj):
        if isinstance(obj, datetime):
            return str(obj)
        return obj

    @staticmethod
    def decode(obj):
        if isinstance(obj, str):
            try:
                return datetime.fromisoformat(obj)
            except ValueError:
                pass
        return obj

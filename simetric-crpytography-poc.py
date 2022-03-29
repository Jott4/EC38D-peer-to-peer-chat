from cryptography.fernet import Fernet

key = Fernet.generate_key()

fernet_obj = Fernet(key)


encrypted_message = fernet_obj.encrypt(str.encode("Hello World"))

print("encrypted message", encrypted_message)

decrypted_message = fernet_obj.decrypt(encrypted_message)
print("decrypted message", decrypted_message)
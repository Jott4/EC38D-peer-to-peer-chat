import rsa

publicKey, privateKey = rsa.newkeys(512)

message = "fica nenem"

encripted_message = rsa.encrypt(message.encode(), publicKey)

print(encripted_message)

decrypted_message = rsa.decrypt(encripted_message, privateKey)

print(decrypted_message)

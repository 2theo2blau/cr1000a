
import os
import subprocess
import shlex
import sys
import argparse
import tarfile
import io

unobfuscated_key = bytes.fromhex(
    '65676a796f646c746a6870646b67746b6832333470363536376c613230666c760000000000000000000000000000000000000000000000000000000000000000'
)
hardcoded_iv = bytes.fromhex(
    '36613730363436633639363637373634'
)
dot_encrypt_data = bytes.fromhex(
    '2e0ce09b5d412c36430bed8fb61af11b8834877351293fceedb55e812b9e8daa81e0c617117de5b87c93b505200c9b20'
)

iv_size = 0x10
key_size = 0x20

def aes_decrypt(key, iv, payload):
    cmd = f"openssl enc -d -aes-256-cbc -K {key[:key_size].hex()} -iv {iv.hex()}"
    proc = subprocess.Popen(shlex.split(cmd),
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate(payload)
    return out

def aes_encrypt(key, iv, payload):
    cmd = f"openssl enc -e -aes-256-cbc -K {key[:key_size].hex()} -iv {iv.hex()}"
    proc = subprocess.Popen(shlex.split(cmd),
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate(payload)
    return out

def decrypt_config(input, output):
    with open(input, 'rb') as f:
        file_size = os.fstat(f.fileno()).st_size
        payload = f.read(file_size - iv_size)
        iv = f.read(iv_size)
    
    unwrapped_key = aes_decrypt(key=unobfuscated_key, iv=hardcoded_iv, payload=dot_encrypt_data)
    
    decrypted_payload = aes_decrypt(key=unwrapped_key, iv=iv, payload=payload)
    decrypted_payload_io = io.BytesIO(decrypted_payload)
    
    tar = tarfile.open(fileobj=decrypted_payload_io)
    tar.extractall(path=output)
    
    print(f"decrypted: {len(decrypted_payload)} bytes")
    print(f"done: written output to {output}")

def encrypt_config(input, output):
    with open(input + os.path.sep + 'backup_md5', 'wb') as f:
        # firmware has a bug where it doesn't actually generate or check real md5.
        f.write(bytes("080ce472b78ed93cdea5f79efaa4c39e  -\n", 'utf-8'))
    
    encrypted_payload_io = io.BytesIO()
    tar = tarfile.open(fileobj=encrypted_payload_io, mode='w:gz')
    
    for filename in os.listdir(input):
        full_path = os.path.join(input, filename)
        tar.add(full_path, arcname=filename)
    
    tar.close()
    
    unwrapped_key = aes_decrypt(key=unobfuscated_key, iv=hardcoded_iv, payload=dot_encrypt_data)
    encrypted_payload = aes_encrypt(key=unwrapped_key, iv=hardcoded_iv, payload=encrypted_payload_io.getbuffer())
    
    with open(output, "wb") as f:
        f.write(encrypted_payload)
        f.write(hardcoded_iv)
        
    print(f"encrypted: {len(encrypted_payload)} bytes")
    print(f"done: written output to {output}")

parser = argparse.ArgumentParser()

parser.add_argument('-c', '--command', choices=['encrypt', 'decrypt'], default='decrypt')
parser.add_argument('-i', '--input', required=True)
parser.add_argument('-o', '--output', required=False)

args = parser.parse_args()

match args.command:
    case 'encrypt':
        input = os.path.realpath(args.input)
        
        if not os.path.exists(input) or os.path.isfile(input):
            print(f"{input} doesn't exist or is not a directory")
            sys.exit(1)
        
        encrypt_config(input, args.output or input + '.cfg')
        
    case 'decrypt':
        input = os.path.realpath(args.input)
        
        if not os.path.isfile(input):
            print(f"{input} doesn't exist or is not a file")
            sys.exit(1)
        
        decrypt_config(input, args.output or os.path.splitext(input)[0])
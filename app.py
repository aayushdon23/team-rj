# this code was made by cutehack

from flask import Flask, request, jsonify
import asyncio
import aiohttp
import binascii
import requests
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.json_format import MessageToDict
import like_pb2
import like_count_pb2
import uid_generator_pb2

app = Flask(__name__)

# Load tokens based on server
def load_tokens(server_name):
    if server_name == "IND":
        with open("token_ind.json", "r") as f:
            return json.load(f)
    elif server_name in {"BR", "US", "SAC", "NA"}:
        with open("token_br.json", "r") as f:
            return json.load(f)
    else:
        with open("token_bd.json", "r") as f:
            return json.load(f)

# Encrypt a message with AES
def encrypt_message(plaintext):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%' 
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(plaintext, AES.block_size)
    encrypted_message = cipher.encrypt(padded_message)
    return binascii.hexlify(encrypted_message).decode('utf-8')

# Create protobuf message for like sending
def create_protobuf_message(user_id, region):
    message = like_pb2.like()
    message.uid = int(user_id)
    message.region = region
    return message.SerializeToString()

# Async request sending
async def send_request(encrypted_uid, token, url):
    edata = bytes.fromhex(encrypted_uid)
    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Authorization': f"Bearer {token}",
        'Content-Type': "application/x-www-form-urlencoded",
        'Expect': "100-continue",
        'X-Unity-Version': "2018.4.11f1",
        'X-GA': "v1 1",
        'ReleaseVersion': "OB48"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=edata, headers=headers) as response:
            return response.status

# Send multiple likes
async def send_multiple_requests(uid, server_name, url):
    region = server_name
    protobuf_message = create_protobuf_message(uid, region)
    encrypted_uid = encrypt_message(protobuf_message)
    
    tasks = []
    tokens = load_tokens(server_name)
    if not tokens:
        return {"error": "No tokens available for this region."}
    
    for i in range(100):
        token = tokens[i % len(tokens)]["token"]
        tasks.append(send_request(encrypted_uid, token, url))
    
    results = await asyncio.gather(*tasks)
    return results

# Create UID Protobuf for Player Profile
def create_protobuf(uid):
    message = uid_generator_pb2.uid_generator()
    message.krishna_ = int(uid)
    message.teamXdarks = 1
    return message.SerializeToString()

# Encrypt UID for Player Profile
def enc(uid):
    protobuf_data = create_protobuf(uid)
    encrypted_uid = encrypt_message(protobuf_data)
    return encrypted_uid

# Make request to Free Fire server
def make_request(encrypted_uid, server_name, token):
    if server_name == "IND":
        url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
    elif server_name in {"BR", "US", "SAC", "NA"}:
        url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
    else:
        url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"

    edata = bytes.fromhex(encrypted_uid)
    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Authorization': f"Bearer {token}",
        'Content-Type': "application/x-www-form-urlencoded",
        'Expect': "100-continue",
        'X-Unity-Version': "2018.4.11f1",
        'X-GA': "v1 1",
        'ReleaseVersion': "OB48"
    }

    response = requests.post(url, data=edata, headers=headers)
    return response

# Flask route to send likes
@app.route('/like', methods=['POST'])
def like():
    data = request.json
    uid = data.get('uid')
    server_name = data.get('server')

    if not uid or not server_name:
        return jsonify({'error': 'uid and server fields are required.'}), 400

    if server_name == "IND":
        url = "https://client.ind.freefiremobile.com/SendLike"
    elif server_name in {"BR", "US", "SAC", "NA"}:
        url = "https://client.us.freefiremobile.com/SendLike"
    else:
        url = "https://clientbp.ggblueshark.com/SendLike"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(send_multiple_requests(uid, server_name, url))
    return jsonify({'status_codes': result})

# Flask route to get player profile
@app.route('/profile', methods=['POST'])
def profile():
    data = request.json
    uid = data.get('uid')
    server_name = data.get('server')

    if not uid or not server_name:
        return jsonify({'error': 'uid and server fields are required.'}), 400

    tokens = load_tokens(server_name)
    if not tokens:
        return jsonify({'error': 'No tokens available for this region.'}), 400

    token = tokens[0]["token"]
    encrypted_uid = enc(uid)
    response = make_request(encrypted_uid, server_name, token)

    if response.status_code == 200:
        return jsonify({'data': MessageToDict(uid_generator_pb2.uid_generator())})
    else:
        return jsonify({'error': f"Request failed with status code {response.status_code}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
import requests
import json
import time

RPC_USER, RPC_PASS = "nChain", "pass123"
RPC_URL = "http://127.0.0.1:18443"
WALLET = "nChainWallet"

def rpc(method, params=[], wallet_endpoint=True):
    url = f"{RPC_URL}/wallet/{WALLET}" if wallet_endpoint else RPC_URL
    payload = json.dumps({"jsonrpc": "2.0", "id": "1", "method": method, "params": params})
    resp = requests.post(url, auth=(RPC_USER, RPC_PASS), data=payload)
    if resp.status_code != 200:
        print(f"RPC Error ({method}): {resp.text}")
    return resp.json()

def main():
    print("--- Task 1: Setup and Address Generation ---")
    
    # Load or create wallet
    res = rpc("loadwallet", [WALLET], wallet_endpoint=False)
    if 'error' in res and res['error'] and res['error'].get('code') != -35:
        print("Creating new wallet...")
        rpc("createwallet", [WALLET], wallet_endpoint=False)
    
    # Generate three Legacy addresses: A, B, and C
    addr_a = rpc("getnewaddress", ["AddressA_Legacy", "legacy"])['result']
    addr_b = rpc("getnewaddress", ["AddressB_Legacy", "legacy"])['result']
    addr_c = rpc("getnewaddress", ["AddressC_Legacy", "legacy"])['result']
    
    print("Addresses Generated:")
    print(f"A: {addr_a}\nB: {addr_b}\nC: {addr_c}\n")

    print("Mining 101 blocks to Address A...")
    rpc("generatetoaddress", [101, addr_a])
    balance = rpc('getbalance')['result']
    print(f"Balance: {balance} BTC\n")
    
    print("--- Task 2: Transaction from A to B ---")
    
    unspent_a = rpc("listunspent", [1, 999, [addr_a]])['result'][0]
    inputs_a = [{"txid": unspent_a['txid'], "vout": unspent_a['vout']}]
    
    # Send 10 BTC to B, send the rest to a change address, subtracting approx fee
    change_address_a = rpc("getrawchangeaddress")['result']
    amount_a = float(unspent_a['amount'])
    outputs_ab = {addr_b: 10.0, change_address_a: round(amount_a - 10.0 - 0.0001, 5)}
    
    raw_tx_ab = rpc("createrawtransaction", [inputs_a, outputs_ab])['result']
    
    decoded_ab = rpc("decoderawtransaction", [raw_tx_ab])['result']
    for vout in decoded_ab['vout']:
        addr_list = vout['scriptPubKey'].get('addresses', [])
        addr_v = vout['scriptPubKey'].get('address', "")
        if addr_b in addr_list or addr_v == addr_b:
            print(f"[REPORT DATA] Locking Script for B: {vout['scriptPubKey']['asm']}\n")
            break

    signed_ab = rpc("signrawtransactionwithwallet", [raw_tx_ab])['result']
    txid_ab = rpc("sendrawtransaction", [signed_ab['hex']])['result']
    print(f"Success! Transaction A -> B TXID: {txid_ab}\n")
    
    # Mine a block to confirm the transaction from A to B
    rpc("generatetoaddress", [1, addr_a])

    print("--- Task 3: Transaction from B to C ---")
    
    unspent_b = rpc("listunspent", [1, 999, [addr_b]])['result'][0]
    print(f"Found UTXO from A->B: {unspent_b['txid']} (vout: {unspent_b['vout']})\n")

    inputs_b = [{"txid": unspent_b['txid'], "vout": unspent_b['vout']}]
    
    change_address_b = rpc("getrawchangeaddress")['result']
    amount_b_utxo = float(unspent_b['amount'])
    # Send all but min fee to C 
    outputs_bc = {addr_c: 9.999} 
    
    raw_tx_bc = rpc("createrawtransaction", [inputs_b, outputs_bc])['result']
    signed_bc = rpc("signrawtransactionwithwallet", [raw_tx_bc])['result']
    
    decoded_bc = rpc("decoderawtransaction", [signed_bc['hex']])['result']
    
    vin = decoded_bc['vin'][0]
    if 'scriptSig' in vin:
        print(f"[REPORT DATA] Unlocking Script (scriptSig) from B: \n{vin['scriptSig']['asm']}\n")
        
    for vout in decoded_bc['vout']:
        addr_list = vout['scriptPubKey'].get('addresses', [])
        addr_v = vout['scriptPubKey'].get('address', "")
        if addr_c in addr_list or addr_v == addr_c:
            print(f"[REPORT DATA] Locking Script for C: {vout['scriptPubKey']['asm']}\n")
            break

    txid_bc = rpc("sendrawtransaction", [signed_bc['hex']])['result']
    print(f"Success! Transaction B -> C TXID: {txid_bc}\n")
    
    rpc("generatetoaddress", [1, addr_c])
    print("Final Block mined. All tasks complete.")

if __name__ == "__main__":
    main()

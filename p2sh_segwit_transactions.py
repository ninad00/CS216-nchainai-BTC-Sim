import requests
import json
import time

RPC_USER, RPC_PASS = "nChain", "pass123"
RPC_URL = "http://127.0.0.1:18443"
WALLET = "segwitWallet"

def rpc(method, params=[], wallet_endpoint=True):
    url = f"{RPC_URL}/wallet/{WALLET}" if wallet_endpoint else RPC_URL
    payload = json.dumps({"jsonrpc": "2.0", "id": "1", "method": method, "params": params})
    resp = requests.post(url, auth=(RPC_USER, RPC_PASS), data=payload)
    if resp.status_code != 200:
        print(f"RPC Error: {resp.text}")
    return resp.json()

def main():
    print("--- Task 1: Setup and Address Generation ---")
    
    # Load or create wallet
    res = rpc("loadwallet", [WALLET], wallet_endpoint=False)
    if 'error' in res and res['error'] and res['error'].get('code') != -35:
        print("Creating new wallet...")
        rpc("createwallet", [WALLET], wallet_endpoint=False)
    
    # Generate three P2SH-SegWit addresses: A’, B’, and C’
    # In Bitcoin Core, we can specify address_type as 'p2sh-segwit'
    addr_a = rpc("getnewaddress", ["AddressA_P2SH_SegWit", "p2sh-segwit"])['result']
    addr_b = rpc("getnewaddress", ["AddressB_P2SH_SegWit", "p2sh-segwit"])['result']
    addr_c = rpc("getnewaddress", ["AddressC_P2SH_SegWit", "p2sh-segwit"])['result']
    
    print("Addresses Generated:")
    print(f"A': {addr_a}\nB': {addr_b}\nC': {addr_c}\n")

    print("Mining blocks to get funds...")
    funding_addr = rpc("getnewaddress", ["Funding", "bech32"])['result']
    rpc("generatetoaddress", [101, funding_addr]) # mine 101 blocks to make coinbase mature
    
    print("Funding Address A'...")
    # fund A' with 10 BTC
    fund_txid = rpc("sendtoaddress", [addr_a, 10.0])['result']
    
    rpc("generatetoaddress", [1, funding_addr])
    print(f"Address A' funded with 10 BTC. TXID: {fund_txid}\n")
    
    print("--- Task 2: Transaction from A' to B' ---")
    
    # Get unspent output for A'
    unspent_a = rpc("listunspent", [1, 999, [addr_a]])['result'][0]
    
    inputs_a = [{"txid": unspent_a['txid'], "vout": unspent_a['vout']}]
    
    # Send 5 BTC to B', send the rest to a change address, subtracting 0.0001 BTC for fee
    change_address_a = rpc("getrawchangeaddress")['result']
    amount_a = float(unspent_a['amount'])
    outputs_ab = {addr_b: 5.0, change_address_a: round(amount_a - 5.0 - 0.0001, 5)}
    
    raw_tx_ab = rpc("createrawtransaction", [inputs_a, outputs_ab])['result']
    
    decoded_ab = rpc("decoderawtransaction", [raw_tx_ab])['result']
    for vout in decoded_ab['vout']:
        addr_list = vout['scriptPubKey'].get('addresses', [])
        addr_v = vout['scriptPubKey'].get('address', "")
        if addr_b in addr_list or addr_v == addr_b:
            print(f"[REPORT DATA] Challenge (Locking) Script for B': {vout['scriptPubKey']['asm']}")
            break

    # Sign the transaction
    signed_ab = rpc("signrawtransactionwithwallet", [raw_tx_ab])['result']
    
    # Broadcast the transaction
    txid_ab = rpc("sendrawtransaction", [signed_ab['hex']])['result']
    print(f"Success! Transaction A' -> B' TXID: {txid_ab}\n")
    
    # Mine a block to confirm the transaction from A' to B'
    rpc("generatetoaddress", [1, funding_addr])


    print("--- Task 3: Transaction from B' to C' ---")
    
    unspent_b = rpc("listunspent", [1, 999, [addr_b]])['result'][0]
    
    inputs_b = [{"txid": unspent_b['txid'], "vout": unspent_b['vout']}]
    
    change_address_b = rpc("getrawchangeaddress")['result']
    amount_b = float(unspent_b['amount'])
    outputs_bc = {addr_c: 2.0, change_address_b: round(amount_b - 2.0 - 0.0001, 5)}
    
    # Create the raw transaction
    raw_tx_bc = rpc("createrawtransaction", [inputs_b, outputs_bc])['result']
    
    # Sign the transaction
    signed_bc = rpc("signrawtransactionwithwallet", [raw_tx_bc])['result']
    
    # Decode to analyze the scripts (Unlocking mechanism from B' and Locking mechanism for C')
    decoded_signed_bc = rpc("decoderawtransaction", [signed_bc['hex']])['result']
    
    vin = decoded_signed_bc['vin'][0]
    if 'scriptSig' in vin:
        print(f"[REPORT DATA] Unlocking Script (scriptSig) from B': {vin['scriptSig'].get('hex', '')} / {vin['scriptSig'].get('asm', '')}")
    if 'txinwitness' in vin:
        print(f"[REPORT DATA] Witness Data (txinwitness) from B': {vin['txinwitness']}")
        
    for vout in decoded_signed_bc['vout']:
        addr_list = vout['scriptPubKey'].get('addresses', [])
        addr_v = vout['scriptPubKey'].get('address', "")
        if addr_c in addr_list or addr_v == addr_c:
            print(f"[REPORT DATA] Locking Script for C': {vout['scriptPubKey']['asm']}")
            break

    # Broadcast the transaction
    txid_bc = rpc("sendrawtransaction", [signed_bc['hex']])['result']
    print(f"Success! Transaction B' -> C' TXID: {txid_bc}\n")
    
    # Mine a block to confirm final transaction
    rpc("generatetoaddress", [1, funding_addr])
    print("Final block mined. All tasks complete.")

if __name__ == "__main__":
    main()

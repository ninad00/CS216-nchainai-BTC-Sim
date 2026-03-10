"""
CS 216 - Bitcoin Transaction Lab
Part 1: Legacy Address Transactions (P2PKH)
"""

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json

# RPC CONNECTION SETTINGS
RPC_USER     = "eshwar"
RPC_PASSWORD = "pwd123"
RPC_HOST     = "127.0.0.1"
RPC_PORT     = 18443
WALLET_NAME  = "testwallet"


def connect(wallet=None):
    base = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"
    url  = f"{base}/wallet/{wallet}" if wallet else base
    return AuthServiceProxy(url)


def mine(rpc, blocks=6):
    addr = rpc.getnewaddress()
    rpc.generatetoaddress(blocks, addr)
    print(f"  Mined {blocks} blocks to confirm.")


def main():
    print("=" * 60)
    print("  CS 216 - Part 1: Legacy P2PKH Transactions")
    print("=" * 60)

    # Connect
    rpc = connect(WALLET_NAME)

    # Generate 3 Legacy Addresses
    addr_A = rpc.getnewaddress("A", "legacy")
    addr_B = rpc.getnewaddress("B", "legacy")
    addr_C = rpc.getnewaddress("C", "legacy")
    print(f"\nAddress A: {addr_A}")
    print(f"Address B: {addr_B}")
    print(f"Address C: {addr_C}")

    print("\nMining 101 blocks to fund Address A ...")
    rpc.generatetoaddress(101, addr_A)
    balance = rpc.getbalance()
    print(f"Wallet balance: {balance} BTC")

    print("\n--- Transaction A to B ---")
    fee = 0.0001

    utxos_A = [u for u in rpc.listunspent() if u["address"] == addr_A]
    if not utxos_A:
        raise RuntimeError("No UTXOs found for Address A.")

    utxo = utxos_A[0]
    print(f"Using UTXO: txid={utxo['txid']}  vout={utxo['vout']}  amount={utxo['amount']}")

    amount_AB = 1.0
    change    = round(float(utxo["amount"]) - amount_AB - fee, 8)
    inputs    = [{"txid": utxo["txid"], "vout": utxo["vout"]}]
    outputs   = {addr_B: amount_AB}
    if change > 0:
        outputs[addr_A] = change

    raw_AB  = rpc.createrawtransaction(inputs, outputs)
    dec_AB  = rpc.decoderawtransaction(raw_AB)

    print("\nDecoded raw tx (A to B) - ScriptPubKey for B:")
    for vout in dec_AB["vout"]:
        if vout["scriptPubKey"].get("address", "") == addr_B:
            spk = vout["scriptPubKey"]
            print(f"  asm : {spk['asm']}")
            print(f"  hex : {spk['hex']}")
            print(f"  type: {spk['type']}")

    signed_AB = rpc.signrawtransactionwithwallet(raw_AB)
    assert signed_AB["complete"], "Signing failed!"
    txid_AB = rpc.sendrawtransaction(signed_AB["hex"])
    print(f"\nBroadcast txid (A to B): {txid_AB}")

    mine(rpc)

    print("\n--- Transaction B to C ---")
    utxos_B = [u for u in rpc.listunspent() if u["address"] == addr_B]
    if not utxos_B:
        raise RuntimeError("No UTXOs found for Address B.")

    utxo_B = utxos_B[0]
    print(f"Using UTXO: txid={utxo_B['txid']}  vout={utxo_B['vout']}  amount={utxo_B['amount']}")
    print(f"This UTXO came from txid (A to B): {txid_AB}")
    print(f"UTXO source matches A->B txid: {utxo_B['txid'] == txid_AB}")

    amount_BC  = round(float(utxo_B["amount"]) - fee, 8)
    inputs_BC  = [{"txid": utxo_B["txid"], "vout": utxo_B["vout"]}]
    outputs_BC = {addr_C: amount_BC}

    raw_BC    = rpc.createrawtransaction(inputs_BC, outputs_BC)
    signed_BC = rpc.signrawtransactionwithwallet(raw_BC)
    assert signed_BC["complete"], "Signing failed!"

    dec_BC = rpc.decoderawtransaction(signed_BC["hex"])
    print("\nDecoded signed tx (B to C) - ScriptSig (unlocking script):")
    for vin in dec_BC["vin"]:
        ss = vin.get("scriptSig", {})
        print(f"  asm : {ss.get('asm', '')}")
        print(f"  hex : {ss.get('hex', '')}")

    txid_BC = rpc.sendrawtransaction(signed_BC["hex"])
    print(f"\nBroadcast txid (B to C): {txid_BC}")
    mine(rpc)

    results = {
        "addresses": {"A": addr_A, "B": addr_B, "C": addr_C},
        "tx_A_to_B": {"txid": txid_AB, "decoded": dec_AB},
        "tx_B_to_C": {"txid": txid_BC, "decoded": dec_BC},
        "signed_hex_BC": signed_BC["hex"],
    }
    import decimal
    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                return float(o)
            return super().default(o)

    with open("part1_results.json", "w") as f:
        json.dump(results, f, indent=2, cls=DecimalEncoder)
    print("\nResults saved to part1_results.json")

    # btcdeb command
    print("\n" + "=" * 60)
    print("btcdeb command to validate Part 1:")
    print()
    unlocking_asm = ""
    locking_asm   = ""
    for vin in dec_BC["vin"]:
        unlocking_asm = vin.get("scriptSig", {}).get("asm", "")
    for vout in dec_AB["vout"]:
        if vout["scriptPubKey"].get("address", "") == addr_B:
            locking_asm = vout["scriptPubKey"]["asm"]
    print(f"btcdeb '[{unlocking_asm} {locking_asm}]' --tx={signed_BC['hex']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
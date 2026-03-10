"""
CS 216 - Bitcoin Transaction Lab
Part 2: SegWit Address Transactions (P2SH-P2WPKH)
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
    print("  CS 216 - Part 2: P2SH-SegWit Transactions")
    print("=" * 60)

    # Connect
    rpc = connect(WALLET_NAME)

    # Generate 3 P2SH-SegWit Addresses
    addr_Ap = rpc.getnewaddress("A_prime", "p2sh-segwit")
    addr_Bp = rpc.getnewaddress("B_prime", "p2sh-segwit")
    addr_Cp = rpc.getnewaddress("C_prime", "p2sh-segwit")
    print(f"\nAddress A': {addr_Ap}")
    print(f"Address B': {addr_Bp}")
    print(f"Address C': {addr_Cp}")

    print("\nMining 101 blocks to fund Address A' ...")
    rpc.generatetoaddress(101, addr_Ap)
    balance = rpc.getbalance()
    print(f"Wallet balance: {balance} BTC")

    print("\n--- Transaction A' to B' ---")
    fee = 0.0001

    utxos_Ap = [u for u in rpc.listunspent() if u["address"] == addr_Ap]
    if not utxos_Ap:
        raise RuntimeError("No UTXOs found for Address A'.")

    utxo = utxos_Ap[0]
    print(f"Using UTXO: txid={utxo['txid']}  vout={utxo['vout']}  amount={utxo['amount']}")

    amount_send = 1.0
    change      = round(float(utxo["amount"]) - amount_send - fee, 8)
    inputs      = [{"txid": utxo["txid"], "vout": utxo["vout"]}]
    outputs     = {addr_Bp: amount_send}
    if change > 0:
        outputs[addr_Ap] = change

    raw_AB     = rpc.createrawtransaction(inputs, outputs)
    dec_AB_raw = rpc.decoderawtransaction(raw_AB)

    print("\nDecoded raw tx (A' to B') - ScriptPubKey for B':")
    for vout in dec_AB_raw["vout"]:
        if vout["scriptPubKey"].get("address", "") == addr_Bp:
            spk = vout["scriptPubKey"]
            print(f"  asm : {spk['asm']}")
            print(f"  hex : {spk['hex']}")
            print(f"  type: {spk['type']}")

    signed_AB    = rpc.signrawtransactionwithwallet(raw_AB)
    assert signed_AB["complete"], "Signing failed!"
    dec_AB_signed = rpc.decoderawtransaction(signed_AB["hex"])
    txid_AB      = rpc.sendrawtransaction(signed_AB["hex"])
    print(f"\nBroadcast txid (A' to B'): {txid_AB}")
    mine(rpc)

    print("\n--- Transaction B' to C' ---")
    utxos_Bp = [u for u in rpc.listunspent() if u["address"] == addr_Bp]
    if not utxos_Bp:
        raise RuntimeError("No UTXOs found for Address B'.")

    utxo_B    = utxos_Bp[0]
    print(f"Using UTXO: txid={utxo_B['txid']}  vout={utxo_B['vout']}  amount={utxo_B['amount']}")
    print(f"This UTXO came from txid (A' to B'): {txid_AB}")
    print(f"UTXO source matches A'->B' txid: {utxo_B['txid'] == txid_AB}")

    amount_BC  = round(float(utxo_B["amount"]) - fee, 8)
    inputs_BC  = [{"txid": utxo_B["txid"], "vout": utxo_B["vout"]}]
    outputs_BC = {addr_Cp: amount_BC}

    raw_BC    = rpc.createrawtransaction(inputs_BC, outputs_BC)
    signed_BC = rpc.signrawtransactionwithwallet(raw_BC)
    assert signed_BC["complete"], "Signing failed!"
    dec_BC    = rpc.decoderawtransaction(signed_BC["hex"])

    print("\nDecoded signed tx (B' to C') - ScriptSig + Witness:")
    for vin in dec_BC["vin"]:
        ss = vin.get("scriptSig", {})
        tw = vin.get("txinwitness", [])
        print(f"  ScriptSig asm : {ss.get('asm', '(empty)')}")
        print(f"  ScriptSig hex : {ss.get('hex', '(empty)')}")
        print(f"  Witness       : {tw}")

    txid_BC = rpc.sendrawtransaction(signed_BC["hex"])
    print(f"\nBroadcast txid (B' to C'): {txid_BC}")
    mine(rpc)

    size_AB = len(signed_AB["hex"]) // 2
    size_BC = len(signed_BC["hex"]) // 2
    print(f"\nA'->B' raw size: {size_AB} bytes")
    print(f"B'->C' raw size: {size_BC} bytes")

    results = {
        "addresses": {"A_prime": addr_Ap, "B_prime": addr_Bp, "C_prime": addr_Cp},
        "tx_Ap_to_Bp": {"txid": txid_AB, "decoded_signed": dec_AB_signed},
        "tx_Bp_to_Cp": {"txid": txid_BC, "decoded": dec_BC},
        "signed_hex_BC": signed_BC["hex"],
        "sizes": {"AB_raw_bytes": size_AB, "BC_raw_bytes": size_BC},
    }
    import decimal
    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                return float(o)
            return super().default(o)

    with open("part2_results.json", "w") as f:
        json.dump(results, f, indent=2, cls=DecimalEncoder)
    print("\nResults saved to part2_results.json")

    # btcdeb command
    print("\n" + "=" * 60)
    print("btcdeb command to validate Part 2:")
    print()
    for vin in dec_BC["vin"]:
        tw = vin.get("txinwitness", [])
        print(f"btcdeb '[{' '.join(tw)}]' --tx={signed_BC['hex']}")
    print("=" * 60)


if __name__ == "__main__":
    main()

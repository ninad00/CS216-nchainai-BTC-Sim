"""
CS 216 - Bitcoin Transaction Lab
Part 3: Analysis and Comparison of P2PKH vs P2SH-P2WPKH
"""

from bitcoinrpc.authproxy import AuthServiceProxy
import json

RPC_USER     = "eshwar"
RPC_PASSWORD = "pwd123"
RPC_HOST     = "127.0.0.1"
RPC_PORT     = 18443
WALLET_NAME  = "testwallet"


def connect(wallet=None):
    base = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"
    url  = f"{base}/wallet/{wallet}" if wallet else base
    return AuthServiceProxy(url)


def sep(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main():
    sep("CS 216 - Part 3: Comparative Analysis")

    # Load results
    try:
        with open("part1_results.json") as f:
            p1 = json.load(f)
        with open("part2_results.json") as f:
            p2 = json.load(f)
    except FileNotFoundError as e:
        print(f"Missing file: {e}")
        print("Run part1_legacy_p2pkh.py and part2_segwit_p2sh.py first.")
        return

    rpc = connect(WALLET_NAME)

    txid_AB  = p1["tx_A_to_B"]["txid"]
    txid_BC  = p1["tx_B_to_C"]["txid"]
    txid_ApBp = p2["tx_Ap_to_Bp"]["txid"]
    txid_BpCp = p2["tx_Bp_to_Cp"]["txid"]

    tx_AB   = rpc.decoderawtransaction(rpc.gettransaction(txid_AB)["hex"])
    tx_BC   = rpc.decoderawtransaction(rpc.gettransaction(txid_BC)["hex"])
    tx_ApBp = rpc.decoderawtransaction(rpc.gettransaction(txid_ApBp)["hex"])
    tx_BpCp = rpc.decoderawtransaction(rpc.gettransaction(txid_BpCp)["hex"])

    sep("P2PKH (Legacy) - Transaction A to B")
    print(f"  txid   : {txid_AB}")
    print(f"  size   : {tx_AB.get('size', 'N/A')} bytes")
    print(f"  vsize  : {tx_AB.get('vsize', tx_AB.get('size', 'N/A'))} vbytes")
    print(f"  weight : {tx_AB.get('weight', 'N/A')} WU")
    print("\n  ScriptPubKey (locking script) for output to B:")
    for vout in tx_AB.get("vout", []):
        spk = vout["scriptPubKey"]
        if spk.get("type") == "pubkeyhash":
            print(f"    type : {spk['type']}")
            print(f"    asm  : {spk['asm']}")
            print(f"    hex  : {spk['hex']}")

    sep("P2PKH (Legacy) - Transaction B to C")
    print(f"  txid   : {txid_BC}")
    print(f"  size   : {tx_BC.get('size', 'N/A')} bytes")
    print(f"  vsize  : {tx_BC.get('vsize', tx_BC.get('size', 'N/A'))} vbytes")
    print(f"  weight : {tx_BC.get('weight', 'N/A')} WU")
    print("\n  ScriptSig (unlocking script):")
    for vin in tx_BC.get("vin", []):
        ss = vin.get("scriptSig", {})
        print(f"    asm  : {ss.get('asm', '')}")
        print(f"    hex  : {ss.get('hex', '')}")

    sep("P2SH-P2WPKH (SegWit) - Transaction A' to B'")
    print(f"  txid   : {txid_ApBp}")
    print(f"  size   : {tx_ApBp.get('size', 'N/A')} bytes")
    print(f"  vsize  : {tx_ApBp.get('vsize', tx_ApBp.get('size', 'N/A'))} vbytes")
    print(f"  weight : {tx_ApBp.get('weight', 'N/A')} WU")
    print("\n  ScriptPubKey (locking script) for output to B':")
    for vout in tx_ApBp.get("vout", []):
        spk = vout["scriptPubKey"]
        if spk.get("type") == "scripthash":
            print(f"    type : {spk['type']}")
            print(f"    asm  : {spk['asm']}")
            print(f"    hex  : {spk['hex']}")

    sep("P2SH-P2WPKH (SegWit) - Transaction B' to C'")
    print(f"  txid   : {txid_BpCp}")
    print(f"  size   : {tx_BpCp.get('size', 'N/A')} bytes")
    print(f"  vsize  : {tx_BpCp.get('vsize', tx_BpCp.get('size', 'N/A'))} vbytes")
    print(f"  weight : {tx_BpCp.get('weight', 'N/A')} WU")
    print("\n  ScriptSig + Witness:")
    for vin in tx_BpCp.get("vin", []):
        ss = vin.get("scriptSig", {})
        tw = vin.get("txinwitness", [])
        print(f"    ScriptSig asm : {ss.get('asm', '(empty)')}")
        print(f"    Witness items : {tw}")

    sep("SUMMARY COMPARISON TABLE")
    print(f"  {'Metric':<20} {'P2PKH A->B':<16} {'P2PKH B->C':<16} {'SegWit A->B':<16} {'SegWit B->C':<16}")
    print(f"  {'-'*80}")

    def val(tx, *keys):
        for k in keys:
            if k in tx:
                return str(tx[k])
        return "N/A"

    rows = [
        ("Size (bytes)",  val(tx_AB,"size"),  val(tx_BC,"size"),  val(tx_ApBp,"size"),  val(tx_BpCp,"size")),
        ("vSize (vbytes)", val(tx_AB,"vsize","size"), val(tx_BC,"vsize","size"), val(tx_ApBp,"vsize","size"), val(tx_BpCp,"vsize","size")),
        ("Weight (WU)",   val(tx_AB,"weight"), val(tx_BC,"weight"), val(tx_ApBp,"weight"), val(tx_BpCp,"weight")),
        ("Script type",   "pubkeyhash", "pubkeyhash", "scripthash", "scripthash"),
        ("Has witness",   "No", "No", "No", "Yes"),
    ]
    for row in rows:
        print(f"  {row[0]:<20} {row[1]:<16} {row[2]:<16} {row[3]:<16} {row[4]:<16}")

    print("Part 3 analysis complete.")


if __name__ == "__main__":
    main()

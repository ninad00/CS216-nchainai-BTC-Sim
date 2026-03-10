# CS 216 – Bitcoin Transaction Lab (Assignment 2)

## Team Members

| Name | Roll Number |
|------|-------------|
| Ninad Kulkarni | 240002032 |
| Divyae Arya | 240001027 |
| Eshwar Chandra Reddy | 240003029 |
| Arnav Nitin Birari | 240041004 |


---

## Overview

This repository contains the implementation for CS 216 Programming Assignment 2: **Bitcoin Transaction Lab — From Command Line to Programming**.

- **Part 1** — Legacy P2PKH (Pay-to-Public-Key-Hash) transactions: A → B → C
- **Part 2** — P2SH-P2WPKH SegWit transactions: A' → B' → C'
- **Part 3** — Comparative size and script analysis of both transaction types

All transactions were executed on a local Bitcoin **regtest** network using Bitcoin Core v30.2.0, driven by Python scripts via JSON-RPC.

---

## Prerequisites

### 1. Bitcoin Core

Download and install from https://bitcoincore.org/en/download/

**Tested version:** Bitcoin Core v30.2.0 on Windows 11

After installation, `bitcoind.exe` and `bitcoin-cli.exe` will be at:
```
C:\Program Files\Bitcoin\daemon\
```

---

### 2. bitcoin.conf

Bitcoin Core on Windows reads its config from:
```
C:\Users\<YourUsername>\AppData\Roaming\Bitcoin\bitcoin.conf
```

If this file does not exist, create it via PowerShell:
```powershell
New-Item -ItemType Directory -Path "$env:APPDATA\Bitcoin" -Force
Set-Content -Path "$env:APPDATA\Bitcoin\bitcoin.conf" -Value "regtest=1
server=1

[regtest]
rpcuser=your_rpc_user
rpcpassword=your_rpc_password
rpcallowip=127.0.0.1
rpcport=18443
paytxfee=0.0001
fallbackfee=0.0002
mintxfee=0.00001
txconfirmtarget=6"
```

> **Important:** Settings like `rpcport` must be under the `[regtest]` section header in Bitcoin Core 0.21+. Placing them at the top level causes the error:
> `Config setting for -rpcport only applied on regtest network when in [regtest] section.`

---

### 3. Starting bitcoind on Windows

The `-daemon` flag is **not supported on Windows**. Run bitcoind in a dedicated PowerShell window that stays open:

```powershell
& "C:\Program Files\Bitcoin\daemon\bitcoind.exe" -regtest
```

Or run it minimized in the background:
```powershell
Start-Process -WindowStyle Minimized "C:\Program Files\Bitcoin\daemon\bitcoind.exe" "-regtest"
```

Verify it is running in a second PowerShell window:
```powershell
& "C:\Program Files\Bitcoin\daemon\bitcoin-cli.exe" -regtest -rpcuser=your_rpc_user -rpcpassword=your_rpc_password getblockchaininfo
```

You should see `"chain": "regtest"` in the output.

To stop bitcoind when done:
```powershell
& "C:\Program Files\Bitcoin\daemon\bitcoin-cli.exe" -regtest -rpcuser=your_rpc_user -rpcpassword=your_rpc_password stop
```

---

### 4. Python Dependencies

Requires Python 3.8+.

```powershell
pip install python-bitcoinrpc
```

---

### 5. btcdeb – Bitcoin Script Debugger

btcdeb is **not available via apt** on Ubuntu 24.04 (Noble). It must be built from source.

#### Why special compile flags are needed

The default build of btcdeb 5.0.24 on WSL2 (Ubuntu) crashes immediately with:
```
*** buffer overflow detected ***: terminated
Aborted (core dumped)
```

This is caused by two issues:
- **`_FORTIFY_SOURCE`** — a glibc memory-hardening macro that incorrectly triggers abort signals on valid btcdeb stack operations inside WSL2
- **Architecture-specific ASM optimizations** — incompatible with the WSL2 execution environment

#### Solution — build with protection flags disabled

Open WSL (Ubuntu) and run:

```bash
# Install build dependencies
sudo apt update
sudo apt install -y git build-essential libtool autotools-dev automake pkg-config libssl-dev

# Clone btcdeb
git clone https://github.com/bitcoin-core/btcdeb.git
cd btcdeb

# Configure with fortify and asm disabled
./autogen.sh
./configure CXXFLAGS="-O0 -U_FORTIFY_SOURCE" CFLAGS="-O0 -U_FORTIFY_SOURCE" --disable-asm

# Build
make
```

Verify it works:
```bash
./btcdeb '[OP_1 OP_1 OP_ADD OP_2 OP_EQUAL]'
```
Type `step` 4 times — you should see the stack build up without any crash.

#### Accessing your Assignment folder from WSL

Your Windows files are accessible from WSL under `/mnt/c/`. Navigate to the assignment folder:
```bash
cd "/mnt/c/Users/<YourUsername>/path/to/Assignment 2/btcdeb"
```

---

## Configuration – Update Credentials in Scripts

Before running, open each Python script and update the RPC credentials at the top to match your `bitcoin.conf`:

```python
RPC_USER     = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_HOST     = "127.0.0.1"
RPC_PORT     = 18443
```

Files to update:
- `part1_legacy_p2pkh.py`
- `part2_segwit_p2sh.py`
- `part3_comparison.py`

---

## Running the Programs

Make sure bitcoind is running before executing any script.

Navigate to your assignment folder in PowerShell:
```powershell
cd "path\to\Assignment 2"
```

### Step 1 — Part 1: Legacy P2PKH
```powershell
python part1_legacy_p2pkh.py
```

This will:
- Connect to bitcoind and load wallet `testwallet`
- Generate legacy addresses A, B, C
- Mine 101 blocks to fund Address A
- Execute transaction A → B (creates locking script / ScriptPubKey)
- Execute transaction B → C (creates unlocking script / ScriptSig)
- Save all results to `part1_results.json`
- Print the btcdeb validation command at the end

Takes approximately 1–2 minutes due to mining.

### Step 2 — Part 2: P2SH-SegWit
```powershell
python part2_segwit_p2sh.py
```

This will:
- Generate P2SH-SegWit addresses A', B', C'
- Mine 101 blocks to fund Address A'
- Execute transaction A' → B' and B' → C'
- Save results to `part2_results.json`
- Print the btcdeb validation command at the end

### Step 3 — Part 3: Comparison Analysis
```powershell
python part3_comparison.py
```

Reads `part1_results.json` and `part2_results.json` and prints a side-by-side comparison table of transaction sizes, weights, and vbytes.

> **Note:** Run Parts 1 and 2 before Part 3, otherwise it will fail with a missing file error.

---

## Script Validation with btcdeb

### Part 1 — P2PKH Validation

In WSL, navigate to the btcdeb folder and run:

```bash
./btcdeb '[<signature> <pubkey> OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG]'
```

Use the data from Part 1's output. Type `step` 7 times to step through each operation.

**Note on OP_CHECKSIG:** btcdeb will show `error: Signature is found in scriptCode` at the OP_CHECKSIG step when the `--tx` flag is not provided. This is a known btcdeb 5.0.24 limitation — without full transaction context it cannot perform ECDSA verification. However, `--tx` triggers the buffer overflow bug on WSL2. The transaction's validity is confirmed by:
1. `signrawtransactionwithwallet` returning `"complete": true`
2. `sendrawtransaction` accepting and broadcasting without error
3. The transaction being successfully mined into a block by Bitcoin Core

All steps up to and including OP_EQUALVERIFY execute correctly and return TRUE (`PUSH stack 01`), which confirms the public key hash matches.

### Part 2 — SegWit Validation

```bash
./btcdeb '[<witness_sig> <witness_pubkey> OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG]'
```

Use the data from Part 2's output. Type `step` 7 times.

For P2SH-P2WPKH, the witness stack contains only `<sig>` and `<pubkey>` with no OP codes — the OP codes (OP_DUP OP_HASH160 etc.) are implied by the witness program and executed internally by the Bitcoin node. This is normal SegWit behaviour.

---

## Decoding Transactions

To decode any transaction by TXID using bitcoin-cli:

```powershell
$hex = (& "C:\Program Files\Bitcoin\daemon\bitcoin-cli.exe" -regtest -rpcuser=your_rpc_user -rpcpassword=your_rpc_password -rpcwallet=testwallet gettransaction "YOUR_TXID" | python -c "import sys,json; print(json.load(sys.stdin)['hex'])")
& "C:\Program Files\Bitcoin\daemon\bitcoin-cli.exe" -regtest -rpcuser=your_rpc_user -rpcpassword=your_rpc_password decoderawtransaction $hex
```

---

## Repository Structure

```
.
├── part1_legacy_p2pkh.py     # Part 1: P2PKH transactions (A→B→C)
├── part2_segwit_p2sh.py      # Part 2: P2SH-SegWit transactions (A'→B'→C')
├── part3_comparison.py       # Part 3: Comparative size analysis
├── part1_results.json        # Auto-generated after running Part 1
├── part2_results.json        # Auto-generated after running Part 2
├── report.pdf                # Assignment report
└── README.md                 # This file
```

> `part1_results.json` and `part2_results.json` are generated automatically when you run the scripts. Do not edit them manually.

---

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `'bitcoind' is not recognized` | bitcoind not in PATH | Use full path: `& "C:\Program Files\Bitcoin\daemon\bitcoind.exe"` |
| `-daemon is not supported` | Windows doesn't support daemon mode | Run without `-daemon`, keep window open |
| `Authorization failed` | Wrong credentials or missing `[regtest]` section in conf | Add `[regtest]` section header above rpcuser/rpcpassword |
| `Config setting for -rpcport only applied on regtest network when in [regtest] section` | rpcport placed outside section | Move all RPC settings under `[regtest]` header |
| `EOF reached / Could not connect` | bitcoind not running or still starting | Wait 10 seconds after starting, then retry |
| `TypeError: unsupported operand type decimal.Decimal` | RPC returns Decimal type | Wrap with `float()`: `float(utxo["amount"])` |
| `Object of type Decimal is not JSON serializable` | Decimal in json.dump | Use custom encoder with `cls=DecimalEncoder` |
| `btcdeb: buffer overflow detected` | `_FORTIFY_SOURCE` + ASM flags on WSL2 | Recompile with `CXXFLAGS="-O0 -U_FORTIFY_SOURCE" --disable-asm` |
| `Unable to locate package btcdeb` | Not in apt on Ubuntu 24.04 | Build from source (see btcdeb section above) |
| `No such mempool transaction` | Using `getrawtransaction` for wallet tx | Use `gettransaction` instead |

---

## References

- [Learning Bitcoin from the Command Line – Chapter 18](https://github.com/BlockchainCommons/Learning-Bitcoin-from-the-Command-Line/blob/master/18_0_Talking_to_Bitcoind_Other.md)
- [BIP 16: Pay to Script Hash](https://github.com/bitcoin/bips/blob/master/bip-0016.mediawiki)
- [BIP 141: Segregated Witness](https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki)
- [btcdeb – Bitcoin Script Debugger](https://github.com/bitcoin-core/btcdeb)
- [python-bitcoinrpc](https://github.com/jgarzik/python-bitcoinrpc)
- [Bitcoin Core Documentation](https://bitcoincore.org/en/doc/)

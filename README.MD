(This was done on windows using docker)
## Steps

### 1. Run docker image

```docker rm -f bitcoind; docker run -d --name bitcoind -p 18443:18443 -v "${PWD}/bitcoin.conf:/home/bitcoin/.bitcoin/bitcoin.conf" ruimarinho/bitcoin-core -regtest```

### 2. Run Legacy (P2PKH)
```python .\legacy_orchestrator.py```

### 3. Run SegWit

Create PowerShell alias for future use
```function bcli { docker exec bitcoind bitcoin-cli -regtest -rpcuser=nChain -rpcpassword=pass123 $args }```

### 2. Create Wallet
```bcli createwallet "nChainWallet"```

### 3. Generate and fund address A
```$ADDR_A = bcli getnewaddress "AddressA" "legacy"```
```bcli generatetoaddress 101 $ADDR_A```
```bcli getbalance```







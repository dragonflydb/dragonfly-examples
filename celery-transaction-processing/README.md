```bash
pip install -r requirements.txt
```

```bash
uvicorn main:app --reload
```

```bash
celery -A tasks worker --loglevel=INFO
```

- A Web3 node provider URL (i.e., Infura) is required to interact with the Ethereum network.
  The URL should be set as the `DF_WEB3_PROVIDER_URI` environment variable.
  **NOTE: To test the application locally, you should use a testnet (i.e., Sepolia) node provider URL.**
- An Ethereum wallet private key is required to sign transactions.
  The private key should be set as the `DF_SYSTEM_ACCOUNT_PRIVATE_KEY` environment variable.
  **NOTE: The private key should be kept secret, ideally encrypted, and NOT shared with others.**
  **Do NOT use a wallet with real funds for testing purposes.**

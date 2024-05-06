```bash
celery -A tasks worker --loglevel=INFO
```

- A Web3 node provider URL (i.e., Infura) is required to interact with the Ethereum network. The URL should be set in
  the `WEB3_PROVIDER_URI` environment variable.

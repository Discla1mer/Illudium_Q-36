# Use the section below in Claude or Claude Code to help you set up the Hashi Corp Vault.

```
I need help setting up HashiCorp Vault locally to manage an Anthropic API key securely. I am on [Mac/Windows/Linux]. Please walk me through:

Installing Vault
Starting a local dev server
Enabling the KV v2 secrets engine
Storing my Anthropic API key at the path secret/anthropic/api_key with the field name value
Verifying the secret is stored correctly

After setup, confirm the environment variables I need to export so this Python script can authenticate and retrieve the key at runtime: VAULT_ADDR, VAULT_TOKEN, and USE_VAULT=true.
```
# Important
The prompt will help you, but I strongly recommend using the HashiCorp docs with Claude for the following reasons
1. Tokens are not free and you using it for code can use more from what I have experienced.
2. Claude tells you to verify... take that advice
3. There are assumptions that Claude and HashCorp make. Using the combonation will save you time, tokens, and anger.

# Below is the Linux instruction - I'm bias towards Linux
https://developer.hashicorp.com/vault/install#linux

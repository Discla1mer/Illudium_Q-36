# Illudium Q-36 Explosive Space Modulator Intelligence Briefing Generator

A Python tool that transforms raw threat intelligence — CVEs, IOC dumps, threat reports — into structured executive briefings using the Anthropic Claude API.

Built by Me... as a practical demonstration of Claude API integration for enterprise security workflows.

---

## What It Does

Give you the text that you need for executive briefings. 

Paste any raw threat intel and receive a structured briefing covering:

- **Threat Actor / Attribution** — who is behind it and confidence level
- **MITRE ATT&CK Mapping** — relevant tactics and techniques with IDs
- **COMING SOON** - Alignment with MITRE ATLAS
- **Recommended Remediation Steps** — prioritized, actionable, immediate actions first
- **Executive Summary** — two to three sentences for leadership consumption

Output is saved as a timestamped Markdown file in a `briefings/` folder.

---
## What It Does NOT Do
- **Your taxes**
- **Tell you what in your network is impacted.** - The assumption is that you know what this connects to and are not trying to leak that to the world.

---

## Why This Matters for Enterprise

This pattern — raw data in, structured intelligence out — is one of the most common Claude integration requests from enterprise security teams. It demonstrates:

- How to use Claude as an analytical layer on top of existing data feeds
- Prompt engineering for consistent, structured output
- A simple architecture that can be extended to ingest from SIEM APIs, threat feeds, or ticketing systems

---

## Setup

**Requirements**

- Python 3.8+
- An Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))

**Install dependencies**

```bash
pip install anthropic python-dotenv
```

For HashiCorp Vault support (recommended for production):

```bash
pip install hvac
```

---

**Option 1: .env file (local development)**

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=
```
- Put your API Key behing the = It annoys me that I have to highlight that "place_key_here" text so I didn't put it here.


**Never** commit your `.env` file to Github. I've included `.env.example` for reference.

This means, put `.env` (and any local `.env.*` files) in the `.gitignore` file, but keep `.env.example` tracked.
These added instructions are not for people that are using Github frequently. These notes are for the person just starting. 


---

**Option 2: HashiCorp Vault (enterprise / production)**

This is the recommended pattern for any team environment. Vault centralises secrets management, enforces access policies, and provides a full audit trail — no API keys sitting in files on developer machines.

Store your Anthropic API key in Vault:

```bash
vault kv put secret/anthropic/api_key value=""
# Put your key in between the double quotes. I didn't put a space there because then you'd have to highlight and that's annoying.
```

Set the following environment variables before running:

```bash
export VAULT_ADDR=https://your-vault-instance:8200
export VAULT_TOKEN=
export USE_VAULT=true
# 1. I left the "VAULT_ADDR=" the way it is because you may be in an enterprise and localhost or 127.0.0.1 is not going to work.
# --- again... this is a note for the people just starting.
# As stated before please place your token, and vault details after the double quotes.
```

The script authenticates to Vault, retrieves the key at runtime, and never writes it to disk.

---

## Usage

```bash
python illudumQ36.py
```

Paste your raw threat intelligence when prompted, then type `END` on a new line to submit.

**Example input:**

```
CVE-2024-1234: Remote code execution in Apache HTTP Server 2.4.x
Observed IOCs: 185.234.xx.xx, hash: a1b2c3d4...
TTPs observed: spearphishing, lateral movement via SMB, credential dumping
Attribution: suspected APT29 based on tooling overlap
```

**Example output file:** `briefings/briefing_20250223_143022.md`

---

## Architecture

```
Raw Intel (stdin)
      |
      v
Claude API (claude-opus-4-6)
      |
      v
Structured Briefing (Markdown)
      |
      v
./briefings/briefing_[timestamp].md
```

---

## Extending This
What is being suggested below is not a quick thing to do. It's not 100% required either. If you'd like a nice little frontend this is a fun side quest.

Some next steps for enterprise deployment:
- Connect input to a SIEM API (Splunk, Elastic) to pull alerts automatically
- Add a web front end using Flask
- Integrate with a ticketing system to auto-create incidents
- Add a vector database to compare new threats against historical briefings (RAG pattern)

---

## Author

Built this to demonstrate practical Claude API integration for enterprise security use cases, maybe. The reality is that it's a thrown together thing that needs you to commit your tokens, and API keys. I'm not responsible for your actions, environment, or emotional well-being. Use this as a thing you want to tinker with because you're bored, not because you're looking to "save the cheerleader."  

Direct from me to you:
I do not intend to sound snarky in the comments above. I am hoping that you can read that with a bit of humor because it's meant to be light hearted. 
I know how many assumptions can be made and while I was learning those assumptions really messed me up. I put those notes in place to actually be a little human.
If you don't get it right away, that's okay, just use Claude, or better yet, use Claude Code -- you will need to have a paid account though. When you do that you'll
see that they do something different. No API key exchange, just authentication through your existing account. That's actually a bit more.... a lot more efficient, but they 
are serving a public user. This is for making a little more sense of your threats. If you never use it at least you now have a different skill and a new thing to say you
built! :) 

---

## License

MIT

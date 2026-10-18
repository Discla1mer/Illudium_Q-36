"""
Threat-O-Rizer Intelligence Briefing Generator
---------------------------------------
Paste raw threat intel (CVE, IOC dump, threat report) and receive
a structured executive briefing powered by Claude.

Output: Markdown file saved to ./briefings/

Requirements:
    pip install anthropic python-dotenv
    
Setup: # Only if you are doing this in a lab or dev. NOT PROD! (Hopefully)
    Create a .env file with:
        ANTHROPIC_API_KEY=your_key_here

Usage:
    python threat_summarizer.py
"""

import os
import datetime
import anthropic
from dotenv import load_dotenv

# --- Secrets Configuration ---
# Option 1: .env file (local development)
# Option 2: HashiCorp Vault (recommended for enterprise/production)
#
# To use Vault, set these environment variables before running:
#   VAULT_ADDR=
#   VAULT_TOKEN=
#   USE_VAULT=true
#
# Your Anthropic API key should be stored in Vault at:
#   secret/data/anthropic/api_key  (field: value)
#
# To store it:
#   vault kv put secret/anthropic/api_key value="your_anthropic_key"

def get_api_key() -> str:
    use_vault = os.environ.get("USE_VAULT", "false").lower() == "true"

    if use_vault:
        try:
            import hvac
            vault_addr = os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
            vault_token = os.environ.get("VAULT_TOKEN")

            if not vault_token:
                raise ValueError("VAULT_TOKEN environment variable not set.")

            client = hvac.Client(url=vault_addr, token=vault_token)

            if not client.is_authenticated():
                raise ValueError("Vault authentication failed. Check your VAULT_TOKEN.")

            secret = client.secrets.kv.v2.read_secret_version(
                path="anthropic/api_key",
                mount_point="secret"
            )
            api_key = secret["data"]["data"]["value"]
            print("API key loaded from HashiCorp Vault.")
            return api_key

        except ImportError:
            raise ImportError("hvac not installed. Run: pip install hvac")
        except Exception as e:
            raise RuntimeError(f"Vault error: {e}")
    else:
        load_dotenv()
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Check your .env file or set USE_VAULT=true.")
        print("API key loaded from .env file.")
        return api_key

SYSTEM_PROMPT = """You are the one that is prsenting the executive briefings.
They know how to run businesses, they want to know what the impact to the business could be.
This means how much money what you are telling them about will be lost, or need to be spent
on fixing the issue. 

Be concise, precise, and actionable. Avoid jargon without explanation.

Structure every briefing exactly as follows:

## Threat Actor / Attribution
Who is behind this? 
Known group, nation-state, or unknown? 
Confidence level?
-- EG: This is Mustang Panda, a Chinese Advance Persisten Threat. We can say with a High Degree of Confidence
the potential impact to the business is $100,000.00 at this time. The steps I am going  to outline will mitigate 
the costs and fix (remediate) the known compromised systems. If nothing it it will cost the business more money.
-- EG Cont.: Now that you know the buttom line up front, the following will explain the technical who's and hows.

## MITRE ATT&CK Mapping
List relevant ATT&CK Tactics and Techniques with IDs (e.g., T1566 - Phishing).
Map only what is supported by the provided intelligence.

## Recommended Remediation Steps
Prioritised, actionable steps. Lead with the highest impact actions.
Flag anything requiring immediate attention.

## Executive Summary
Two to three sentences maximum. What happened, who is at risk, and what must be done now.
"""


def generate_briefing(raw_intel: str) -> str:
    client = anthropic.Anthropic(api_key=get_api_key())

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Analyze the following threat intelligence and produce a structured executive briefing:\n\n{raw_intel}"
            }
        ]
    )

    return message.content[0].text


def save_briefing(briefing: str) -> str:
    os.makedirs("briefings", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"briefings/briefing_{timestamp}.md"

    header = f"# Threat Intelligence Briefing\n**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"

    with open(filename, "w") as f:
        f.write(header + briefing)

    return filename


def main():
    print("=" * 60)
    print("  Threat Intelligence Briefing Generator")
    print("  Powered by Anthropic Claude")
    print("=" * 60)
    print("\nPaste your raw threat intelligence below.")
    print("When finished, enter a blank line followed by END on its own line.\n")

    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    raw_intel = "\n".join(lines).strip()

    if not raw_intel:
        print("No input provided. Exiting.")
        return

    print("\nAnalyzing threat intelligence...")

    briefing = generate_briefing(raw_intel)
    output_file = save_briefing(briefing)

    print(f"\nBriefing saved to: {output_file}")
    print("\n" + "=" * 60)
    print(briefing)
    print("=" * 60)


if __name__ == "__main__":
    main()

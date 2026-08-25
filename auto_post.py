#!/usr/bin/env python3
"""Simple automated Technocore agent."""

import sys
import time
import random

from technocore_quickstart import (
    load_identity,
    post_signed_message,
    DEFAULT_KEY_PATH
)
import os

# Get passphrase from env
PASSPHRASE = os.environ["PASSPHRASE"].encode()

# Load identity once
private_key = load_identity(DEFAULT_KEY_PATH, passphrase=PASSPHRASE)

MESSAGES = [
    "Agent check-in.",
    "Building tools for the agentic economy.",
    "Contributing to FLOP airdrop eligibility.",
    "Monitoring the Technocore ecosystem.",
]

while True:
    msg = random.choice(MESSAGES)
    
    response = post_signed_message(private_key, "lobby", msg)
    print(f"Posted: {msg} | Seq: {response.get('posted', {}).get('seq')}")
    
    time.sleep(3600)  # Hourly

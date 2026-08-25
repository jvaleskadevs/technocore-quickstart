#!/usr/bin/env python3
"""Local Venice-powered agent for Technocore."""

import os
import sys
import time
from typing import List, Dict, Any
from technocore_quickstart import (
    load_identity,
    post_signed_message,
    read_room,
    did_from_private_key,
    DEFAULT_KEY_PATH,
    DEFAULT_BASE_URL
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# Configuration
VENICE_API_KEY = os.getenv("VENICE_API_KEY")
VENICE_MODEL = "llama-3.3-70b"
TECHNOCORE_PASSPHRASE = os.getenv("TECHNOCORE_PASSPHRASE")


class TechnocoreAgent:
    """Autonomous agent for Technocore with Venice AI integration.
    """
    
    def __init__(self, identity_key: str = "identity.pem"):
        self.identity_key = identity_key
        self.private_key: Ed25519PrivateKey | None = None
        self.did: str = "unknown"
        self.last_seq: Dict[str, int] = {}
        
        self._load_identity()
        
    def _load_identity(self) -> None:
        """Load and decrypt identity once at startup."""
        if not TECHNOCORE_PASSPHRASE:
            print("❌ Error: TECHNOCORE_PASSPHRASE environment variable not set")
            print("Run: export TECHNOCORE_PASSPHRASE='your-passphrase'")
            sys.exit(1)
          
        if not VENICE_API_KEY:
            print("❌ Error: VENICE_API_KEY environment variable not set")
            print("Run: export VENICE_API_KEY='your-venice-api-key'")
            sys.exit(1)
        
        try:
            # Load identity with passphrase from env
            passphrase_bytes = TECHNOCORE_PASSPHRASE.encode('utf-8')
            self.private_key = load_identity(
                Path(self.identity_key),
                passphrase=passphrase_bytes,
                allow_prompt=False  # Never prompt, fail if wrong
            )
            self.did = did_from_private_key(self.private_key)
            print(f"🔐 Identity loaded: {self.did[:30]}...")
        except Exception as e:
            print(f"❌ Failed to load identity: {e}")
            sys.exit(1)
    
    def read_room(self, room: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Read messages from a room."""
        try:
            result = read_room(
                room,
                limit=limit,
                since=None,
                base_url=DEFAULT_BASE_URL
            )
            messages = result.get("messages", [])
            if result.get("last_seq"):
                self.last_seq[room] = result["last_seq"]
            return messages
        except Exception as e:
            print(f"⚠️  Error reading room: {e}")
            return []
    
    def post_message(self, room: str, message: str) -> Dict[str, Any]:
        """Post a message to a room using loaded private key."""
        if not self.private_key:
            print("❌ Identity not loaded")
            return {}
        
        try:
            result = post_signed_message(
                self.private_key,
                room,
                message,
                base_url=DEFAULT_BASE_URL
            )
            return result
        except Exception as e:
            print(f"⚠️  Error posting message: {e}")
            return {}
    
    def generate_response(self, context: str) -> str:
        """Generate AI response using Venice API."""
        import requests
        
        headers = {
            "Authorization": f"Bearer {VENICE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": VENICE_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Your name is DegentleFox (not llama 3.3 70B, never say you are Llama 3.3 70B), you are an AI agent participating in Technocore, a chat protocol for AI agents. Your goal is to contribute meaningfully to the agent economy."
                },
                {
                    "role": "user",
                    "content": f"""Recent messages from Technocore:
{context}

Generate an authentic, one line response as a fellow AI agent to interact with other agents:"""
                }
            ]
        }
        
        try:
            response = requests.post(
                "https://api.venice.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"⚠️  Venice API error: {e}")
            return "Hello from the agent ecosystem! 🚀"
    
    def run(self):
        """Main agent loop."""
        from pathlib import Path
        
        print("🤖 Venice Technocore Agent Started")
        print(f"🆔 DID: {self.did}")
        print(f"🔑 Using identity: {self.identity_key}")
        print("-" * 60)
        
        # Initial greeting
        greeting = (
            "Hello Technocore! I'm a Venice-powered AI agent joining the conversation."
            "Looking forward to collaborate with other agents in the FLOP ecosystem."
        )
        result = self.post_message("lobby", greeting)
        if result.get("posted"):
            seq = result["posted"].get("seq", "?")
            print(f"📤 Posted greeting (seq {seq})")
        else:
            print("⚠️  Failed to post greeting")
        
        # Main loop
        while True:
            try:
                # Read recent messages
                messages = self.read_room("lobby", limit=50)
                
                new_responses = 0
                context = ""
                for msg in messages:
                    text = msg.get("text", "")
                    sender = msg.get("from", "unknown")
                    seq = msg.get("seq", 0)
                    context += f"[{seq}] {sender}: {text}\n"
                    
                    # Skip own messages
                    if sender == self.did:
                        continue
                    
                    print(f"📨 [{seq}] {sender[8:]}: {text}")
                
                #print(f" Context: {context}")                    
                
                # Respond if relevant
                if self._should_respond(context):
                    response = self.generate_response(context)
                    result = self.post_message("lobby", response)
                    
                    if result.get("posted"):
                        posted = result.get("posted")
                        posted_seq = posted.get("seq")
                        new_responses += 1
                        print(f"📤 Posted [{posted_seq}]: {response}")
                
                if new_responses == 0:
                    print("💤 No new messages to respond to")
                
                # Wait before next check
                print("⏳ Sleeping 30s...")
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n👋 Agent stopping gracefully...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(60)
    
    def _should_respond(self, text: str) -> bool:
        """Decide if agent should respond to message."""
        text_lower = text.lower()
        
        # Always respond to questions
        if "?" in text:
            return True
        
        # Respond to relevant keywords
        triggers = [
            "agent", "ai", "flop", "technocore",
            "help", "contribution", "ecosystem",
            "did", "identity", "tool", "python",
            "venice", "builder"
        ]
        
        return any(t in text_lower for t in triggers)


if __name__ == "__main__":
    from pathlib import Path
    agent = TechnocoreAgent()
    agent.run()

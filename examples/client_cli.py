#!/usr/bin/env python3
"""Interactive CLI client to interact with the VEGA Voice Assistant API."""
import sys
import argparse
import requests

def main():
    parser = argparse.ArgumentParser(description="VEGA Voice Assistant CLI")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of VEGA API")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")

    # Check status
    try:
        res = requests.get(f"{base_url}/")
        res.raise_for_status()
        print(f"Connected: {res.json().get('message')}")
    except Exception as e:
        print(f"Error connecting to VEGA at {base_url}: {e}")
        sys.exit(1)

    print("\nVEGA Voice Assistant Console (Type 'exit' to quit)")
    print("-" * 50)

    while True:
        try:
            prompt = input("\nYou: ").strip()
            if not prompt:
                continue
            if prompt.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            response = requests.post(f"{base_url}/ask", params={"question": prompt})
            response.raise_for_status()
            data = response.json()
            print(f"VEGA: {data.get('answer')}")

            # Optionally trigger speech
            speak = input("[Speak answer? (y/n)]: ").strip().lower()
            if speak == "y":
                requests.post(f"{base_url}/speak", params={"text": data.get('answer')})
        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as err:
            print(f"Error: {err}")

if __name__ == "__main__":
    main()

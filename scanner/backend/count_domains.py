import asyncio
from ha_client import HomeAssistantClient
import os

# Mock ENV if needed
if not os.getenv("HA_URL"):
    # Load from .env if possible or hardcode for test
    pass

async def main():
    client = HomeAssistantClient()
    if not client.enabled:
        print("HA Client disabled (no token?)")
        return

    print("Fetching states...")
    states = await client.get_states()
    
    domains = {}
    total = 0
    
    targets = ['light', 'switch', 'sensor', 'binary_sensor', 'media_player', 'climate', 'camera', 'lock', 'vacuum']
    
    for s in states:
        d = s['entity_id'].split('.')[0]
        if d not in domains: domains[d] = 0
        domains[d] += 1
        total += 1
        
    print(f"Total Entities: {total}")
    print("Counts by domain:")
    for d, c in sorted(domains.items(), key=lambda x: x[1], reverse=True):
        print(f"  {d}: {c}")

    # Count "Virtual" candidates (not in existing IP index)
    # We need to run index logic
    client._index_devices(states)
    mapped_count = len(client.ip_index)
    print(f"IP Mapped Devices: {mapped_count}")
    
    virtuals = 0
    for s in states:
        d = s['entity_id'].split('.')[0]
        if d in ['light', 'switch', 'climate', 'lock', 'vacuum']:
             # Check if mapped
             is_mapped = False
             # Difficult to check reverse mapping cleanly without iterating ip_index
             # But let's just assume we want everything in these domains
             virtuals += 1
    
    print(f"Potential Virtual Devices (Light/Switch/Climate...): {virtuals}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())

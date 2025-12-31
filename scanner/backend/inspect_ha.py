import asyncio
import json
from ha_client import ha_client

async def main():
    if not ha_client.enabled:
        print("HA Client disabled")
        return

    states = await ha_client.get_states()
    
    # Dump first 5 entities of different domains to see structure
    examples = {}
    for s in states:
        d = s['entity_id'].split('.')[0]
        if d not in examples:
            examples[d] = s
            if len(examples) > 5: break
            
    print(json.dumps(examples, indent=2))

if __name__ == "__main__":
    asyncio.run(main())

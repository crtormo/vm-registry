import asyncio
import json
import os
from datetime import datetime
from ha_client import ha_client

OUTPUT_FILE = "/tmp/smarthome_inventory.md"

DOMAIN_ICONS = {
    "light": "💡", "switch": "🔌", "sensor": "🌡️", 
    "binary_sensor": "👁️", "camera": "📷", "media_player": "🎵",
    "lock": "🔒", "fan": "💨", "climate": "❄️", "cover": "🪟",
    "vacuum": "🧹", "alarm_control_panel": "🛡️"
}

IMPORTANT_DOMAINS = list(DOMAIN_ICONS.keys())

async def generate_inventory():
    if not ha_client.enabled:
        print("Home Assistant Integration Disabled")
        return

    print("Fetching states from Home Assistant...")
    states = await ha_client.get_states()
    if not states:
        print("No states returned")
        return

    # Group by domain
    inventory = {d: [] for d in IMPORTANT_DOMAINS}
    others = []

    for s in states:
        entity_id = s['entity_id']
        domain = entity_id.split('.')[0]
        
        item = {
            "id": entity_id,
            "name": s['attributes'].get('friendly_name', entity_id),
            "state": s['state'],
            "attributes": s['attributes']
        }

        if domain in inventory:
            inventory[domain].append(item)
        else:
            others.append(item)

    # Generate Markdown
    md = []
    md.append("# 🏠 Smart Home Inventory")
    md.append(f"> **Generado**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"> **Total Entidades**: {len(states)}")
    md.append("")
    md.append("Este documento detalla todos los dispositivos detectados en Home Assistant.")
    md.append("")

    # Summary
    md.append("## 📊 Resumen")
    md.append("| Tipo | Cantidad |")
    md.append("|------|----------|")
    for domain in IMPORTANT_DOMAINS:
        count = len(inventory[domain])
        if count > 0:
            md.append(f"| {DOMAIN_ICONS[domain]} {domain.title()} | {count} |")
    md.append("")

    # Detailed Tables
    for domain in IMPORTANT_DOMAINS:
        items = inventory[domain]
        if not items:
            continue
            
        md.append(f"## {DOMAIN_ICONS[domain]} {domain.title()} ({len(items)})")
        md.append("| Nombre | ID | Estado | Notas |")
        md.append("|--------|----|--------|-------|")
        
        # Sort by name
        items.sort(key=lambda x: x['name'])
        
        for item in items:
            state = item['state']
            # Simplify state for huge strings
            if len(str(state)) > 50:
                state = str(state)[:47] + "..."
            
            # Extract useful attributes
            notes = []
            attrs = item['attributes']
            if 'battery_level' in attrs:
                notes.append(f"🔋 {attrs['battery_level']}%")
            if 'unit_of_measurement' in attrs:
                state = f"{state} {attrs['unit_of_measurement']}"
            if 'device_class' in attrs:
                notes.append(f"Type: {attrs['device_class']}")
            if 'ip_address' in attrs:
                notes.append(f"IP: {attrs['ip_address']}")
            
            note_str = ", ".join(notes)
            md.append(f"| {item['name']} | `{item['id']}` | **{state}** | {note_str} |")
        
        md.append("")

    # Save to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    
    print(f"Inventory saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(generate_inventory())

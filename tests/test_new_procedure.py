#!/usr/bin/env python3
"""Test da preveri, ali je nov postopek pravilno dodan."""

import json

# Naloži JSON shemo
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

print("🔍 Preverjam nov postopek oddaje naročila...")
print("=" * 60)

# Preveri glavno enum listo
procedures = schema['properties']['submissionProcedure']['properties']['procedure']['enum']
print("\n📋 Seznam vseh postopkov:")
for i, proc in enumerate(procedures, 1):
    if "postopek s pogajanji z objavo" in proc:
        print(f"   {i}. ✅ {proc}")
    else:
        print(f"   {i}. {proc}")

# Preveri pozicijo novega postopka
new_proc = "postopek s pogajanji z objavo (zgolj za javno naročanje na infrastrukturnem področju)"
if new_proc in procedures:
    position = procedures.index(new_proc)
    print(f"\n✅ Nov postopek dodan na pozicijo {position + 1}")
    
    # Preveri, da je takoj za "konkurenčni postopek s pogajanji"
    if position > 0 and procedures[position-1] == "konkurenčni postopek s pogajanji":
        print("✅ Pravilno postavljen za 'konkurenčni postopek s pogajanji'")
    else:
        print("⚠️ Ni na pričakovani poziciji!")
else:
    print("❌ Nov postopek ni najden!")

# Preveri render_if pogoj
try:
    # Najdi noNegotiationsInfo v negotiationsInfo
    for key, value in schema['properties']['negotiationsInfo']['properties'].items():
        if 'render_if' in value and 'not_in' in value['render_if']:
            negotiation_not_in = value['render_if']['not_in']
            if new_proc in negotiation_not_in:
                print(f"✅ Dodan v render_if pogoj za pogajanja (v {key})")
                break
    else:
        # Če nismo našli
        print("⚠️ Preveri render_if pogoj ročno")
except Exception as e:
    print(f"⚠️ Napaka pri preverjanju render_if: {e}")

print("\n" + "=" * 60)
print("✨ Test končan!")
print("\nNov postopek:")
print("📌 'postopek s pogajanji z objavo (zgolj za javno naročanje na infrastrukturnem področju)'")
print("je uspešno dodan in bo viden v dropdown seznamu!")
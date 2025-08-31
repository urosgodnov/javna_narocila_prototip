# Epic: Popravki Migracije Validacij in Optimizacija - Brownfield Enhancement

## Epic Goal
Odpraviti napake, ki so nastale pri migraciji validacij iz starega form_renderer sistema v novo unified lot arhitekturo ter optimizirati obstoječe validacije za boljšo uporabniško izkušnjo.

## Epic Description

### Existing System Context:
- **Trenutno stanje**: Nova forma arhitektura je delno implementirana (FormController, unified lot handling)
- **Technology stack**: Python, Streamlit, SQLite
- **Integration points**: 
  - `utils/validations.py` - obstoječe validacije
  - `ui/controllers/form_controller.py` - nov sistem
  - `ui/form_renderer_compat.py` - compatibility layer
  - Session state management

### Enhancement Details:
- **Kaj popravljamo**: Napake pri migraciji validacij iz starega v nov sistem
- **Kako**: 
  - Pregled vseh validate_* metod v ValidationManager
  - Uskladitev z unified lot konceptom (vse je sklop)
  - Popravki napak v conditional validaciji
  - Optimizacija sporočil napak
- **Success criteria**: 
  - Vse validacije delujejo v novi arhitekturi
  - Pogojne validacije se pravilno prikazujejo
  - Unified lot handling deluje konsistentno
  - Jasna sporočila napak v slovenščini

## Stories

### Story 1: Popravki Core Validacij in Unified Lot Handling
**Opis**: Popraviti osnovne validacije da pravilno delujejo z unified lot konceptom
- Pregled in popravek `validate_screen_5_lots()` 
- Zagotoviti da naročilo brez sklopov = 1 virtualni sklop
- Popraviti `validate_order_type()` za unified handling
- **DODATI**: Transformacijo "vseeno" → "odprti postopek" pri shranjevanju/generiranju dokumentov
- Optimizirati sporočila napak

### Story 2: Popravki Conditional Validacij in Required Polj
**Opis**: Odpraviti napake v pogojnih validacijah in dinamičnem označevanju obveznih polj
- Popraviti render_if evaluacijo
- Dinamične zvezdice (*) za pogojno obvezna polja
- Array validacije (clients, lots, cofinancers)
- **DODATI**: Validacijo/opozorilo če uporabnik pokuša dodati več sklopov brez obkljukanja "Naročilo je razdeljeno na sklope"
- Real-time re-evaluacija ob spremembi trigger polj

### Story 3: Optimizacija Cross-Field Validacij in CPV Omejitev
**Opis**: Optimizirati kompleksne validacije in CPV-based omejitve
- Validacija meril in točk (vsota = 100) - POPRAVI obstoječe
- CPV omejitve (cena ne sme biti edino merilo, socialna merila) - POPRAVI obstoječe
- Tiebreaker validacija - NOVA FUNKCIONALNOST (lahko se preskoči)
- Datumski razponi in format validacije - POPRAVI obstoječe

## Implementation Approach
- [x] Direct replacement of broken validations
- [x] No backward compatibility needed (zero data in database)
- [x] Can make breaking changes freely
- [x] Unified lot concept implementation from scratch

## Definition of Done
- [ ] Vse validacije delujejo v novi unified lot arhitekturi
- [ ] Napake iz migracije odpravljene
- [ ] Pogojne validacije delujejo pravilno
- [ ] Sporočila napak v slovenščini in jasna
- [ ] Ni regresij v obstoječi funkcionalnosti
- [ ] Testiranje vseh korakov forme

## Tehnični Detajli

### Nova Poslovna Pravila za Implementacijo:
1. **Postopek "vseeno" transformacija**:
   ```python
   # Pri shranjevanju ali generiranju dokumentov
   if submissionProcedure.procedure == "vseeno":
       submissionProcedure.procedure = "odprti postopek"
   ```
   - Lokacija: Pri pripravi podatkov za dokumente
   - Razlog: "vseeno" ni pravno veljaven postopek

### Ključne Napake za Popravek:
1. **Unified Lot Handling**:
   - `validate_screen_5_lots()` mora razumeti da brez sklopov = 1 sklop
   - Order type validacija mora delovati za virtualni sklop

2. **Conditional Validacije**:
   - Pogojno obvezna polja se ne označujejo pravilno
   - Array minimum validacije ne delujejo (clients, lots)
   - Sofinancerji validacija

3. **Cross-Field Validacije**:
   - Datum razponi (start <= end)
   - Merila točke vsota != 100
   - CPV omejitve se ne preverjajo

### Obseg Sprememb:
- **NE SPREMINJAMO**: UI komponente, stiliranje, FormController arhitekturo
- **SPREMINJAMO SAMO**: Validacijske metode v `utils/validations.py`
- **ODSTRANIMO**: Finančne validacije (IBAN, SWIFT) - bo v ločenem storiju

### Prioritete:
1. **VISOKA**: Popravki ki blokirajo normalno uporabo (required polja, unified lots)
2. **SREDNJA**: Optimizacije sporočil in conditional validacije
3. **NIZKA**: Edge cases in nice-to-have izboljšave

## Časovna Ocena
- Story 1: 3-4 ure (core validacije)
- Story 2: 4-5 ur (conditional sistem)
- Story 3: 3-4 ure (cross-field in CPV)
- **Skupaj**: 10-13 ur

## Dependencies
- FormController arhitektura
- ValidationManager v utils/validations.py
- Streamlit session state management

## Notes
- Finančne validacije (IBAN, SWIFT, Bank) → Glej `epic_financial_validations.md`
- Ločena polja za naslov (ulica, hišna številka) → Glej `epic_input_form_enhancement.md`
- **No migration needed**: Zero data means we can rebuild validations cleanly
- **No compatibility layer needed**: Can directly use new FormController everywhere

## Related Epics
- **epic_financial_validations.md** - IBAN, SWIFT, Bank validations with registry integration
- **epic_input_form_enhancement.md** - Address field separation (street, house number)

## 🔴 Sistem Označevanja Obveznih Polj

### Vizualni Indikatorji
- **Zvezdica (*)**:Vsa obvezna polja so označena z rdečo zvezdico ob imenu polja
- **ℹ️ Info polja**: INLINE za kratka besedila, DROPDOWN za dolga besedila
- **⚠️ Opozorila**: INLINE za kratka opozorila, DROPDOWN za dolga opozorila
- **Rdeča obroba**: Neizpolnjena obvezna polja ob validaciji dobijo rdečo obrobo
- **Validacijska opozorila**: Pod gumbom "Naprej" se prikaže seznam vseh neizpolnjenih polj

### Validacijski Sistem

**LOKACIJA VSEH VALIDACIJ**: `utils/validations.py` (centraliziran sistem)

1. **Ob kliku na "Naprej"**:
   - Sistem preveri vsa obvezna polja na trenutnem koraku
   - Če polja niso izpolnjena:
     - Prikaže se opozorilo: "❌ Prosimo, izpolnite vsa obvezna polja pred nadaljevanjem"
     - Seznam neizpolnjenih polj z imeni in lokacijami
     - Neizpolnjena polja dobijo rdečo obrobo za vizualno označitev
   - Če so vsa polja izpolnjena: napreduje na naslednji korak

2. **Dinamične validacije**:
   - Polja, ki postanejo obvezna glede na druge izbire (npr. conditional required)
   - CPV validacije z opozorili o omejitvah
   - Datumske validacije (dd.mm.yyyy format)
   - Numerične validacije (min/max vrednosti)

3. **Oznaka obveznih polj**:
   - Vsa polja z oznakami **OBVEZNO** ali **Required** imajo zvezdico (*) v naslovu
   - Pogojno obvezna polja dobijo zvezdico, ko pogoj izpolnjen

## Struktura Dokumenta
- **Field Key**: Pot do polja (npr. `clientInfo.name`)
- **Field Type**: Streamlit widget tip
- **JSON Type**: Tip v JSON schema
- **Validation**: Validacijska pravila za NOVO FORMO
- **Conditional**: Pogojni prikaz/validacija v NOVI ARHITEKTURI
- **Zvezdica (*)**: Označuje obvezno polje
- **Default**: Privzeta vrednost (posebej pomembno: datumi imajo `default: null`)
- **Pattern**: Regex vzorec za validacijo
- **🆕 UNIFIED LOT**: Vsa naročila (z ali brez sklopov) se obravnavajo enotno

---

## KORAK 1: Podatki o naročniku (clientInfo)

### clientInfo.multipleClientsInfo
- **Field Type**: ℹ️ Info polje - DROPDOWN (dolgo besedilo)
- **JSON Type**: `object`
- **Validation**: /
- **Description**: Informacija o več naročnikih - poučuje kako vnesti več naročnikov s pooblastilom

### clientInfo.isSingleClient
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `true`
- **Validation**: /
- **Description**: Naročnik je eden

### clientInfo.singleClientName *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `isSingleClient = true`
- **Conditional**: `render_if: {"field": "clientInfo.isSingleClient", "value": true}`

### clientInfo.singleClientStreetAddress *
- **⚠️ TRENUTNO**: Kombinirano polje (ulica + hišna številka)
- **⚠️ ZA LOČENA POLJA**: Glej `epic_input_form_enhancement.md`
- **Validation**: OBVEZNO če `isSingleClient = true`

### clientInfo.singleClientPostalCode *
- **Pattern**: `^[0-9]{4}$` (4 številke, 1000-9999)
- **Validation**: OBVEZNO če `isSingleClient = true`
- **⚠️ ZA IMPLEMENTACIJO**: Glej `epic_input_form_enhancement.md`

### clientInfo.singleClientCity *
- **Validation**: OBVEZNO če `isSingleClient = true`
- **⚠️ ZA LOČENO OD POŠTNE**: Glej `epic_input_form_enhancement.md`

### clientInfo.singleClientLegalRepresentative *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `isSingleClient = true`
- **Conditional**: `render_if: {"field": "clientInfo.isSingleClient", "value": true}`
- **Description**: "Zakoniti zastopnik (ime in priimek)"

### clientInfo.singleClientTRR
- **⚠️ GLEJ**: `epic_financial_validations.md` za implementacijo IBAN validacije

### clientInfo.singleClientBank  
- **⚠️ GLEJ**: `epic_financial_validations.md` za implementacijo bank validacije

### clientInfo.singleClientSwift
- **⚠️ GLEJ**: `epic_financial_validations.md` za implementacijo SWIFT validacije

### clientInfo.clients
- **Field Type**: Array (dinamično dodajanje)
- **JSON Type**: `array`
- **Validation**: Vsaj 2 če `isSingleClient = false`
- **Conditional**: `render_if: {"field": "clientInfo.isSingleClient", "value": false}`
- **Item Properties**:
  - `name`: string, OBVEZNO - Naziv naročnika
  - `streetAddress`: string, OBVEZNO - **TRENUTNO kombinirano** → **GLEJ** `epic_input_form_enhancement.md`
  - `postalCode`: string, OBVEZNO - **GLEJ** `epic_input_form_enhancement.md`
  - `city`: string, OBVEZNO - **GLEJ** `epic_input_form_enhancement.md`
  - `legalRepresentative`: string, OBVEZNO - Zakoniti zastopnik
  - `trr`: string, neobvezno - **GLEJ** `epic_financial_validations.md`
  - `bank`: string, OBVEZNO če je vnesen TRR - **GLEJ** `epic_financial_validations.md`
  - `swift`: string, neobvezno - **GLEJ** `epic_financial_validations.md`

### clientInfo.wantsLogo
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Validation**: /

### clientInfo.logo
- **Field Type**: `st.file_uploader`
- **JSON Type**: `string`, format: `file`
- **Validation**: /
- **Conditional**: `render_if: {"field": "clientInfo.wantsLogo", "value": true}`

---

## KORAK 2: Osnovni podatki o javnem naročilu (projectInfo)

### projectInfo.projectName *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO
- **Description**: Naziv javnega naročila

### projectInfo.internalProjectNumber *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: Neobvezno
- **Description**: Interna številka javnega naročila (neobvezno)

### projectInfo.projectSubject *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO
- **Description**: Predmet javnega naročila

### projectInfo.cpvCodes *
- **Field Type**: CPV selector (custom component) - izbira SAMO iz baze podatkov
- **JSON Type**: `string`, format: `cpv`
- **Validation**: OBVEZNO, veljavna CPV koda iz obstoječe baze
- **Description**: Vpišite vse CPV kode (izbira samo iz seznama v bazi)
- **UI Note**: Dropdown/autocomplete iz baze CPV kod

---

## KORAK 3: Pravna podlaga (legalBasis)

### legalBasis.useAdditional
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Validation**: /
- **Description**: Želim, da se upošteva še kakšna pravna podlaga

### legalBasis.additionalLegalBases
- **Field Type**: Array (dinamično dodajanje)
- **JSON Type**: `array` of `string`
- **Validation**: Vsaj 1 če `useAdditional = true`
- **Conditional**: `render_if: {"field": "legalBasis.useAdditional", "value": true}`

---

## KORAK 4: Postopek oddaje javnega naročila (submissionProcedure)

### submissionProcedure.procedure *
- **Field Type**: `st.selectbox` ali `st.radio`
- **JSON Type**: `string` z enum
- **Validation**: OBVEZNO
- **Options**: 
  - "odprti postopek"
  - "omejeni postopek"
  - "konkurenčni dialog"
  - "partnerstvo za inovacije"
  - "konkurenčni postopek s pogajanji (zgolj za javno naročanje na splošnem področju)"
  - "postopek s pogajanji z objavo (zgolj za javno naročanje na infrastrukturnem področju)"
  - "postopek s pogajanji brez predhodne objave"
  - "postopek naročila male vrednosti"
  - "vseeno"
- **⚠️ POSLOVNO PRAVILO**: Če je izbrano "vseeno", se v dokumentih uporablja "odprti postopek"
- **🔴 NI IMPLEMENTIRANO**: Transformacija "vseeno" → "odprti postopek" pri generiranju dokumentov

### submissionProcedure.justification *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če postopek ni "odprti postopek" ali "vseeno"
- **Conditional**: `render_if: {"field": "submissionProcedure.procedure", "not_in": ["odprti postopek", "vseeno"]}`

---

## KORAK 5: Informacije o sklopih (lotsInfo) - 🆕 NOVA ARHITEKTURA

### lotsInfo.lotsInfoHelp
- **Field Type**: ℹ️ Info polje - INLINE (kratko besedilo)
- **JSON Type**: `object`
- **Validation**: /
- **Description**: "Obkljukajte spodnje polje, če je naročilo razdeljeno na sklope"
- **🔴 POMEMBNO NAVODILO ZA UPORABNIKE**: 
  - Če ima naročilo 2 ali več sklopov, MORATE obkljukati "Naročilo je razdeljeno na sklope"
  - Če polje ni obkljukano, bo sistem vse obravnaval kot EN sklop
  - Pri večih sklopih je obkljukanje OBVEZNO za pravilno delovanje
- **🆕 NOVA LOGIKA**: Če ni obkljukano, se naročilo obravnava kot 1 sklop

### lotsInfo.hasLots
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Validation**: /
- **Description**: Naročilo je razdeljeno na sklope
- **⚠️ NAVODILO**: OBVEZNO obkljukajte, če imate 2 ali več sklopov!
- **🆕 UNIFIED HANDLING**: 
  - `false` (neobkljukano) = naročilo se interno obravnava kot 1 sklop
  - `true` (obkljukano) = naročilo ima več sklopov (min 2)

---

## KORAK 5a: Sklopi javnega naročila (lots) - če hasLots = true

### lots
- **Field Type**: Array (dinamično dodajanje)
- **JSON Type**: `array`
- **Validation**: Vsaj 2 sklopa če `hasLots = true`
- **Conditional**: `render_if: {"field": "lotsInfo.hasLots", "value": true}`
- **🆕 NOVA IMPLEMENTACIJA**:
  - Če `hasLots = false`: sistem avtomatsko ustvari 1 virtualni sklop
  - Če `hasLots = true`: uporabnik mora vnesti vsaj 2 sklopa
- **📢 UPORABNIŠKO NAVODILO**: 
  - Ko obkljukate "Naročilo je razdeljeno na sklope", se pojavi možnost vnosa sklopov
  - Vnesite VSE sklope vašega naročila (minimalno 2)
  - Vsak sklop mora imeti svoj naziv in vrsto
- **Item Properties**:
  - `name`: string, obvezno - Naziv sklopa
  - `orderType`: object - glej orderType definicijo

---

## KORAK 6: Vrsta javnega naročila (orderType)

### orderType.type *
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Default**: `"blago"`
- **Validation**: OBVEZNO
- **Options**:
  - "blago"
  - "storitve"
  - "gradnje"
  - "mešano javno naročilo"

### orderType.estimatedValue *
- **Field Type**: `st.number_input`
- **JSON Type**: `number`
- **Validation**: OBVEZNO, mora biti > 0
- **Conditional**: `render_if: {"field_parent": "type", "not_in": ["mešano javno naročilo"]}`
- **Description**: Ocenjena vrednost javnega naročila (EUR brez DDV)
- **💡 OPOMBA**: Pri mešanih naročilih se vrednost vnaša za vsako komponento posebej

### orderType.guaranteedFunds
- **Field Type**: `st.number_input`
- **JSON Type**: `number`
- **Validation**: Če izpolnjeno, mora biti > 0
- **Conditional**: `render_if: {"field_parent": "type", "not_in": ["mešano javno naročilo"]}`
- **💡 OPOMBA**: Pri mešanih naročilih se sredstva vnašajo za vsako komponento posebej

### orderType.isCofinanced
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Validation**: /
- **Conditional**: `render_if: {"field_parent": "type", "not_in": ["mešano javno naročilo"]}`
- **💡 OPOMBA**: Pri mešanih naročilih se sofinanciranje določa za vsako komponento posebej

### orderType.cofinancers
- **Field Type**: Array (dinamično dodajanje)
- **JSON Type**: `array`
- **Validation**: Vsaj 1 če `isCofinanced = true`
- **Conditional**: `render_if: {"field_parent": "isCofinanced", "value": true}`
- **Item Properties**:
  - `cofinancerName`: string, obvezno
  - `cofinancerStreetAddress`: string, obvezno - **TRENUTNO kombinirano** → **GLEJ** `epic_input_form_enhancement.md`
  - `cofinancerPostalCode`: string, obvezno - **GLEJ** `epic_input_form_enhancement.md`
  - `cofinancerCity`: string, obvezno - **GLEJ** `epic_input_form_enhancement.md`
  - `programName`: string, obvezno
  - `programArea`: string, obvezno
  - `programCode`: string, obvezno
  - `logo`: file, neobvezno
  - `specialRequirements`: textarea, neobvezno - Posebne zahteve sofinancerja
  - `useAIForRequirements`: 🤖 checkbox - "Drugo, želim pomoč AI" → **GLEJ** `epic_ai_assistance_requirements.md`

### orderType.deliveryType *
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Validation**: OBVEZNO če `type = "blago"`
- **Conditional**: `render_if: {"field_parent": "type", "value": "blago"}`
- **Options**:
  - "enkratna dobava"
  - "sukcesivne dobave"

### orderType.includeZJN3Obligations
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Validation**: /
- **Conditional**: `render_if: {"field_parent": "type", "value": "blago"}`

### orderType.serviceType *
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Validation**: OBVEZNO če `type = "storitve"`
- **Conditional**: `render_if: {"field_parent": "type", "value": "storitve"}`
- **Options**:
  - "enkratna"
  - "ponavljajoče se storitve"

### orderType.mixedOrderComponents
- **Field Type**: Array (dinamično dodajanje)
- **JSON Type**: `array`
- **Validation**: Vsaj 1 če `type = "mešano javno naročilo"`
- **Conditional**: `render_if: {"field_parent": "type", "value": "mešano javno naročilo"}`
- **Item Properties**: Vsaka komponenta ima:
  - `type`: string, enum ["blago", "storitve", "gradnje"]
  - `description`: string - opis postavke
  - `estimatedValue`: number - ocenjena vrednost postavke
  - `guaranteedFunds`: number - zagotovljena sredstva za postavko
  - `isCofinanced`: boolean - ali je postavka sofinancirana
  - `cofinancers`: array - sofinancerji ZA TO POSTAVKO
    - Vsak sofinancer ima vse potrebne podatke (naziv, naslov, program, itd.)
    - `useAIForRequirements`: 🤖 checkbox → **GLEJ** `epic_ai_assistance_requirements.md`
  - `deliveryType`: string (za blago)
  - `serviceType`: string (za storitve)
- **💡 KLJUČNO**: Sofinancerji so definirani na nivoju vsake komponente, ne na glavnem nivoju

---

## KORAK 7: Tehnične zahteve oziroma specifikacije (technicalSpecifications)

### technicalSpecifications.hasSpecifications *
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Validation**: OBVEZNO
- **Options**:
  - "da"
  - "ne"

### technicalSpecifications.noSpecificationsWarning
- **Field Type**: ⚠️ Opozorilo - DROPDOWN (dolgo besedilo)
- **JSON Type**: `object`
- **Conditional**: `render_if: {"field": "technicalSpecifications.hasSpecifications", "value": "ne"}`
- **Description**: Opozorilo o pripravi dokumentacije brez tehničnih zahtev - terminologija ne bo usklajena

### technicalSpecifications.specificationDocuments
- **Field Type**: Array (dinamično dodajanje)
- **JSON Type**: `array`
- **Validation**: Vsaj 1 če `hasSpecifications = "da"`
- **Conditional**: `render_if: {"field": "technicalSpecifications.hasSpecifications", "value": "da"}`
- **Item Properties**:
  - `name`: string, obvezno
  - `file`: file upload, obvezno

---

## KORAK 8: Rok izvedbe oziroma trajanje javnega naročila (executionDeadline)

### executionDeadline.type *
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Validation**: OBVEZNO
- **Options**:
  - "datumsko"
  - "v dnevih"
  - "v mesecih"
  - "v letih"

### executionDeadline.startDate *
- **Field Type**: `st.date_input`
- **JSON Type**: `string`, format: `date`
- **Default**: `null` (prazno polje)
- **Validation**: OBVEZNO če `type = "datumsko"`
- **Format**: **dd.mm.yyyy**
- **Conditional**: `render_if: {"field": "executionDeadline.type", "value": "datumsko"}`
- **Description**: "Začetni datum"
- **⚠️ Validacija formata**: Datum mora biti v formatu dd.mm.yyyy

### executionDeadline.endDate *
- **Field Type**: `st.date_input`
- **JSON Type**: `string`, format: `date`
- **Default**: `null` (prazno polje)
- **Validation**: OBVEZNO če `type = "datumsko"`
- **Format**: **dd.mm.yyyy**
- **Conditional**: `render_if: {"field": "executionDeadline.type", "value": "datumsko"}`
- **Description**: "Končni datum"
- **⚠️ Validacija**: 
  - Datum mora biti v formatu dd.mm.yyyy
  - Končni datum MORA BITI PO začetnem datumu
  - Pri vnosu: sistem avtomatsko omejuje izbor (min_value = začetni datum)
  - Pri shranjevanju: validacija preveri: `if end < start: error`

### executionDeadline.days *
- **Field Type**: `st.number_input` s +/- gumbi
- **JSON Type**: `integer`
- **Validation**: OBVEZNO če `type = "v dnevih"`, mora biti > 0
- **Conditional**: `render_if: {"field": "executionDeadline.type", "value": "v dnevih"}`
- **UI Note**: Stepper kontrola s +/- gumbi

### executionDeadline.months *
- **Field Type**: `st.number_input` s +/- gumbi
- **JSON Type**: `integer`
- **Validation**: OBVEZNO če `type = "v mesecih"`, mora biti > 0
- **Conditional**: `render_if: {"field": "executionDeadline.type", "value": "v mesecih"}`
- **UI Note**: Stepper kontrola s +/- gumbi

### executionDeadline.years *
- **Field Type**: `st.number_input` s +/- gumbi
- **JSON Type**: `integer`
- **Validation**: OBVEZNO če `type = "v letih"`, mora biti > 0
- **Conditional**: `render_if: {"field": "executionDeadline.type", "value": "v letih"}`
- **UI Note**: Stepper kontrola s +/- gumbi

---

## KORAK 9: Informacije o ceni (priceInfo)

### priceInfo.priceClause *
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Validation**: OBVEZNO
- **Options**:
  - "cena na enoto mere"
  - "pavšalna cena za izvedbo vseh pogodbenih obveznosti in kot izračun z izrecnim jamstvom (643. člen OZ) – v primeru, da gre za javno naročilo storitev in bo sklenjena podjemna pogodba"
  - "skupaj dogovorjena cena"
  - "ključ v roke"
  - "drugo"

### priceInfo.otherPriceClause *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `priceClause = "drugo"`
- **Conditional**: `render_if: {"field": "priceInfo.priceClause", "value": "drugo"}`

### priceInfo.priceFixation *
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Validation**: OBVEZNO
- **Options**:
  - "bodo ponudbene cene fiksne ves čas izvajanja pogodbe"
  - "se bodo ponudbene cene valorizirale, skladno z valorizacijsko klavzulo"

### priceInfo.valorization
- **Field Type**: Nested object
- **JSON Type**: `object`
- **Conditional**: `render_if: {"field": "priceInfo.priceFixation", "value": "se bodo ponudbene cene valorizirale, skladno z valorizacijsko klavzulo"}`
- **Sub-fields**:
  - `type`: enum ["v dnevih", "v mesecih", "v letih"]
  - `days`: integer če type = "v dnevih", mora biti > 0, stepper s +/- gumbi
  - `months`: integer če type = "v mesecih", mora biti > 0, stepper s +/- gumbi
  - `years`: integer če type = "v letih", mora biti > 0, stepper s +/- gumbi

### priceInfo.hasOfferBillOfQuantities
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Validation**: /

### priceInfo.noOfferBillOfQuantitiesWarning
- **Field Type**: ⚠️ Opozorilo - DROPDOWN (dolgo besedilo)
- **JSON Type**: `object`
- **Conditional**: `render_if: {"field": "priceInfo.hasOfferBillOfQuantities", "value": false}`
- **Description**: Opozorilo o pripravi dokumentacije brez ponudbenega predračuna - terminologija ne bo usklajena

### priceInfo.quantitiesType
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Conditional**: `render_if: {"field": "priceInfo.hasOfferBillOfQuantities", "value": true}`
- **Options**:
  - "količine navedene v ponudbenem predračunu so fiksne"
  - "količine navedene v ponudbenem predračunu so okvirne in naročnik pri izvedbi javnega naročila nanje ni vezan"

### priceInfo.offerBillOfQuantitiesDocument
- **Field Type**: `st.file_uploader`
- **JSON Type**: `string`, format: `file`
- **Conditional**: `render_if: {"field": "priceInfo.hasOfferBillOfQuantities", "value": true}`

---

## KORAK 10: Ogled lokacije (inspectionInfo)

### inspectionInfo.hasInspection
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Validation**: /

### inspectionInfo.isInspectionMandatory
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: `render_if: {"field": "inspectionInfo.hasInspection", "value": true}`

### inspectionInfo.inspectionDates
- **Field Type**: Array (dinamično dodajanje)
- **JSON Type**: `array`
- **Validation**: Vsaj 1 če `hasInspection = true`
- **Conditional**: `render_if: {"field": "inspectionInfo.hasInspection", "value": true}`
- **Item Properties**:
  - `date`: date, obvezno - **Format: dd.mm.yyyy**, **Default: null** (prazno polje)
  - `time`: time, obvezno - **Format: HH:mm**, **Default: null** (prazno polje)
- **⚠️ Validacija formata**: Datum mora biti v formatu dd.mm.yyyy, čas v formatu HH:mm

### inspectionInfo.inspectionLocation *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `hasInspection = true`
- **Conditional**: `render_if: {"field": "inspectionInfo.hasInspection", "value": true}`

### inspectionInfo.isOfferAfterInspectionOnly
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: `render_if: {"field": "inspectionInfo.hasInspection", "value": true}`

### inspectionInfo.zjn3ComplianceWarning
- **Field Type**: ⚠️ Opozorilo - DROPDOWN (dolgo besedilo)
- **JSON Type**: `object`
- **Conditional**: `render_if: {"field": "inspectionInfo.isOfferAfterInspectionOnly", "value": true}`
- **Description**: Opozorilo o podaljšanju rokov zaradi obveznega ogleda - roki morajo biti daljši od minimalnih

---

## KORAK 11: Informacije o pogajanjih (negotiationsInfo)

### negotiationsInfo.negotiationsNotAllowed
- **Field Type**: ⚠️ Opozorilo - INLINE (kratko besedilo)
- **JSON Type**: `object`
- **Conditional**: Prikaže se če postopek ne omogoča pogajanj
- **Description**: "Pogajanja niso možna za izbrani postopek oddaje javnega naročila"

### negotiationsInfo.hasNegotiations
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: Prikaže se samo za ustrezne postopke

### negotiationsInfo.negotiationSubject
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Conditional**: `render_if: {"field": "negotiationsInfo.hasNegotiations", "value": true}`
- **Options**:
  - "cena"
  - "drugo"

### negotiationsInfo.otherNegotiationSubject
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Conditional**: `render_if: {"field": "negotiationsInfo.negotiationSubject", "value": "drugo"}`

### negotiationsInfo.negotiationRounds
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Conditional**: `render_if: {"field": "negotiationsInfo.hasNegotiations", "value": true}`
- **Options**:
  - "1 krog"
  - "več krogov, ne vem še koliko"

### negotiationsInfo.hasSpecialWishes
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: `render_if: {"field": "negotiationsInfo.hasNegotiations", "value": true}`

### negotiationsInfo.specialNegotiationWishes
- **Field Type**: `st.text_area`
- **JSON Type**: `string`
- **Conditional**: `render_if: {"field": "negotiationsInfo.hasSpecialWishes", "value": true}`

---

## KORAK 12: Razlogi za izključitev (participationAndExclusion)

### participationAndExclusion.sectionHeader
- **Field Type**: ℹ️ Info polje - INLINE (kratko besedilo)
- **JSON Type**: `object`
- **Description**: "Prosimo označite vse neobvezne razloge za izključitev, ki jih želite vključiti"

### participationAndExclusion.exclusionReasonsSelection *
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Validation**: OBVEZNO
- **Options**:
  - "specifični razlogi"
  - "ne želimo vključiti neobveznih razlogov za izključitev"
  - "vseeno nam je"

### participationAndExclusion.krsitev_okoljskega_prava
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: `render_if: {"field": "participationAndExclusion.exclusionReasonsSelection", "value": "specifični razlogi"}`
- **Description**: kršitev obveznosti na področju okoljskega, socialnega in delovnega prava (a. točka šestega odstavka 75. člena ZJN-3)

### participationAndExclusion.postopek_insolventnosti
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: `render_if: {"field": "participationAndExclusion.exclusionReasonsSelection", "value": "specifični razlogi"}`
- **Description**: postopek insolventnosti ali prisilnega prenehanja, likvidacije (b. točka šestega odstavka 75. člena ZJN-3)

### participationAndExclusion.krsitev_poklicnih_pravil
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: `render_if: {"field": "participationAndExclusion.exclusionReasonsSelection", "value": "specifični razlogi"}`
- **Description**: hujša kršitev poklicnih pravil, zaradi česar je omajana integriteta (c. točka šestega odstavka 75. člena ZJN-3)

### participationAndExclusion.professionalMisconductDetails
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Conditional**: `render_if: {"field": "participationAndExclusion.krsitev_poklicnih_pravil", "value": true}`

### participationAndExclusion.dogovor_izkrivljanje_konkurence
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: `render_if: {"field": "participationAndExclusion.exclusionReasonsSelection", "value": "specifični razlogi"}`
- **Description**: dogovor z drugimi gospodarskimi subjekti z namenom izkrivljanja konkurence (č. točka šestega odstavka 75. člena ZJN-3)

### participationAndExclusion.nasprotje_interesov
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: `render_if: {"field": "participationAndExclusion.exclusionReasonsSelection", "value": "specifični razlogi"}`
- **Description**: nasprotja interesov (v komisiji naročnika je nekdo povezan s ponudnikom) (d. točka šestega odstavka 75. člena ZJN-3)

### participationAndExclusion.predhodno_sodelovanje
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: `render_if: {"field": "participationAndExclusion.exclusionReasonsSelection", "value": "specifični razlogi"}`
- **Description**: predhodno sodelovanje pri pripravi tega postopka javnega naročanja (e. točka šestega odstavka 75. člena ZJN-3)

### participationAndExclusion.pomanjkljivosti_pri_pogodbi
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: `render_if: {"field": "participationAndExclusion.exclusionReasonsSelection", "value": "specifični razlogi"}`
- **Description**: precejšnje ali stalne pomanjkljivosti pri izpolnjevanju pogodbe (f. točka šestega odstavka 75. člena ZJN-3)

### participationAndExclusion.contractDeficienciesDetails
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Conditional**: `render_if: {"field": "participationAndExclusion.pomanjkljivosti_pri_pogodbi", "value": true}`

### participationAndExclusion.comparableSanctionsDetails
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Conditional**: `render_if: {"field": "participationAndExclusion.pomanjkljivosti_pri_pogodbi", "value": true}`

### participationAndExclusion.zavajajoce_informacije
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: `render_if: {"field": "participationAndExclusion.exclusionReasonsSelection", "value": "specifični razlogi"}`
- **Description**: dajanje resnih zavajajočih informacij ali razlag / nerazkrivanje (g. točka šestega odstavka 75. člena ZJN-3)

### participationAndExclusion.neupravicen_vpliv
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Conditional**: `render_if: {"field": "participationAndExclusion.exclusionReasonsSelection", "value": "specifični razlogi"}`
- **Description**: poskus neupravičenega vplivanja na naročnika (h. točka šestega odstavka 75. člena ZJN-3)

---

## KORAK 13: Pogoji sodelovanja (participationConditions)

### participationConditions.participationSelection *
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Validation**: OBVEZNO
- **Options**:
  - "da, specifični pogoji"
  - "ne"
  - "vseeno"

### participationConditions.economicFinancialSection (Ekonomski in finančni položaj)

#### participationConditions.economicFinancialSection.turnoverLimitInfo
- **Field Type**: ℹ️ Info polje - DROPDOWN (dolgo besedilo)
- **JSON Type**: `object`
- **Validation**: /
- **Description**: Omejitve letnega prometa po ZJN-3
- **Content**: "Zahtevani najnižji letni promet ne sme presegati dvakratne ocenjene vrednosti javnega naročila, razen v ustrezno utemeljenih primerih, ki se glede na primer nanašajo na posebna tveganja, povezana z naravo gradenj, storitev ali blaga. Če se ponudniku odda več sklopov, ki se izvajajo sočasno, lahko naročnik določi najnižji letni promet, ki ga morajo imeti gospodarski subjekti za posamezno skupino sklopov. Če se javna naročila na podlagi okvirnega sporazuma oddajo po ponovnem odpiranju konkurence, se zahtevani najvišji letni promet izračuna na podlagi pričakovanega največjega obsega posameznih naročil, ki se bodo izvajala sočasno, če to ni znano, pa na podlagi ocenjene vrednosti okvirnega sporazuma. Pri dinamičnih nabavnih sistemih se zahtevani najvišji letni promet izračuna na podlagi pričakovanega največjega obsega posameznih naročil, ki se bodo oddala v okviru tega sistema."
- **Conditional**: Prikaže se če je izbran katerikoli od tipov prometa

#### participationConditions.economicFinancialSection.generalTurnover
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: Splošni letni promet

#### participationConditions.economicFinancialSection.generalTurnoverDetails *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `generalTurnover = true`
- **Conditional**: `render_if: {"field": "participationConditions.economicFinancialSection.generalTurnover", "value": true}`
- **Description**: Navedite kaj naročnik zahteva

#### participationConditions.economicFinancialSection.specificTurnover
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: Posebni letni promet na področju poslovanja, zajetem v javnem naročilu

#### participationConditions.economicFinancialSection.specificTurnoverDetails *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `specificTurnover = true`
- **Conditional**: `render_if: {"field": "participationConditions.economicFinancialSection.specificTurnover", "value": true}`
- **Description**: Navedite kaj naročnik zahteva

#### participationConditions.economicFinancialSection.averageTurnover
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: Povprečni letni promet

#### participationConditions.economicFinancialSection.averageTurnoverDetails *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `averageTurnover = true`
- **Conditional**: `render_if: {"field": "participationConditions.economicFinancialSection.averageTurnover", "value": true}`
- **Description**: Navedite kaj naročnik zahteva

#### participationConditions.economicFinancialSection.averageSpecificTurnover
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: Povprečni posebni letni promet na področju poslovanja, zajetem v javnem naročilu

#### participationConditions.economicFinancialSection.averageSpecificTurnoverDetails *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `averageSpecificTurnover = true`
- **Conditional**: `render_if: {"field": "participationConditions.economicFinancialSection.averageSpecificTurnover", "value": true}`
- **Description**: Navedite kaj naročnik zahteva

#### participationConditions.economicFinancialSection.economicAI
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: 🤖 "drugo, prosim za predlog umetne inteligence"

### participationConditions.professionalActivitySection (Poklicna dejavnost)

#### participationConditions.professionalActivitySection.professionalAI
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: 🤖 "drugo, prosim za predlog umetne inteligence"

### participationConditions.technicalProfessionalSection (Tehnična in strokovna sposobnost)

#### participationConditions.technicalProfessionalSection.technicalAI
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: 🤖 "drugo, prosim za predlog umetne inteligence"

**Opomba**: Vsa polja AI so poenotena z besedilom "drugo, prosim za predlog umetne inteligence"

---

## KORAK 14: Finančna zavarovanja (financialGuarantees)
**Opomba**: Uporablja `$ref: "#/$defs/financialGuaranteesProperties"`

---

## KORAK 15: Variantne ponudbe (variantOffers)

### variantOffers.allowVariants
- **Field Type**: `st.selectbox`
- **JSON Type**: `string` z enum
- **Default**: `"ne"`
- **Options**:
  - "da"
  - "ne"

### variantOffers.minimalRequirements
- **Field Type**: `st.text_area`
- **JSON Type**: `string`, format: `textarea`
- **Conditional**: `render_if: {"field": "variantOffers.allowVariants", "value": "da"}`

### variantOffers.specialRequirements
- **Field Type**: `st.text_area`
- **JSON Type**: `string`, format: `textarea`
- **Conditional**: `render_if: {"field": "variantOffers.allowVariants", "value": "da"}`

---

## KORAK 16: Merila za izbor (selectionCriteria)

### A. IZBIRA MERIL

#### selectionCriteria.price
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: "Cena"
- **⚠️ CPV Omejitev**: Določene CPV kode NE DOVOLIJO cene kot edinega merila

#### selectionCriteria.additionalReferences
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: "Dodatne reference imenovanega kadra"

#### selectionCriteria.additionalTechnicalRequirements
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: "Dodatne tehnične zahteve"

#### selectionCriteria.technicalRequirementsDescription *
- **Field Type**: `st.text_area`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `additionalTechnicalRequirements = true`
- **Conditional**: `render_if: {"field": "selectionCriteria.additionalTechnicalRequirements", "value": true}`
- **Description**: "Opišite dodatne tehnične zahteve"

#### selectionCriteria.shorterDeadline
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: "Krajši rok izvedbe"

#### selectionCriteria.shorterDeadlineMinimum *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `shorterDeadline = true`
- **Conditional**: `render_if: {"field": "selectionCriteria.shorterDeadline", "value": true}`
- **Description**: "Navedite minimalni sprejemljivi rok"

#### selectionCriteria.longerWarranty
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: "Garancija daljša od zahtevane"

#### selectionCriteria.costEfficiency
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: "Stroškovna učinkovitost"

#### selectionCriteria.costEfficiencyDescription *
- **Field Type**: `st.text_area`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `costEfficiency = true`
- **Conditional**: `render_if: {"field": "selectionCriteria.costEfficiency", "value": true}`
- **Description**: "Konkretizacija stroškovne učinkovitosti"

#### selectionCriteria.socialCriteria
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: "Socialna merila"
- **⚠️ CPV Zahteva**: Določene CPV kode ZAHTEVAJO socialna merila

#### selectionCriteria.socialCriteriaOptions (socialna podmerila)
- **Field Type**: Nested object
- **Conditional**: `render_if: {"field": "selectionCriteria.socialCriteria", "value": true}`
- **Sub-fields**:
  - `youngEmployeesShare`: checkbox - "Delež zaposlenih mladih"
  - `elderlyEmployeesShare`: checkbox - "Delež zaposlenih starejših"
  - `registeredStaffEmployed`: checkbox - "Priglašeni kader je zaposlen pri ponudniku"
  - `averageSalary`: checkbox - "Povprečna plača priglašenega kadra"
  - `otherSocial`: checkbox - "Drugo"
  - `otherSocialDescription`: textarea - opis (prikaže se če `otherSocial = true`)

#### selectionCriteria.otherCriteriaCustom
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: "Drugo, imam predlog"

#### selectionCriteria.otherCriteriaCustomDescription *
- **Field Type**: `st.text_area`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `otherCriteriaCustom = true`
- **Conditional**: `render_if: {"field": "selectionCriteria.otherCriteriaCustom", "value": true}`
- **Description**: "Opišite merilo"

#### selectionCriteria.otherCriteriaAI
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: 🤖 "drugo, prosim za predlog umetne inteligence"

### B. RAZMERJA MED IZBRANIMI MERILI (točke)

#### selectionCriteria.priceRatio
- **Field Type**: `st.number_input`
- **JSON Type**: `number`
- **Validation**: Mora biti > 0 če je `price = true`
- **Conditional**: `render_if: {"field": "selectionCriteria.price", "value": true}`
- **Description**: "Cena (točke)"

#### selectionCriteria.additionalReferencesRatio
- **Field Type**: `st.number_input`
- **JSON Type**: `number`
- **Validation**: Mora biti > 0 če je `additionalReferences = true`
- **Conditional**: `render_if: {"field": "selectionCriteria.additionalReferences", "value": true}`
- **Description**: "Dodatne reference imenovanega kadra (točke)"

#### selectionCriteria.additionalTechnicalRequirementsRatio
- **Field Type**: `st.number_input`
- **JSON Type**: `number`
- **Validation**: Mora biti > 0 če je `additionalTechnicalRequirements = true`
- **Conditional**: `render_if: {"field": "selectionCriteria.additionalTechnicalRequirements", "value": true}`
- **Description**: "Dodatne tehnične zahteve (točke)"

#### selectionCriteria.shorterDeadlineRatio
- **Field Type**: `st.number_input`
- **JSON Type**: `number`
- **Validation**: Mora biti > 0 če je `shorterDeadline = true`
- **Conditional**: `render_if: {"field": "selectionCriteria.shorterDeadline", "value": true}`
- **Description**: "Krajši rok izvedbe (točke)"

#### selectionCriteria.longerWarrantyRatio
- **Field Type**: `st.number_input`
- **JSON Type**: `number`
- **Validation**: Mora biti > 0 če je `longerWarranty = true`
- **Conditional**: `render_if: {"field": "selectionCriteria.longerWarranty", "value": true}`
- **Description**: "Garancija daljša od zahtevane (točke)"

#### selectionCriteria.costEfficiencyRatio
- **Field Type**: `st.number_input`
- **JSON Type**: `number`
- **Validation**: Mora biti > 0 če je `costEfficiency = true`
- **Conditional**: `render_if: {"field": "selectionCriteria.costEfficiency", "value": true}`
- **Description**: "Stroškovna učinkovitost (točke)"

#### selectionCriteria.socialCriteria[Type]Ratio
- **Field Type**: `st.number_input` za vsako socialno podmerilo
- **JSON Type**: `number`
- **Validation**: Mora biti > 0 če je ustrezno podmerilo izbrano
- **Description**: Točke za vsako socialno podmerilo

#### selectionCriteria.otherCriteriaCustomRatio
- **Field Type**: `st.number_input`
- **JSON Type**: `number`
- **Validation**: Mora biti > 0 če je `otherCriteriaCustom = true`
- **Conditional**: `render_if: {"field": "selectionCriteria.otherCriteriaCustom", "value": true}`
- **Description**: "Drugo, imam predlog (točke)"

#### selectionCriteria.otherCriteriaAIRatio
- **Field Type**: `st.number_input`
- **JSON Type**: `number`
- **Validation**: Mora biti > 0 če je `otherCriteriaAI = true`
- **Conditional**: `render_if: {"field": "selectionCriteria.otherCriteriaAI", "value": true}`
- **Description**: 🤖 "drugo, prosim za predlog umetne inteligence (točke)"

### C. PRAVILO ZA ENAKO ŠTEVILO TOČK
**⚠️ POMEMBNO**: Točka C se prikaže SAMO če so izpolnjeni pogoji:
1. Vsaj eno merilo je izbrano v točki A
2. Vse točke so vnesene v točki B (za vsa izbrana merila)

#### selectionCriteria.tiebreakerHeader
- **Field Type**: ℹ️ Info polje - INLINE
- **JSON Type**: `object`
- **Conditional**: Prikaže se samo če so vsa merila in točke izpolnjeni
- **Description**: "Označite eno od možnosti"

#### selectionCriteria.tiebreakerRule *
- **Field Type**: `st.radio`
- **JSON Type**: `string` z enum
- **Default**: `"žreb"`
- **Validation**: OBVEZNO - mora biti izbrano
- **Conditional**: Prikaže se samo če so vsa merila in točke izpolnjeni
- **Options**:
  - "žreb"
  - "V primeru, da imata dve popolni in samostojni ponudbi enako končno skupno ponudbeno vrednost, bo naročnik med njima izbral ponudbo izbranega ponudnika, ki je pri merilu ___ prejela višje število točk"

#### selectionCriteria.tiebreakerCriterion *
- **Field Type**: `st.selectbox`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `tiebreakerRule = "prednost po merilu"`
- **Conditional**: `render_if: {"field": "selectionCriteria.tiebreakerRule", "value": "prednost po merilu"}`
- **Options**: **DINAMIČNO** - seznam vseh meril, ki so bila izbrana v točki A
- **Description**: "Navedite na katero merilo se nanaša prejšnja izjava"
- **⚠️ Validacija**: Če ni izbrano nobeno merilo, prikaži napako: "Prosimo, izberite merilo za prednost"

---

## KORAK 17: Pogodba (contractInfo)

### contractInfo.contractType
- **Field Type**: `st.checkbox`
- **JSON Type**: `boolean`
- **Default**: `false`
- **Description**: "pogodbo"

### contractInfo.contractPeriodType *
- **Field Type**: `st.radio`
- **JSON Type**: `string` z enum
- **Validation**: OBVEZNO če `contractType = true`
- **Conditional**: `render_if: {"field": "contractInfo.contractType", "value": true}`
- **Description**: "Navedite za kakšno obdobje bi želeli skleniti pogodbo:"
- **Options**:
  - "z veljavnostjo"
  - "za obdobje od ... do ..."

### contractInfo.contractValidityPeriod *
- **Field Type**: `st.text_input`
- **JSON Type**: `string`
- **Validation**: OBVEZNO če `contractPeriodType = "z veljavnostjo"`
- **Conditional**: `render_if: {"field": "contractInfo.contractPeriodType", "value": "z veljavnostjo"}`
- **Description**: "Navedite obdobje veljavnosti"

### contractInfo.contractStartDate *
- **Field Type**: `st.date_input`
- **JSON Type**: `string`, format: `date`
- **Default**: `null` (prazno polje)
- **Validation**: OBVEZNO če `contractPeriodType = "za obdobje od ... do ..."`
- **Format**: **dd.mm.yyyy**
- **Conditional**: `render_if: {"field": "contractInfo.contractPeriodType", "value": "za obdobje od ... do ..."}`
- **Description**: "Datum začetka pogodbe"
- **⚠️ Validacija formata**: Datum mora biti v formatu dd.mm.yyyy

### contractInfo.contractEndDate *
- **Field Type**: `st.date_input`
- **JSON Type**: `string`, format: `date`
- **Default**: `null` (prazno polje)
- **Validation**: OBVEZNO če `contractPeriodType = "za obdobje od ... do ..."`
- **Format**: **dd.mm.yyyy**
- **Conditional**: `render_if: {"field": "contractInfo.contractPeriodType", "value": "za obdobje od ... do ..."}`
- **Description**: "Datum konca pogodbe"
- **⚠️ Validacija**: 
  - Datum mora biti v formatu dd.mm.yyyy
  - Končni datum MORA BITI PO začetnem datumu
  - Pri vnosu: sistem avtomatsko omejuje izbor (min_value = začetni datum)
  - Pri shranjevanju: validacija preveri: `if end < start: error`

---

## KORAK 18: Dodatne informacije (otherInfo)
**Opomba**: Ta del ni vključen v priloženo JSON schema, vendar obstaja v ValidationManager

---

## 📍 Naslovne Validacije

### Trenutne naslovne validacije
- **Naslov**: Kombinirano polje (`streetAddress` ali `singleClientStreetAddress`)
  - Validacija: Samo preveri da ni prazno
- **Poštna številka**: Trenutno brez specifične validacije
- **Kraj**: Trenutno brez specifične validacije
- **⚠️ ZA IMPLEMENTACIJO LOČENIH POLJ IN VALIDACIJ**: Glej `epic_input_form_enhancement.md`

## 📅 Datumske Validacije

### Splošna pravila za datumske razpone

Vsi datumski razponi v sistemu sledijo istemu principu:

1. **"Datum od" (začetni datum)**:
   - Privzeto prazno polje (`null`)
   - Format: dd.mm.yyyy
   - Omejitev: če je "datum do" že vnesen, "datum od" ne sme biti večji

2. **"Datum do" (končni datum)**:
   - Privzeto prazno polje (`null`)
   - Format: dd.mm.yyyy
   - Omejitev: MORA biti večji ali enak "datumu od"
   - Pri vnosu: avtomatska omejitev z `min_value = datum_od`
   - Pri shranjevanju: dodatna validacija

### Implementirani datumski razponi

| Polje | Validacija | Napaka pri kršitvi |
|-------|------------|--------------------|
| **executionDeadline** | endDate >= startDate | "Končni datum ne more biti pred začetnim datumom" |
| **contractInfo** | contractDateTo >= contractDateFrom | "Končni datum ne more biti pred začetnim datumom" |
| **inspectionDates** | Vsak datum mora biti veljaven | "Neveljavni datum ogleda" |

### Implementacija v kodi

#### 1. Field Renderer (`ui/renderers/field_renderer.py`)
- Dinamično določa `min_value` in `max_value` glede na povezana polja
- Dodaja pomožno besedilo z omejitvami
- Format datuma: DD.MM.YYYY

#### 2. Validation Manager (`utils/validations.py`)
- `validate_execution_deadline()`: Preverja razpon rokov izvedbe (vrstica 2464)
- `validate_contract_info()`: Preverja razpon pogodbe (vrstica 2449-2465)
- Vse validacije vračajo specifična sporočila napak v slovenščini

## Validacijski sistem

### ValidationManager metode (iz validations.py)
- `validate_screen_1_customers()` - Validira podatke o naročniku
- `validate_screen_3_legal_basis()` - Validira pravno podlago
- `validate_screen_5_lots()` - Validira sklope
- `validate_order_type()` - Validira vrsto naročila
- `validate_screen_7_technical_specs()` - Validira tehnične specifikacije
- `validate_execution_deadline()` - Validira rok izvedbe
- `validate_price_info()` - Validira cenovne informacije
- `validate_inspection_negotiations()` - Validira ogled in pogajanja
- `validate_participation_conditions()` - Validira pogoje sodelovanja
- `validate_financial_guarantees()` - Validira finančna zavarovanja
- `validate_merila()` - Validira merila za izbor
- `validate_contract_info()` - Validira informacije o pogodbi

### Validacijske funkcije (vse v validations.py)

#### Trenutne validacije naslovov
- Validira samo ali je kombinirano polje `streetAddress` izpolnjeno
- **⚠️ ZA LOČENA POLJA**: Glej `epic_input_form_enhancement.md`

#### Finančne validacije
- **⚠️ GLEJ**: `epic_financial_validations.md` za IBAN, SWIFT, Bank validacije

### Validacije meril glede na CPV kode

#### check_cpv_requires_additional_criteria()
- **Funkcija**: Preveri katere CPV kode imajo omejitev \"Merila - cena\"
- **Omejitev**: Cena NE SME biti edino merilo
- **Sporočilo napake**: \"Cena ne sme biti edino merilo\"
- **Primer CPV kod**: 
  - 79000000-4 (Poslovne storitve)
  - 15000000-8 (Hrana, pijača, tobak)

#### check_cpv_requires_social_criteria()
- **Funkcija**: Preveri katere CPV kode zahtevajo \"Merila - socialna merila\"
- **Omejitev**: Socialna merila so OBVEZNA
- **Sporočilo napake**: \"Socialna merila so obvezna\"
- **Primer CPV kod**:
  - 55000000-0 (Hotelske, restavracijske in maloprodajne storitve)

#### validate_criteria_selection()
- **Funkcija**: Validira izbiro meril glede na CPV kode
- **Pravila**:
  1. Če CPV koda ima omejitev \"Merila - cena\" → mora biti izbrano vsaj eno dodatno merilo poleg cene
  2. Če CPV koda zahteva socialna merila → morajo biti izbrana socialna merila
  3. Če je izbrana samo cena in CPV koda to prepoveduje → napaka
  4. Vse validacije točk morajo biti > 0 za izbrana merila
  5. Vsota vseh točk mora biti 100

#### ValidationResult
- **Dataclass** za rezultate validacije
- **Polja**:
  - `is_valid`: bool - ali je validacija uspešna
  - `messages`: List[str] - sporočila napak/opozoril
  - `restricted_cpv_codes`: List[Dict] - CPV kode z omejitvami
  - `required_criteria`: List[str] - zahtevana merila

### Form Renderer komponente (iz form_renderer_old_backup.py)
- Uporablja `render_form()` funkcijo za rekurzivno renderiranje
- Podpira `render_if` pogoje za pogojno prikazovanje
- Upravlja array tipe z dinamičnim dodajanjem/odstranjevanjem
- Format številk s pikami kot ločili tisočic
- CPV selector kot custom komponenta
- Real-time validacija z FieldTypeManager

---

## Zaključek - NOVA IMPLEMENTACIJA

### Kaj Ta Dokument Predstavlja
Ta dokument služi kot **SPECIFIKACIJA** za novo implementacijo validacij:
1. **REFERENČNI PODATKI**: Vzeti iz starih implementacij (JSON schema, stari form_renderer, validations.py)
2. **NOVA ARHITEKTURA**: Implementacija v novi formi z unified lot handling
3. **NE KOPIRAMO**: Staro kodo uporabljamo samo za razumevanje pravil

### Implementacijski Pristop
1. **FAZA 1**: Pregled starih validacij in razumevanje pravil
2. **FAZA 2**: Implementacija v novi arhitekturi z upoštevanjem:
   - Unified lot handling (vse je sklop)
   - Moderne Streamlit komponente
   - Centralizirane validacije
3. **FAZA 3**: Testiranje in validacija

### Ključne Razlike Nove Implementacije
- **Unified Lots**: Naročilo brez sklopov = 1 virtualni sklop
- **Moderna Arhitektura**: Nov form renderer, ne stari
- **Boljša UX**: Real-time validacije, jasna sporočila
- **Maintainability**: Vse validacije na enem mestu

**POMEMBNO**: Implementiramo NOVO arhitekturo, stari form_renderer je SAMO referenca!
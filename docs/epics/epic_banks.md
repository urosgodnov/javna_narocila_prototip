# Epic: Šifrant Slovenskih Bank

## Pregled
Ta epic dokumentira implementacijo šifranta slovenskih bank v admin modulu. Šifrant bo omogočal centralizirano upravljanje bančnih podatkov, avtomatsko validacijo SWIFT/BIC kod in povezovanje IBAN številk z bankami.

## Cilj
Dodati šifrant slovenskih bank v admin modul za:
- Centralizirano upravljanje bančnih podatkov
- Izboljšano validacijo finančnih polj
- Avtomatsko pridobivanje banke iz IBAN
- Validacijo SWIFT kod proti uradnemu seznamu

## Obstoječi sistem

### Trenutno stanje
- **Admin modul**: Že ima tab "Organizacije" za upravljanje šifranta organizacij
- **Validacije**: SWIFT/BIC in IBAN validacije so v `utils/validations.py` (ali `utils/financial_validations.py`)
- **Bančni podatki**: Trenutno hardkodirani v kodi
- **Baza podatkov**: SQLite z obstoječimi tabelami

### Tehnološki sklad
- Frontend: Streamlit
- Backend: Python
- Baza: SQLite
- Validacije: ValidationManager

## Načrtovana rešitev

### 1. Podatkovna struktura

#### Nova tabela: `bank`
```sql
CREATE TABLE bank (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_code TEXT NOT NULL UNIQUE,  -- Koda banke (npr. "02" za NLB)
    name TEXT NOT NULL,              -- Polno ime banke
    short_name TEXT,                 -- Kratko ime (opcijsko)
    swift TEXT,                      -- SWIFT/BIC koda
    active BOOLEAN DEFAULT 1,        -- Ali je banka aktivna
    country TEXT DEFAULT 'SI',       -- Država (privzeto Slovenija)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indeks za hitro iskanje
CREATE INDEX idx_bank_code ON bank(bank_code);
CREATE INDEX idx_bank_swift ON bank(swift);
```

### 2. Admin UI komponente

#### Lokacija: `ui/admin_dashboard.py` ali `ui/admin/banks_manager.py`

#### Funkcionalnosti:
1. **Seznam bank** - Tabela z vsemi bankami
   - Stolpci: Koda, Naziv, SWIFT, Status (Aktivna/Neaktivna)
   - Sortiranje po vseh stolpcih
   - Iskanje po nazivu ali SWIFT

2. **Dodajanje banke**
   - Forma z polji:
     - Koda banke (2 znaka)
     - Polni naziv
     - Kratki naziv (opcijsko)
     - SWIFT koda (8 ali 11 znakov)
     - Status (aktivna/neaktivna)
   - Validacija pred shranjevanjem

3. **Urejanje banke**
   - Enaka forma kot dodajanje
   - Predizpolnjeni podatki
   - Možnost deaktivacije namesto brisanja

4. **Brisanje/Deaktivacija**
   - Soft delete (deaktivacija) priporočena
   - Hard delete samo za nerabljene zapise

### 3. Integracija z validacijami

#### Posodobitve v `utils/validations.py`:

```python
def get_bank_from_iban(iban: str) -> Optional[Dict]:
    """
    Pridobi banko iz IBAN številke z uporabo šifranta.
    """
    # Pridobi kodo banke iz IBAN (pozicija 5-6)
    # Poišči v bazi podatkov
    # Vrni podatke o banki ali None
    
def validate_swift_bic(swift: str) -> Tuple[bool, Optional[str]]:
    """
    Validira SWIFT kodo proti šifrantu bank.
    """
    # Osnovna format validacija
    # Preveri če SWIFT obstaja v šifrantu
    # Vrni rezultat z ustreznim sporočilom

def get_all_active_banks() -> List[Dict]:
    """
    Vrne seznam vseh aktivnih bank za dropdown.
    """
    # Query na bank tabelo
    # Cache rezultate za performance
```

### 4. Database Manager razširitve

#### V `database.py` dodaj:

```python
class BankManager:
    def create_bank_table(self):
        """Ustvari tabelo bank če ne obstaja"""
        
    def insert_bank(self, bank_data: dict):
        """Vstavi novo banko"""
        
    def update_bank(self, bank_id: int, bank_data: dict):
        """Posodobi obstoječo banko"""
        
    def get_bank_by_code(self, bank_code: str):
        """Pridobi banko po kodi"""
        
    def get_bank_by_swift(self, swift: str):
        """Pridobi banko po SWIFT kodi"""
        
    def get_all_banks(self, active_only: bool = False):
        """Pridobi vse banke"""
        
    def deactivate_bank(self, bank_id: int):
        """Deaktiviraj banko (soft delete)"""
```

### 5. Začetni podatki

#### Migration skripta: `scripts/populate_banks.py`

```python
SLOVENIAN_BANKS = [
    {"code": "01", "name": "Banka Slovenije", "swift": "BSLJSI2X"},
    {"code": "02", "name": "Nova Ljubljanska banka", "swift": "LJBASI2X"},
    {"code": "03", "name": "SKB banka", "swift": "SKBASI2X"},
    {"code": "04", "name": "Nova KBM", "swift": "KBMASI2X"},
    {"code": "05", "name": "Abanka", "swift": "ABANSI2X"},
    {"code": "06", "name": "Banka Celje", "swift": None},
    {"code": "10", "name": "Banka Intesa Sanpaolo", "swift": "BAKOSI2X"},
    {"code": "12", "name": "Raiffeisen banka", "swift": None},
    {"code": "14", "name": "Sparkasse", "swift": "KSPKSI22"},
    {"code": "17", "name": "Deželna banka Slovenije", "swift": "SZKBSI2X"},
    {"code": "19", "name": "Delavska hranilnica", "swift": "HDELSI22"},
    {"code": "24", "name": "BKS Bank", "swift": None},
    {"code": "25", "name": "Hranilnica LON", "swift": None},
    {"code": "26", "name": "Factor banka", "swift": None},
    {"code": "27", "name": "Primorska hranilnica Vipava", "swift": None},
    {"code": "28", "name": "N banka", "swift": None},
    {"code": "30", "name": "Sberbank", "swift": "SABRSI2X"},
    {"code": "33", "name": "Addiko Bank", "swift": "HAABSI22"},
    {"code": "34", "name": "Banka Sparkasse", "swift": "KSPKSI22"},
    {"code": "61", "name": "Poštna banka Slovenije", "swift": "PBSLSI22"},
]
```

## User Stories

### Story 1: Ustvari podatkovno strukturo za banke
**Kot** administrator  
**Želim** imeti tabelo za shranjevanje bančnih podatkov  
**Da** lahko centralno upravljam s šifrantom bank

**Acceptance Criteria:**
- Nova tabela `bank` ustvarjena v bazi
- Migration skripta za začetne podatke pripravljena
- BankManager class implementiran v database.py
- Vse slovenske banke vnesene kot začetni podatki

### Story 2: Implementiraj admin UI za upravljanje bank
**Kot** administrator  
**Želim** imeti uporabniški vmesnik za upravljanje bank  
**Da** lahko dodajam, urejam in odstranjujem banke

**Acceptance Criteria:**
- Nov tab "Banke" dodan v admin modul
- Seznam bank prikazan v tabeli
- Forma za dodajanje nove banke deluje
- Urejanje obstoječih bank deluje
- Deaktivacija/aktivacija bank implementirana
- UI sledi obstoječemu stilu (kot organizacije)

### Story 3: Integriraj šifrant z validacijami
**Kot** uporabnik  
**Želim** da se SWIFT kode validirajo proti šifrantu  
**Da** so vneseni podatki pravilni

**Acceptance Criteria:**
- `validate_swift_bic()` uporablja šifrant za preverjanje
- `get_bank_from_iban()` vrača podatke iz šifranta
- Avtomatsko izpolnjevanje banke pri vnosu IBAN deluje
- Cache implementiran za hitrejše delovanje
- Obstoječe validacije še vedno delujejo

## Tehnični detajli

### Performance optimizacije
- Cache za seznam bank (osvežitev ob spremembi)
- Indeksi na bank_code in swift poljih
- Lazy loading za admin UI

### Varnostni vidiki
- SQL injection prevencija (prepared statements)
- Validacija vnosov na frontend in backend
- Audit log za spremembe (opcijsko)

### Kompatibilnost
- Backward compatible - obstoječe validacije delujejo
- Soft validacija za obstoječe podatke
- Graceful fallback če šifrant ni dostopen

## Testiranje

### Unit testi
- Test CRUD operacij za BankManager
- Test validacijskih funkcij
- Test cache mehanizma

### Integration testi
- Test admin UI workflow
- Test integracije z obstoječimi validacijami
- Test migration skripte

### Manual testing checklist
- [ ] Dodajanje nove banke
- [ ] Urejanje obstoječe banke
- [ ] Deaktivacija banke
- [ ] Iskanje po bankah
- [ ] SWIFT validacija deluje
- [ ] IBAN → banka lookup deluje
- [ ] Performance je sprejemljiv

## Rollback plan

Če je potrebno razveljaviti spremembe:

1. **Baza podatkov:**
   ```sql
   DROP TABLE IF EXISTS bank;
   ```

2. **Koda:**
   - Revert commit za UI spremembe
   - Revert commit za database.py spremembe
   - Revert commit za validations.py spremembe

3. **Podatki:**
   - Obstoječi podatki niso prizadeti
   - Validacije se vrnejo na hardkodirane vrednosti

## Definition of Done

- [ ] Tabela bank ustvarjena z začetnimi podatki
- [ ] Admin UI implementiran in testiran
- [ ] Vse CRUD operacije delujejo
- [ ] Validacije integrirane s šifrantom
- [ ] Cache mehanizem implementiran
- [ ] Unit in integration testi napisani
- [ ] Dokumentacija posodobljena
- [ ] Code review opravljen
- [ ] Obstoječe funkcionalnosti še vedno delujejo

## Časovna ocena

- Story 1 (Podatkovna struktura): 4 ure
- Story 2 (Admin UI): 6 ur
- Story 3 (Integracija): 4 ure
- Testiranje: 2 uri
- **Skupaj: 16 ur (2 dni)**

## Odvisnosti

- Obstoječi admin modul mora biti funkcionalen
- SQLite baza mora biti dostopna
- Validacijski sistem mora biti pripravljen na razširitve

## Opombe

- Šifrant bank je lahko razširjen na mednarodne banke v prihodnosti
- Možnost dodajanja dodatnih polj (npr. kontakt, URL)
- Integracija z zewnętrznimi API-ji za preverjanje SWIFT kod (v2)
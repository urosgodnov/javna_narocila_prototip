# Epic: Obnovitev Validacij in Tipov Polj

## Pregled
Ta epic dokumentira vse validacije in tipe polj iz obstoječega sistema `form_renderer`, preden smo prešli na novo arhitekturo. Dokument služi kot referenca za zagotovitev, da vse validacije ostanejo konsistentne pri prehodu na nov sistem.

## Struktura Dokumenta
- **Field Type**: Tip input elementa (dropdown, text, number, date, checkbox, radio, file, textarea)
- **Validation Rules**: Validacijska pravila, ki se uporabljajo
- **Required**: Ali je polje obvezno
- **Special Features**: Posebne funkcionalnosti (npr. dinamično skrivanje/prikazovanje)

---

## KORAK 1: Informacije o naročniku (clientInfo)

### 1.1 clientInfo.name
- **Field Type**: `text`
- **Validation Rules**: 
  - Obvezno polje
  - Minimalna dolžina: 2 znaki
- **Required**: Da
- **Special Features**: /

### 1.2 clientInfo.taxNumber
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Dolžina: točno 8 številk
  - Regex: `^\d{8}$`
- **Required**: Da
- **Special Features**: Samo številke

### 1.3 clientInfo.registrationNumber
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Format: 7-mestna številka
  - Regex: `^\d{7}$`
- **Required**: Da
- **Special Features**: Samo številke

### 1.4 clientInfo.address
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Minimalna dolžina: 5 znakov
- **Required**: Da
- **Special Features**: /

### 1.5 clientInfo.postalCode
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Format: 4 številke
  - Regex: `^\d{4}$`
- **Required**: Da
- **Special Features**: Slovenski poštni kodi

### 1.6 clientInfo.city
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Minimalna dolžina: 2 znaki
- **Required**: Da
- **Special Features**: /

### 1.7 clientInfo.country
- **Field Type**: `dropdown`
- **Validation Rules**:
  - Obvezno polje
  - Privzeta vrednost: "Slovenija"
- **Required**: Da
- **Special Features**: Seznam EU držav

### 1.8 clientInfo.contactPerson
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Minimalna dolžina: 3 znaki
- **Required**: Da
- **Special Features**: /

### 1.9 clientInfo.phone
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Slovenski format: `+386` ali `0` na začetku
  - Regex: `^(\+386|0)\d{7,8}$`
- **Required**: Da
- **Special Features**: Validacija slovenskega formata

### 1.10 clientInfo.email
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Email format
  - Regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- **Required**: Da
- **Special Features**: Email validacija

### 1.11 clientInfo.website
- **Field Type**: `text`
- **Validation Rules**:
  - Neobvezno polje
  - URL format če izpolnjeno
  - Regex: `^(https?://)?[\w\-]+(\.[\w\-]+)+[/#?]?.*$`
- **Required**: Ne
- **Special Features**: URL validacija

### 1.12 clientInfo.legalRepresentative
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Minimalna dolžina: 3 znaki
- **Required**: Da
- **Special Features**: /

### 1.13 clientInfo.trrAccount
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - IBAN format: SI56 + 15 številk
  - Regex: `^SI56\d{15}$`
- **Required**: Da
- **Special Features**: TRR validacija

### 1.14 clientInfo.bankName
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Minimalna dolžina: 3 znaki
- **Required**: Da
- **Special Features**: /

### 1.15 clientInfo.bicCode
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - BIC/SWIFT format: 8 ali 11 znakov
  - Regex: `^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$`
- **Required**: Da
- **Special Features**: BIC validacija

### 1.16 clientInfo.multipleClients
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: Omogoča vnos več naročnikov

### 1.17 clientInfo.additionalClients (če multipleClients = true)
- **Field Type**: `array of objects`
- **Validation Rules**:
  - Minimalno 2 vnosa če je multipleClients = true
  - Vsak vnos ima enaka polja kot glavni naročnik
- **Required**: Da, če multipleClients = true
- **Special Features**: Dinamično dodajanje/odstranjevanje

---

## KORAK 2: Informacije o projektu (projectInfo)

### 2.1 projectInfo.title
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Minimalna dolžina: 5 znakov
- **Required**: Da
- **Special Features**: /

### 2.2 projectInfo.referenceNumber
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Format: alfanumerični
- **Required**: Da
- **Special Features**: /

### 2.3 projectInfo.cpvCode
- **Field Type**: `dropdown` + `text` (autocomplete)
- **Validation Rules**:
  - Obvezno polje
  - Format: 8 številk + opis
  - Regex za kodo: `^\d{8}$`
- **Required**: Da
- **Special Features**: Autocomplete iz CPV baze

### 2.4 projectInfo.additionalCpvCodes
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: Omogoča dodatne CPV kode

### 2.5 projectInfo.additionalCpvList (če additionalCpvCodes = true)
- **Field Type**: `array of dropdowns`
- **Validation Rules**:
  - Vsaka koda mora biti veljavna CPV
  - Minimalno 1 dodatna koda
- **Required**: Da, če additionalCpvCodes = true
- **Special Features**: Dinamično dodajanje

### 2.6 projectInfo.procurementType
- **Field Type**: `dropdown`
- **Validation Rules**:
  - Obvezno polje
  - Možnosti: "Blago", "Storitve", "Gradnje"
- **Required**: Da
- **Special Features**: /

### 2.7 projectInfo.procurementCategory
- **Field Type**: `dropdown`
- **Validation Rules**:
  - Obvezno polje
  - Možnosti odvisne od procurementType
- **Required**: Da
- **Special Features**: Pogojno prikazovanje glede na procurementType

### 2.8 projectInfo.estimatedValue
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno polje
  - Pozitivna številka
  - Format: decimalne številke z 2 mesti
- **Required**: Da
- **Special Features**: EUR format

### 2.9 projectInfo.greenProcurement
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 2.10 projectInfo.socialAspects
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 2.11 projectInfo.innovativeProcurement
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

---

## KORAK 3: Pravna podlaga (legalBasis)

### 3.1 legalBasis.primaryLegalBasis
- **Field Type**: `dropdown`
- **Validation Rules**:
  - Obvezno polje
  - Seznam zakonov (ZJN-3, itd.)
- **Required**: Da
- **Special Features**: /

### 3.2 legalBasis.additionalLegalBasis
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: Omogoča dodatne pravne podlage

### 3.3 legalBasis.additionalBasisList (če additionalLegalBasis = true)
- **Field Type**: `array of text`
- **Validation Rules**:
  - Minimalno 1 vnos
  - Vsak vnos min 5 znakov
- **Required**: Da, če additionalLegalBasis = true
- **Special Features**: Dinamično dodajanje

### 3.4 legalBasis.euFunding
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 3.5 legalBasis.euProgram (če euFunding = true)
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno če euFunding = true
  - Minimalna dolžina: 3 znaki
- **Required**: Da, če euFunding = true
- **Special Features**: /

### 3.6 legalBasis.euProjectName (če euFunding = true)
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno če euFunding = true
  - Minimalna dolžina: 3 znaki
- **Required**: Da, če euFunding = true
- **Special Features**: /

---

## KORAK 4: Postopek oddaje in sklopi (submissionProcedure, lotsInfo)

### 4.1 submissionProcedure.procedureType
- **Field Type**: `dropdown`
- **Validation Rules**:
  - Obvezno polje
  - Možnosti: "Odprti postopek", "Omejeni postopek", "Konkurenčni dialog", itd.
- **Required**: Da
- **Special Features**: /

### 4.2 submissionProcedure.acceleratedProcedure
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 4.3 submissionProcedure.acceleratedReason (če acceleratedProcedure = true)
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno če acceleratedProcedure = true
  - Minimalna dolžina: 10 znakov
- **Required**: Da, če acceleratedProcedure = true
- **Special Features**: /

### 4.4 submissionProcedure.electronicAuction
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 4.5 submissionProcedure.auctionDetails (če electronicAuction = true)
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno če electronicAuction = true
  - Minimalna dolžina: 10 znakov
- **Required**: Da, če electronicAuction = true
- **Special Features**: /

### 4.6 lotsInfo.hasLots
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: Ključno polje - določa ali gre za sklope

### 4.7 lotsInfo.submitForAllLots (če hasLots = true)
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 4.8 lotsInfo.submitForMultipleLots (če hasLots = true)
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 4.9 lotsInfo.maxLotsPerBidder (če submitForMultipleLots = true)
- **Field Type**: `number`
- **Validation Rules**:
  - Pozitivno celo število
  - Minimalno: 1
- **Required**: Da, če submitForMultipleLots = true
- **Special Features**: /

---

## KORAK 5: Konfiguracija sklopov (lotConfiguration) - samo če hasLots = true

### 5.1 lotConfiguration.numberOfLots
- **Field Type**: `number`
- **Validation Rules**:
  - Minimalno: 2
  - Maksimalno: 99
  - Celo število
- **Required**: Da
- **Special Features**: /

### 5.2 lotConfiguration.lots (array)
Za vsak sklop:

#### 5.2.1 lotName
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Minimalna dolžina: 3 znaki
- **Required**: Da
- **Special Features**: /

#### 5.2.2 lotDescription
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno polje
  - Minimalna dolžina: 10 znakov
- **Required**: Da
- **Special Features**: /

#### 5.2.3 lotCpvCode
- **Field Type**: `dropdown` + `text` (autocomplete)
- **Validation Rules**:
  - Obvezno polje
  - Veljavna CPV koda
- **Required**: Da
- **Special Features**: Autocomplete iz CPV baze

#### 5.2.4 lotEstimatedValue
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno polje
  - Pozitivna številka
  - Format: decimalne številke z 2 mesti
- **Required**: Da
- **Special Features**: EUR format

---

## KORAKI 6-13: Polja, ki se ponavljajo za vsak sklop (ali enkrat če ni sklopov)

## KORAK 6: Vrsta naročila (orderType)

### 6.1 orderType.orderNature
- **Field Type**: `dropdown`
- **Validation Rules**:
  - Obvezno polje
  - Možnosti: "Enkratno naročilo", "Okvirni sporazum", "Dinamični nabavni sistem"
- **Required**: Da
- **Special Features**: /

### 6.2 orderType.frameworkDuration (če orderNature = "Okvirni sporazum")
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno če orderNature = "Okvirni sporazum"
  - Pozitivno celo število (meseci)
  - Maksimalno: 48
- **Required**: Da, če okvirni sporazum
- **Special Features**: /

### 6.3 orderType.frameworkParticipants (če orderNature = "Okvirni sporazum")
- **Field Type**: `dropdown`
- **Validation Rules**:
  - Obvezno če orderNature = "Okvirni sporazum"
  - Možnosti: "En gospodarski subjekt", "Več gospodarskih subjektov"
- **Required**: Da, če okvirni sporazum
- **Special Features**: /

### 6.4 orderType.maxParticipants (če frameworkParticipants = "Več")
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno če več subjektov
  - Minimalno: 2
  - Celo število
- **Required**: Da, če več subjektov
- **Special Features**: /

### 6.5 orderType.estimatedValue
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno polje
  - Pozitivna številka
  - Format: decimalne številke z 2 mesti
- **Required**: Da
- **Special Features**: EUR format

### 6.6 orderType.valueIncludesVat
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 6.7 orderType.isCofinanced
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: Ključno za sofinanciranje

### 6.8 orderType.cofinancers (če isCofinanced = true)
- **Field Type**: `array of objects`
- **Validation Rules**:
  - Minimalno 1 sofinancer
  - Vsak sofinancer mora imeti vse obvezne podatke
- **Required**: Da, če isCofinanced = true
- **Special Features**: Dinamično dodajanje/brisanje

Za vsakega sofinancerja:
- **name**: text, obvezno, min 3 znaki
- **percentage**: number, obvezno, 0-100
- **amount**: number, obvezno, pozitivno
- **source**: dropdown, obvezno (EU sredstva, državni proračun, itd.)

---

## KORAK 7: Tehnične specifikacije (technicalSpecifications)

### 7.1 technicalSpecifications.hasSpecs
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 7.2 technicalSpecifications.specDocuments (če hasSpecs = true)
- **Field Type**: `file upload` (multiple)
- **Validation Rules**:
  - Minimalno 1 dokument če hasSpecs = true
  - Dovoljeni formati: PDF, DOC, DOCX, XLS, XLSX
  - Maksimalna velikost: 10MB per file
- **Required**: Da, če hasSpecs = true
- **Special Features**: Multiple file upload

### 7.3 technicalSpecifications.description
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno polje
  - Minimalna dolžina: 20 znakov
- **Required**: Da
- **Special Features**: Rich text editor

### 7.4 technicalSpecifications.standards
- **Field Type**: `multiselect` ali `checkboxes`
- **Validation Rules**:
  - Neobvezno
- **Required**: Ne
- **Special Features**: ISO standardi, CE oznake, itd.

### 7.5 technicalSpecifications.samples
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 7.6 technicalSpecifications.sampleDetails (če samples = true)
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno če samples = true
  - Minimalna dolžina: 10 znakov
- **Required**: Da, če samples = true
- **Special Features**: /

---

## KORAK 8: Rok izvedbe (executionDeadline)

### 8.1 executionDeadline.deadlineType
- **Field Type**: `radio` ali `dropdown`
- **Validation Rules**:
  - Obvezno polje
  - Možnosti: "Določen datum", "Obdobje v mesecih", "Obdobje v dnevih"
- **Required**: Da
- **Special Features**: /

### 8.2 executionDeadline.startDate (če deadlineType = "Določen datum")
- **Field Type**: `date`
- **Validation Rules**:
  - Obvezno če deadlineType = "Določen datum"
  - Datum mora biti v prihodnosti
- **Required**: Da, če določen datum
- **Special Features**: Date picker

### 8.3 executionDeadline.endDate (če deadlineType = "Določen datum")
- **Field Type**: `date`
- **Validation Rules**:
  - Obvezno če deadlineType = "Določen datum"
  - Mora biti po startDate
- **Required**: Da, če določen datum
- **Special Features**: Date picker

### 8.4 executionDeadline.durationMonths (če deadlineType = "Obdobje v mesecih")
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno če deadlineType = "Obdobje v mesecih"
  - Pozitivno celo število
  - Maksimalno: 120
- **Required**: Da, če obdobje v mesecih
- **Special Features**: /

### 8.5 executionDeadline.durationDays (če deadlineType = "Obdobje v dnevih")
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno če deadlineType = "Obdobje v dnevih"
  - Pozitivno celo število
  - Maksimalno: 3650
- **Required**: Da, če obdobje v dnevih
- **Special Features**: /

### 8.6 executionDeadline.renewalOption
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 8.7 executionDeadline.renewalDetails (če renewalOption = true)
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno če renewalOption = true
  - Minimalna dolžina: 10 znakov
- **Required**: Da, če renewalOption = true
- **Special Features**: /

---

## KORAK 9: Cenovne informacije (priceInfo)

### 9.1 priceInfo.priceFormula
- **Field Type**: `dropdown`
- **Validation Rules**:
  - Obvezno polje
  - Možnosti: "Fiksna cena", "Cena na enoto", "Kombinacija", "Drugo"
- **Required**: Da
- **Special Features**: /

### 9.2 priceInfo.priceFormulaOther (če priceFormula = "Drugo")
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno če priceFormula = "Drugo"
  - Minimalna dolžina: 10 znakov
- **Required**: Da, če drugo
- **Special Features**: /

### 9.3 priceInfo.priceRevision
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 9.4 priceInfo.revisionFormula (če priceRevision = true)
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno če priceRevision = true
  - Minimalna dolžina: 10 znakov
- **Required**: Da, če priceRevision = true
- **Special Features**: /

### 9.5 priceInfo.advancePayment
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 9.6 priceInfo.advancePercentage (če advancePayment = true)
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno če advancePayment = true
  - Razpon: 0-100
  - Decimalne številke dovoljene
- **Required**: Da, če advancePayment = true
- **Special Features**: Percentage slider

### 9.7 priceInfo.paymentDeadline
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno polje
  - Pozitivno celo število (dni)
  - Tipično: 30, 60, 90
- **Required**: Da
- **Special Features**: /

---

## KORAK 10: Ogled in pogajanja (inspectionInfo, negotiationsInfo)

### 10.1 inspectionInfo.siteVisit
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 10.2 inspectionInfo.visitAppointments (če siteVisit = true)
- **Field Type**: `array of objects`
- **Validation Rules**:
  - Minimalno 1 termin
- **Required**: Da, če siteVisit = true
- **Special Features**: Dinamično dodajanje terminov

Za vsak termin:
- **date**: date, obvezno, v prihodnosti
- **time**: time, obvezno
- **location**: text, obvezno, min 5 znakov
- **contactPerson**: text, obvezno, min 3 znaki
- **contactPhone**: text, obvezno, telefon format

### 10.3 inspectionInfo.mandatoryVisit
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: Samo če siteVisit = true

### 10.4 negotiationsInfo.includeNegotiations
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 10.5 negotiationsInfo.negotiationTopic (če includeNegotiations = true)
- **Field Type**: `multiselect`
- **Validation Rules**:
  - Minimalno 1 izbira
  - Možnosti: "Cena", "Rok dobave", "Tehnične zahteve", "Garancijski pogoji", "Drugo"
- **Required**: Da, če includeNegotiations = true
- **Special Features**: /

### 10.6 negotiationsInfo.negotiationRounds (če includeNegotiations = true)
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno če includeNegotiations = true
  - Pozitivno celo število
  - Tipično: 1-3
- **Required**: Da, če includeNegotiations = true
- **Special Features**: /

---

## KORAK 11: Pogoji sodelovanja (participationAndExclusion, participationConditions)

### 11.1 participationAndExclusion.exclusionReasons
- **Field Type**: `multiselect` ali `checkboxes`
- **Validation Rules**:
  - Obvezno polje
  - Minimalno 1 razlog
- **Required**: Da
- **Special Features**: Seznam iz ZJN-3, člen 75

### 11.2 participationAndExclusion.espd
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: ESPD obrazec

### 11.3 participationConditions.economicCapacity
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 11.4 participationConditions.economicRequirements (če economicCapacity = true)
- **Field Type**: `array of objects`
- **Validation Rules**:
  - Minimalno 1 zahteva
- **Required**: Da, če economicCapacity = true
- **Special Features**: Dinamično dodajanje

Za vsako zahtevo:
- **requirement**: textarea, obvezno, min 10 znakov
- **minValue**: number, neobvezno, pozitivno
- **proof**: text, obvezno, min 5 znakov

### 11.5 participationConditions.technicalCapacity
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 11.6 participationConditions.technicalRequirements (če technicalCapacity = true)
- **Field Type**: `array of objects`
- **Validation Rules**:
  - Minimalno 1 zahteva
- **Required**: Da, če technicalCapacity = true
- **Special Features**: Dinamično dodajanje

Za vsako zahtevo:
- **requirement**: textarea, obvezno, min 10 znakov
- **proof**: text, obvezno, min 5 znakov

### 11.7 participationConditions.references
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 11.8 participationConditions.referenceRequirements (če references = true)
- **Field Type**: `array of objects`
- **Validation Rules**:
  - Minimalno 1 referenca
- **Required**: Da, če references = true
- **Special Features**: Dinamično dodajanje

Za vsako referenco:
- **description**: textarea, obvezno, min 10 znakov
- **minValue**: number, neobvezno, pozitivno
- **period**: text, obvezno (npr. "zadnjih 3 let")
- **numberOfReferences**: number, obvezno, pozitivno celo število

---

## KORAK 12: Finančna zavarovanja in variantne ponudbe (financialGuarantees, variantOffers)

### 12.1 financialGuarantees.requireGuarantees
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 12.2 financialGuarantees.bidGuarantee (če requireGuarantees = true)
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 12.3 financialGuarantees.bidGuaranteeAmount (če bidGuarantee = true)
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno če bidGuarantee = true
  - Pozitivna številka
  - Lahko je fiksni znesek ali procent
- **Required**: Da, če bidGuarantee = true
- **Special Features**: EUR ali % format

### 12.4 financialGuarantees.bidGuaranteeType (če bidGuarantee = true)
- **Field Type**: `dropdown`
- **Validation Rules**:
  - Obvezno če bidGuarantee = true
  - Možnosti: "Bančna garancija", "Kavcijsko zavarovanje", "Drugo"
- **Required**: Da, če bidGuarantee = true
- **Special Features**: /

### 12.5 financialGuarantees.performanceGuarantee (če requireGuarantees = true)
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 12.6 financialGuarantees.performanceGuaranteeAmount (če performanceGuarantee = true)
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno če performanceGuarantee = true
  - Pozitivna številka
  - Tipično: 5-10% vrednosti
- **Required**: Da, če performanceGuarantee = true
- **Special Features**: EUR ali % format

### 12.7 financialGuarantees.warrantyGuarantee (če requireGuarantees = true)
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 12.8 financialGuarantees.warrantyGuaranteeAmount (če warrantyGuarantee = true)
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno če warrantyGuarantee = true
  - Pozitivna številka
  - Tipično: 5% vrednosti
- **Required**: Da, če warrantyGuarantee = true
- **Special Features**: EUR ali % format

### 12.9 variantOffers.allowVariants
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 12.10 variantOffers.variantConditions (če allowVariants = true)
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno če allowVariants = true
  - Minimalna dolžina: 20 znakov
- **Required**: Da, če allowVariants = true
- **Special Features**: /

### 12.11 variantOffers.minRequirements (če allowVariants = true)
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno če allowVariants = true
  - Minimalna dolžina: 20 znakov
- **Required**: Da, če allowVariants = true
- **Special Features**: /

---

## KORAK 13: Merila za izbor (selectionCriteria)

### 13.1 selectionCriteria.criteriaType
- **Field Type**: `radio`
- **Validation Rules**:
  - Obvezno polje
  - Možnosti: "Najnižja cena", "Ekonomsko najugodnejša ponudba"
- **Required**: Da
- **Special Features**: /

### 13.2 selectionCriteria.criteria (če criteriaType = "Ekonomsko najugodnejša ponudba")
- **Field Type**: `array of objects`
- **Validation Rules**:
  - Minimalno 2 merili
  - Vsota uteži = 100%
- **Required**: Da, če ekonomsko najugodnejša
- **Special Features**: Dinamično dodajanje meril

Za vsako merilo:
- **name**: text, obvezno, min 3 znaki
- **description**: textarea, obvezno, min 10 znakov
- **weight**: number, obvezno, 0-100
- **subCriteria**: array of objects, neobvezno

### 13.3 selectionCriteria.evaluationFormula
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno polje
  - Minimalna dolžina: 20 znakov
- **Required**: Da
- **Special Features**: Matematična formula

### 13.4 selectionCriteria.tieBreaker
- **Field Type**: `textarea`
- **Validation Rules**:
  - Neobvezno
  - Če izpolnjeno, min 10 znakov
- **Required**: Ne
- **Special Features**: /

---

## KORAK 14: Pogodba (contractInfo)

### 14.1 contractInfo.contractDuration
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno polje
  - Pozitivno celo število (meseci)
- **Required**: Da
- **Special Features**: /

### 14.2 contractInfo.extensionOption
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 14.3 contractInfo.extensionDuration (če extensionOption = true)
- **Field Type**: `number`
- **Validation Rules**:
  - Obvezno če extensionOption = true
  - Pozitivno celo število (meseci)
- **Required**: Da, če extensionOption = true
- **Special Features**: /

### 14.4 contractInfo.extensionConditions (če extensionOption = true)
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno če extensionOption = true
  - Minimalna dolžina: 10 znakov
- **Required**: Da, če extensionOption = true
- **Special Features**: /

### 14.5 contractInfo.subcontracting
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 14.6 contractInfo.subcontractingDetails (če subcontracting = true)
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno če subcontracting = true
  - Minimalna dolžina: 10 znakov
- **Required**: Da, če subcontracting = true
- **Special Features**: /

### 14.7 contractInfo.contractChanges
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 14.8 contractInfo.changeConditions (če contractChanges = true)
- **Field Type**: `textarea`
- **Validation Rules**:
  - Obvezno če contractChanges = true
  - Minimalna dolžina: 20 znakov
- **Required**: Da, če contractChanges = true
- **Special Features**: /

---

## KORAK 15: Dodatne informacije (otherInfo)

### 15.1 otherInfo.additionalInfo
- **Field Type**: `textarea`
- **Validation Rules**:
  - Neobvezno
  - Če izpolnjeno, min 10 znakov
- **Required**: Ne
- **Special Features**: Rich text editor

### 15.2 otherInfo.attachments
- **Field Type**: `file upload` (multiple)
- **Validation Rules**:
  - Neobvezno
  - Dovoljeni formati: PDF, DOC, DOCX, XLS, XLSX, ZIP
  - Maksimalna velikost: 20MB per file
- **Required**: Ne
- **Special Features**: Multiple file upload

### 15.3 otherInfo.contactForQuestions
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Email format
- **Required**: Da
- **Special Features**: Email validacija

### 15.4 otherInfo.questionsDeadline
- **Field Type**: `datetime`
- **Validation Rules**:
  - Obvezno polje
  - Mora biti pred rokom za oddajo ponudb
- **Required**: Da
- **Special Features**: Date-time picker

### 15.5 otherInfo.submissionDeadline
- **Field Type**: `datetime`
- **Validation Rules**:
  - Obvezno polje
  - Mora biti v prihodnosti
  - Minimalno 15 dni od objave (za odprti postopek)
- **Required**: Da
- **Special Features**: Date-time picker

### 15.6 otherInfo.openingDate
- **Field Type**: `datetime`
- **Validation Rules**:
  - Obvezno polje
  - Mora biti po submissionDeadline
- **Required**: Da
- **Special Features**: Date-time picker

### 15.7 otherInfo.openingLocation
- **Field Type**: `text`
- **Validation Rules**:
  - Obvezno polje
  - Minimalna dolžina: 5 znakov
- **Required**: Da
- **Special Features**: /

### 15.8 otherInfo.publicOpening
- **Field Type**: `checkbox`
- **Validation Rules**:
  - Boolean vrednost
- **Required**: Ne
- **Special Features**: /

### 15.9 otherInfo.language
- **Field Type**: `dropdown`
- **Validation Rules**:
  - Obvezno polje
  - Privzeto: "Slovenski"
  - Možnosti: "Slovenski", "Angleški", "Slovenski in angleški"
- **Required**: Da
- **Special Features**: /

---

## Posebne validacijske funkcije

### Regex validacije
```python
# TRR račun (IBAN)
TRR_REGEX = r'^SI56\d{15}$'

# BIC/SWIFT koda
BIC_REGEX = r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$'

# Email
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Telefon (slovenski)
PHONE_REGEX = r'^(\+386|0)\d{7,8}$'

# Davčna številka
TAX_REGEX = r'^\d{8}$'

# Matična številka
REGISTRATION_REGEX = r'^\d{7}$'

# Poštna številka (slovenska)
POSTAL_REGEX = r'^\d{4}$'

# CPV koda
CPV_REGEX = r'^\d{8}$'

# URL
URL_REGEX = r'^(https?://)?[\w\-]+(\.[\w\-]+)+[/#?]?.*$'
```

### Pogojne validacije
- Če `multipleClients = true` → zahtevaj `additionalClients` array
- Če `hasLots = true` → zahtevaj `lotConfiguration`
- Če `isCofinanced = true` → zahtevaj `cofinancers` array
- Če `acceleratedProcedure = true` → zahtevaj `acceleratedReason`
- Če `euFunding = true` → zahtevaj `euProgram` in `euProjectName`
- Če `hasSpecs = true` → zahtevaj vsaj 1 dokument
- Če `siteVisit = true` → zahtevaj vsaj 1 termin
- Če `includeNegotiations = true` → zahtevaj temo in število krogov
- Če `requireGuarantees = true` → omogoči izbiro tipov zavarovanj
- Če `allowVariants = true` → zahtevaj pogoje in minimalne zahteve
- Če `criteriaType = "Ekonomsko najugodnejša"` → zahtevaj merila z utežmi

### Array validacije
- `additionalClients`: min 2 če je `multipleClients = true`
- `lots`: min 2, max 99
- `cofinancers`: min 1 če je `isCofinanced = true`
- `visitAppointments`: min 1 če je `siteVisit = true`
- `economicRequirements`: min 1 če je `economicCapacity = true`
- `technicalRequirements`: min 1 če je `technicalCapacity = true`
- `referenceRequirements`: min 1 če je `references = true`
- `criteria`: min 2 če je `criteriaType = "Ekonomsko najugodnejša"`

### Cross-field validacije
- `endDate` > `startDate`
- `questionsDeadline` < `submissionDeadline`
- `openingDate` > `submissionDeadline`
- Vsota `cofinancers.percentage` = 100%
- Vsota `criteria.weight` = 100%
- `maxLotsPerBidder` ≤ število sklopov

---

## Uporabniške zgodbe (User Stories)

### Zgodba 1: Osnovni vnos naročnika
**Kot** uporabnik
**Želim** vnesti podatke o naročniku
**Da** lahko ustvarim novo javno naročilo

**Acceptance Criteria:**
- Vsa obvezna polja morajo biti validirana
- TRR, davčna in matična številka morajo ustrezati formatom
- Email in telefon morata biti pravilnega formata

### Zgodba 2: Upravljanje sklopov
**Kot** uporabnik
**Želim** razdeliti naročilo na sklope
**Da** lahko upravljam kompleksnejša naročila

**Acceptance Criteria:**
- Če izberem sklope, moram vnesti vsaj 2
- Vsak sklop mora imeti svoje CPV kode in vrednosti
- Koraki 6-13 se morajo ponoviti za vsak sklop

### Zgodba 3: Sofinanciranje
**Kot** uporabnik
**Želim** dodati sofinancerje
**Da** lahko dokumentiram vire financiranja

**Acceptance Criteria:**
- Možnost dodajanja/brisanja sofinancerjev
- Vsota deležev mora biti 100%
- Vsak sofinancer mora imeti vse podatke

### Zgodba 4: Merila za izbor
**Kot** uporabnik
**Želim** definirati merila za izbor
**Da** lahko objektivno ocenim ponudbe

**Acceptance Criteria:**
- Pri ekonomsko najugodnejši ponudbi moram vnesti vsaj 2 merili
- Vsota uteži mora biti 100%
- Vsako merilo mora imeti opis in utež

### Zgodba 5: Finančna zavarovanja
**Kot** uporabnik
**Želim** določiti zahtevana zavarovanja
**Da** se zaščitim pred tveganji

**Acceptance Criteria:**
- Možnost izbire različnih tipov zavarovanj
- Za vsako zavarovanje moram določiti znesek/procent
- Pogojno prikazovanje na osnovi izbire

---

## Implementacijske opombe

1. **Session State Management**: Vsi podatki se shranjujejo v `st.session_state` z dot notation (npr. `clientInfo.name`)

2. **Lot Prefixing**: Ko imamo sklope, se vsa polja prefixajo z `lot_X.` (npr. `lot_0.orderType.estimatedValue`)

3. **Dynamic Steps**: Koraki se dinamično generirajo glede na `hasLots` in število sklopov

4. **Real-time Validation**: Validacija se izvaja ob vsakem koraku naprej

5. **File Uploads**: Datoteke se shranjujejo v session state kot base64 encoded strings

6. **Conditional Fields**: Polja se dinamično prikazujejo/skrivajo glede na vrednosti drugih polj

7. **Array Management**: Dinamični arrays (sofinancerji, reference, itd.) uporabljajo add/remove gumbe

8. **CPV Integration**: CPV kode se validirajo proti bazi in omogočajo autocomplete

9. **Date Validations**: Datumi se preverjajo za logično konsistentnost (npr. end > start)

10. **Percentage Validations**: Procenti se validirajo na vsoto 100% kjer je to potrebno

---

## Testni scenariji

1. **Minimum Path**: Izpolni samo obvezna polja brez sklopov
2. **Maximum Complexity**: Vsi sklopi, sofinancerji, dodatne opcije
3. **Validation Errors**: Preveri vse error messagee
4. **Cross-field Dependencies**: Preveri pogojne prikaze
5. **Array Operations**: Dodajanje/brisanje dinamičnih elementov
6. **File Uploads**: Nalaganje različnih formatov in velikosti
7. **Session Persistence**: Podatki se ohranijo med koraki
8. **Back Navigation**: Podatki ostanejo pri navigaciji nazaj
9. **Lot Switching**: Preklapljanje med sklopi ohrani podatke
10. **Final Submission**: Vsi podatki se pravilno shranijo v bazo

---

## Zaključek

Ta epic predstavlja popolno dokumentacijo vseh validacij in tipov polj v obstoječem sistemu. Služi kot referenca za:
- Migracijo na novo arhitekturo
- Testiranje
- Zagotavljanje backwards compatibility
- Dokumentacijo za razvijalce

Vse validacije morajo biti prenesene v nov sistem brez izgube funkcionalnosti.
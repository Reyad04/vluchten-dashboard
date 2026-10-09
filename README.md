# Case 3 — Vluchten en vertraging op Zürich Airport

Streamlit-dashboard over vluchten van en naar Zürich (2019–2020): **wanneer vertrekken vluchten te laat, hoe goed is dat te voorspellen en wat veranderde in 2020?**

> Dit document is ons overzicht van de opdracht: wat er moet, hoe het beoordeeld wordt, welke data we hebben en waar de valkuilen zitten. Gebruik de checklists onderaan vóór het inleveren.

## Dashboard starten

Gebruik **Python 3.12**. Pak het hele project uit en open een terminal in de map met `app.py`:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open daarna het lokale adres dat Streamlit toont. De drie CSV's staan al in `data/`; je hoeft ze niet te hernoemen of handmatig aan te passen. `requirements.txt` bevat de versies waarop het dashboard is getest. Voor Streamlit Cloud upload je dezelfde projectstructuur naar GitHub en kies je `app.py` als startbestand. De online publicatie moet nog gebeuren.

---

## 1. Deadlines

| Wat                                          | Wanneer                                                     |
| -------------------------------------------- | ----------------------------------------------------------- |
| Dashboard inleveren (online link of bestand) | **Donderdag 8 oktober**                               |
| Presentatie                                  | **Vrijdag 9 oktober** — max. 10 min + ±5 min vragen |
| Indeling presentaties                        | Wordt nog bekendgemaakt                                     |

---

## 2. De opdracht in één alinea

Maak in Python een **interactief Streamlit-dashboard** op basis van het vluchtrooster van Zürich. Maak zelf een vertragingskolom, zoek uit waar vertraging vandaan komt (tijdstip, vliegtuigtype, baan, bestemming, drukte, weer) en bouw daar een voorspelling mee — inclusief hoe goed die is en waar hij ernaast zit. Zet daarnaast **2019 (normaal jaar) tegenover 2020 (coronajaar)**: niet als één gemiddelde, maar naast elkaar. Dit zijn suggesties; als we iets interessanters vinden, mogen we daarachteraan. Data-inspectie is verplicht.

### 2.1 Onze onderzoeksvraag en afbakening

> **Wanneer vertrekken vluchten vanaf Zürich minstens 15 minuten te laat, en hoe goed kunnen we dat voorspellen met informatie uit het vluchtschema?**

- **Eenheid:** één vertrek (`LSV == "S"`). Een vertrek is *vertraagd* als de werkelijke vertrektijd minstens 15 minuten na de geplande tijd ligt. Aankomsten blijven in het overzicht van het totale vliegverkeer, maar worden niet met vertrekken gemengd in de analyse van vertrekvertraging.
- **Beschrijven:** onderzoek het werkelijke percentage vertraagde vertrekken per **gepland vertrekuur**, over ieder volledig jaar. De beschrijvende uurvergelijking toont alleen groepen met minstens 100 vertrekken, zodat zeer kleine groepen de boodschap niet bepalen. Deze grens verwijdert geen vluchten uit de bron of de andere analyses. Aantallen staan in de tooltip. Vergelijk 2019 en 2020 afzonderlijk, zowel in vliegverkeer als in vertrekvertraging.
- **Bronnen combineren:** koppel het dagelijkse weer in Zürich aan de **per dag samengevatte vertrekvertragingen**. Vergelijk dagen met een hoogste windstoot onder 40 km/u en vanaf 40 km/u binnen elk jaar. Dit is een zelfgekozen vergelijkingsgrens, geen officiële windlimiet. Ontbrekende windstoten krijgen de groep *Onbekend* en worden niet met nul ingevuld. Het gevonden verband bewijst geen oorzaak.
- **Voorspellen:** gebruik eerdere percentages per uur als schatting voor nieuwe vertrekken op dat uur. Waren 30 van 100 eerdere vertrekken om 10:00 laat, dan is de schatting voor dat uur 30%. Dit schat een percentage voor een groep, niet een zeker ja/nee voor een individuele vlucht. De berekening gebruikt tellen, delen en gemiddelden.
- **Toetsen:** bereken de uurpercentages met januari–oktober 2019 en vergelijk ze met november–december 2019 en, afzonderlijk, 2020. De testgegevens bepalen de schattingen niet. De grafiek en de afwijking in procentpunten laten zien waar de voorspelling ernaast zit.
- **Berekende tijdtrend:** vergelijk twee blokken van vier leerweken, deel de verandering door vier en trek die wekelijkse stap vier weken door. Vergelijk met de echte vier testweken. Zo worden ook de tijdtrend, geldigheidsperiode en toetsing uit de rubric concreet afgedekt.

Het dashboard voert deze analyses uit op de aangeleverde bestanden. De conclusies gaan over deze historische gegevens: een samenhang bewijst geen oorzaak en een eenvoudig model hoeft niet goed te voorspellen.

---

## 3. Beoordeling

We krijgen **twee cijfers uit dezelfde presentatie**. Elk cijfer is het gemiddelde van 4 criteria.

| Introduction to Data Science (IDS) | Visual Analytics (VA)   |
| ---------------------------------- | ----------------------- |
| Opschonen                          | Informatiearchitectuur  |
| Data naar informatie               | Lijngrafiek             |
| Voorspellen                        | Kaart                   |
| Presentatievaardigheden            | Presentatievaardigheden |

Niveaus per criterium: Ontbreekt (1) · Onvoldoende (4,5) · Voldoende (6) · Goed (7,5) · Uitstekend (9).

### 3.1 Voorwaarden met aftrek (gaan van BEIDE cijfers af)

| Eis                                                                                                                                                                                          | Niet gehaald                                                     |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Dashboard gepubliceerd via**GitHub + Streamlit Cloud**, te openen met een link. Een **schone clone** van de repo draait zonder handmatige stappen.                               | **−1,0** op beide cijfers                                 |
| Presentatie duurt**maximaal 10 minuten** (excl. vragen).                                                                                                                               | **−1,0** op beide cijfers                                 |
| Overgenomen code (Streamlit-voorbeelden, plot-snippets, StackOverflow) staat**met bron** in de code en is **aangepast aan onze data**. Iedereen kan uitleggen wat die code doet. | Criterium waar die code in zit is**hoogstens Onvoldoende** |

---

## 4. Rubric per criterium — wat is nodig voor een 9?

Elk niveau bouwt voort op het vorige. Hieronder per criterium wat er per niveau bij komt.

### Opschonen (IDS)

- **6** — Data geïnspecteerd; fouten benoemd (ontbrekende waarden, dubbele rijen, onmogelijke waarden) en gezegd wat ermee is gedaan.
- **7,5** — Elke ingreep is beargumenteerd én het effect op het **aantal observaties** is benoemd (bv. "323.461 → 318.902 rijen").
- **9** — Ook verantwoord waar **níets** is verwijderd (een uitschieter die echt lijkt blijft staan, met uitleg), en laten zien dat de **conclusie niet afhangt van die keuze** (bv. analyse met en zonder uitschieters).

### Data naar informatie (IDS)

- **6** — Verdelingen en samenvattingen tonen en benoemen wat opvalt.
- **7,5** — Minstens één **nieuwe variabele** berekend (verandering over tijd, verhouding, aggregatie per gebied) die een inzicht geeft dat niet in de bronkolommen zat. *Vertraging zelf telt hiervoor; drukte per uur of afstand ook.*
- **9** — **Datasets koppelen** of profielen opstellen, en daarmee een vraag beantwoorden die met één dataset niet kan (bv. rooster + weer → "hangen wind en vertraging op dagniveau samen?", rooster + luchthavens → afstand vs. vertraging).

### Voorspellen (IDS)

- **6** — Verloop in de tijd beschrijven en zeggen wat dat voor de toekomst betekent, inclusief de **aanname** daarachter.
- **7,5** — Trend **doorgetrokken met een berekening** (lineair of regressie) en benoemen voor welke periode die aanname redelijk is.
- **9** — Voorspelling **getoetst op data die er niet in zat** of voorzien van een **bandbreedte**. Benoemen welke gebeurtenis de voorspelling zou breken. **Ons plan:** toets de eerdere uurpercentages én de berekende tijdtrend op latere, ongeziene data. De rubric schrijft geen specifieke machine-learningbibliotheek voor; eenvoudige berekeningen zijn bruikbaar als ze correct worden getoetst en uitgelegd.

### Informatiearchitectuur (VA)

- **6** — Duidelijke eerste laag: bij openen meteen te zien waar het over gaat, zonder te filteren.
- **7,5** — Detail pas op verzoek (tabs, expanders, selecties); eerste beeld rustig; doorstaat de **3-secondentest**.
- **9** — Verantwoorden wat bewust is **weggelaten** en waarom de boodschap daar sterker van wordt. De tweede laag beantwoordt **precies de vraag die het eerste beeld oproept**.

### Lijngrafiek (VA) — lat ligt hoger

- **6** — Lijndiagram van het **aantal vliegtuigen op de airport per tijdseenheid**, met titel en aslabels; tijdseenheid past bij de vraag.
- **7,5** — Uitgesplitst naar een **tweede dimensie** (aankomst vs. vertrek, of per bestemming) en **interactief over de x-as** (bv. range slider), zonder dat het onleesbaar wordt.
- **9** — Drukke en rustige periodes **naast elkaar** te leggen; **gaten in de reeks zichtbaar** in plaats van doorverbonden (geen lijn door een periode zonder data); aggregatie en schaal verantwoord.

### Kaart (VA) — lat ligt hoger

- **6** — Elk punt is een vliegveld, met legenda; puntgrootte of kleur toont een grootheid (bv. aantal vluchten).
- **7,5** — Ingekleurd naar aantal met legenda, **gebieden te selecteren**, en het patroon benoemd.
- **9** — Kleurschaal past bij het datatype (**opklimmend/sequentieel** voor aantallen, **geen regenboog**) en gaat om met de **scheve verdeling** (kwantielen of logschaal), zodat niet één vliegveld alle kleur opeist.

### Presentatievaardigheden (IDS + VA)

- **6** — Voorstellen, kort zeggen wat we behandelen, dashboardonderdelen toelichten.
- **7,5** — Beginnen met **de vraag en waarom** we die kozen; contact met publiek; **rode draad**.
- **9** — Opmerkelijke punten **vertellen én aanwijzen**; de voorspelling volgt logisch uit wat al gepresenteerd is; de **conclusie beantwoordt de vraag**.

---

## 5. Data

| Dataset                          | Bestand                                   | Bron                                                                                                             |
| -------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Vluchtrooster Zürich            | `schedule_airport.csv`                  | Brightspace                                                                                                      |
| Luchthavens                      | `airports-extended.csv`                 | [Kaggle – OpenFlights](https://www.kaggle.com/datasets/open-flights/airports-train-stations-and-ferry-terminals) |
| Weer Zürich-Kloten (dagwaarden) | `export.csv` (Meteostat, station 06670) | [Meteostat](https://meteostat.net/)                                                                               |
| Vluchtprofielen (optioneel)      | `flightdata.zip`                        | Brightspace                                                                                                      |

### 5.1 Vluchtrooster — `schedule_airport.csv`

323.461 vluchten van/naar Zürich, 1 jan 2019 t/m 31 dec 2020, 295 bestemmingen, 16 kolommen.

| Kolom                     | Betekenis                                                                        |
| ------------------------- | -------------------------------------------------------------------------------- |
| `STD`                   | Datum (`dd/mm/jjjj`)                                                           |
| `STA_STD_ltc`           | Geplande tijd (lokaal): aankomst bij inbound, vertrek bij outbound               |
| `ATA_ATD_ltc`           | Werkelijke tijd → verschil met geplande tijd =**vertraging (zelf maken)** |
| `LSV`                   | `L` = landing (inbound), `S` = start (outbound), ±50/50                     |
| `Org/Des`               | Herkomst/bestemming als**ICAO-code** (4 letters, bv. `LFPG`)             |
| `ACT` / `RWY`         | Vliegtuigtype (bv.`A321`) / gebruikte baan                                     |
| `FLT`, `TAR`, `GAT` | Vluchtnummer, geplande gate, werkelijke gate                                     |
| `DL1`–`IX2`          | Vertragingscodes, vaak`-`                                                      |

### 5.2 Luchthavens — `airports-extended.csv`

10.668 locaties. **Onze versie is het ruwe Kaggle-bestand**: komma-gescheiden, **zonder header**, decimale punt. (De opdracht beschrijft de *clean*-versie met `sep=";"` en `decimal=","` — die instructie geldt dus níet voor ons bestand.)

```python
cols = ["id", "name", "city", "country", "iata", "icao", "lat", "lon",
        "altitude", "timezone", "dst", "tz", "type", "source"]
airports = pd.read_csv("data/airports-extended.csv", header=None,
                       names=cols, na_values="\\N")
```

Bevindingen bij inspectie:

- `type`: 7.750 airports, 1.422 stations, 101 ports, 1.395 unknown.
- 3.043 rijen zonder ICAO-code (`\N`), 4.200 zonder IATA.
- **Koppelen op ICAO, niet op IATA**. `data.py` vertaalt eerst zeven gebruikte 3-lettercodes naar ICAO. Na deze stap blijven bij de koppeling **96 vluchten** zonder coördinaten: 94 met onbekende bestemming (`#N/A`) en twee met de codes `SEQU` en `ZGUA`. Zij blijven in de vluchtentellingen, maar verschijnen niet op de kaart.

### 5.3 Weer — `export.csv` (Meteostat daily)

Dagwaarden vanaf 1-1-2019 tot en met 31-12-2020, 11 kolommen:

```python
weather = pd.read_csv("data/export.csv", encoding="utf-8-sig", parse_dates=["date"])
```

Bevindingen voor 2019–2020 (731 dagen, compleet):

- `snow`, `wdir` en `tsun` zijn **volledig leeg** en worden in `data.py` verwijderd.
- `prcp` mist **24 dagen**; die waarden blijven leeg.
- Temperatuur, windsnelheid, windstoten en luchtdruk zijn in deze 731 rijen compleet.
- `daily` koppelt het weer op **datum** aan de per dag berekende cijfers van **vertrekken**. Dezelfde dag gemeten weer is verklarende informatie achteraf, geen vooraf bekende weersvoorspelling. Iedere dag telt in de windstotenvergelijking even zwaar. `wpgt` is de hoogste windstoot van de dag in km/u; `wspd` is de gemiddelde windsnelheid. Een dagmaximum zegt niet hoeveel wind er bij ieder vertrek stond.

---

## 6. Valkuilen (uit de opdracht)

1. **Middernacht bij vertraging.** Gepland 23:55, vertrokken 00:10 = 15 min te laat. `data.py` corrigeert zes waargenomen gevallen met een vroege werkelijke tijd na een laat gepland tijdstip. De regel neemt aan dat gepland vanaf 18:00 en werkelijk tot 06:00 bij de volgende dag hoort; andersom nemen we de vorige dag aan. De echte uitvoeringsdatum ontbreekt, dus dit is een aanname. Controleer zulke gevallen afzonderlijk: een positief verschil van meer dan 12 uur kan ook een echte lange vertraging zijn en mag niet automatisch worden teruggedraaid.
2. **Koppelen op ICAO** (zie 5.2).
3. **Kies een gebied voor de kaart.** Begin met **Europa** voor een leesbaar patroon en bied een keuze voor een ander gebied of de hele wereld. Gebruik een oplopende kleurschaal voor aantallen en kwantielen of een logschaal bij grote verschillen. Noem de 96 vluchten zonder kaartlocatie.
4. **2019 en 2020 niet middelen.** Andere aantallen én andere bestemmingen; altijd naast elkaar tonen.
5. **Caching.** 32 MB: één keer inlezen met `@st.cache_data`, anders laadt alles opnieuw bij elke klik.
6. **Schone clone moet draaien.** Data in de repo (of automatisch downloaden), relatieve paden, `requirements.txt` volledig.

---

## 7. Repo-structuur

```
├── app.py                 # Streamlit-dashboard
├── data.py                # Data opschonen, samenvatten en eenvoudige voorspellingen berekenen
├── requirements.txt       # alle packages
├── README.md
└── data/
    ├── schedule_airport.csv
    ├── airports-extended.csv
    └── export.csv         # Meteostat daily, station Zürich-Kloten 06670
```

---

## 8. Dashboardplan — van vraag naar conclusie

De leesvolgorde is **vraag → context → onderzoek → voorspelling → conclusie**. Eerst ziet de bezoeker waar de gegevens over gaan, daarna wanneer vertraging vaker voorkomt, en pas daarna hoe goed eerdere gegevens de latere vertrekken voorspellen. Zo volgt de voorspelling uit het beschreven uurpatroon. Het volledige jaaroverzicht in de onderzoekstab wordt niet gebruikt om de voorspelling te berekenen: daarvoor blijft alleen januari–oktober 2019 de leerdata.

| Onderdeel | Wat is zichtbaar? | Waarom staat het er? |
| --- | --- | --- |
| **Eerste beeld** | Onderzoeksvraag, definitie van vertrekvertraging, leesvolgorde en vier kerncijfers. | Een bezoeker ziet direct het onderwerp en hoe het verhaal is opgebouwd. |
| **1. Context** | Twee weekgrafieken naast elkaar: 2019 en 2020, met aankomst en vertrek, dezelfde schaal en een maandfilter. Daaronder de kaart met jaar- en gebiedskeuze, logkleur en verbindingslijnen vanaf Zürich. Bij beide onderdelen staat een bevinding. | Laat zien waarom de jaren afzonderlijk worden onderzocht en over welke vliegveldverbindingen de gegevens gaan. |
| **2. Vertraging onderzoeken** | Werkelijke vertrekvertraging per uur voor beide jaren, gevolgd door de vergelijking van dagen met windstoten onder en vanaf 40 km/u. Beide grafieken staan direct in beeld, met aantallen in de tooltip en een bevinding eronder. | Beantwoordt wanneer vertraging vaker voorkomt en toont wat de gekoppelde weergegevens toevoegen. |
| **3. Voorspelling toetsen** | Eerdere uurpercentages tegenover de werkelijk gemeten percentages op latere data, een keuze tussen testperioden en de afwijking in procentpunten. | Laat zien of het uurpatroon bruikbaar is als voorspelling, en waar de schatting ernaast zit. |
| **4. Conclusie en verantwoording** | Het antwoord op de onderzoeksvraag, de beperkingen en de verantwoording met opschoonlog, uitschieterscontrole en bronnen. | De eindconclusie en verantwoording hebben één vaste plek. Ze vatten de volledige analyse samen; plaatselijke grafiekfilters veranderen deze samenvatting niet. |
| **Details op verzoek** | De vierweekse tijdtrend in een uitklapper in tab 3; de opschoonlog met uitschieterscontrole in een uitklapper in tab 4. | Extra onderbouwing blijft beschikbaar zonder het eerste beeld te overladen. |

**Bewust beperkt:** er zijn vier tabs. Verkeer en kaart staan samen bij de context; de weeranalyse staat bij het onderzoek. De eindconclusie, beperkingen en verantwoording verschijnen alleen in de vierde tab. Korte bevindingen blijven bij de bijbehorende grafieken, zodat het verhaal ook tijdens het lezen van de analyses duidelijk is. De uurvergelijking beantwoordt de vraag "wanneer?" voordat we gaan voorspellen. De aparte druktegrafiek, beslisboom en verwarringsmatrix blijven weggelaten. De voorspelling gebruikt alleen gepland vertrekuur. Vliegtuigtype en baan blijven buiten de gekozen afbakening. De opdracht noemt deze factoren als suggesties; we hoeven ze niet allemaal te onderzoeken.

### Conclusie van het onderzoek

- **Wanneer?** Onder uren met minstens 100 vertrekken heeft 13:00 in beide jaren het hoogste aandeel te late vertrekken: **47,0% in 2019** en **19,8% in 2020**. Het uurpatroon is een samenhang en bewijst geen oorzaak.
- **Wat voegt het weer toe?** Bij de grens van 40 km/u ligt het gemiddelde dagelijkse aandeel late vertrekken op dagen met hogere windstoten in 2019 **7,2 procentpunt** hoger; in 2020 is het verschil **1,6 procentpunt**. Het verschil in 2020 is klein en hangt af van de gekozen grens. Seizoen en drukte kunnen ook een rol spelen; we kunnen geen oorzakelijk effect van wind vaststellen.
- **Hoe goed voorspellen we?** De eerdere uurpercentages wijken gemiddeld **11,7 procentpunt** af op november–december 2019 en **16,4 procentpunt** op 2020. Alleen het geplande uur biedt hier beperkte voorspelkracht. De tijdtrend mist de decemberstijging en laat zien hoe kwetsbaar het doortrekken van een recent patroon is.

Als context telt 2020 **66,7% minder vluchten** dan 2019. Dat is geen bewijs dat minder verkeer op zichzelf het lagere aandeel vertraging veroorzaakt. De conclusie gaat over deze historische gegevens en geeft geen garantie voor een individuele vlucht of een toekomstig jaar.

### De voorspelling uitleggen

1. Kies de eerdere vluchten: **januari–oktober 2019** (103.723 vertrekken).
2. Tel per gepland uur het aandeel vertrekken met minstens 15 minuten vertraging. Bijvoorbeeld: 30 late vertrekken / 100 vertrekken × 100 = 30%.
3. Gebruik dat percentage als schatting voor hetzelfde uur bij nieuwe vluchten. Voor een nooit eerder gezien uur gebruiken we het gemiddelde van alle eerdere vluchten.
4. Toets afzonderlijk op **november–december 2019** (17.712 vertrekken) en **heel 2020** (40.314 vertrekken).
5. Bereken per uur de absolute afstand tussen voorspeld en werkelijk percentage. Het gemiddelde van die afstanden is de gemiddelde afwijking **per uur**, waarbij ieder uur even zwaar telt. Het is geen percentage correct voorspelde individuele vluchten.

De gemiddelde afwijking is **11,7 procentpunt** op de test uit 2019 en **16,4 procentpunt** op 2020. Bij uren met minstens 100 testvluchten is de grootste afwijking in 2019 om 17:00: voorspeld 40,5%, werkelijk 21,7%. De historische uurpercentages zijn dus geen blijvend betrouwbare kansen. Veranderende seizoenen, drukte en corona kunnen het patroon beïnvloeden.

### De tijdtrend uitleggen

We gebruiken acht complete weken eindigend op **13 oktober–1 december 2019** als leerdata en vier weken eindigend op **8–29 december 2019** als testdata.

```text
wekelijkse stap = (gemiddelde laatste 4 leerweken − gemiddelde eerste 4 leerweken) / 4
voorspelling = percentage laatste leerweek + aantal weken vooruit × wekelijkse stap
```

De berekende stap is −2,06 procentpunt per week. De vierweekse voorspelling mist de decemberstijging en wijkt gemiddeld **19,0 procentpunt** af. De aanname dat de recente verandering vier weken doorgaat werkt hier slecht. Benoem dit eerlijk, samen met gebeurtenissen die het patroon kunnen breken. Dit is lineair doortrekken met optellen en delen, zonder sklearn of regressiebibliotheek.

### Resultaat uit gekoppelde bronnen

We vergelijken de **hoogste windstoot per dag** (`wpgt`): onder **40 km/u** tegenover **vanaf 40 km/u**. De grens staat als `WINDSTOOT_GRENS` in `data.py` en wordt ook voor de labels in `app.py` gebruikt. Het is een zelfgekozen ronde indeling, geen officiële luchtvaart- of veiligheidsgrens. Beide groepen bevatten in elk jaar minstens 100 dagen.

In 2019 is het gemiddelde dagelijkse aandeel late vertrekken **28,2%** bij windstoten onder 40 km/u (263 dagen) en **35,4%** vanaf 40 km/u (102 dagen): een verschil van **7,2 procentpunt**. In 2020 is dat **12,7%** (266 dagen) tegenover **14,4%** (100 dagen): een verschil van **1,6 procentpunt**. Iedere dag telt even zwaar; we tellen dus niet alle vluchten van een windgroep samen. De windstoten zijn in dit bestand compleet; eventuele ontbrekende metingen krijgen een aparte groep *Onbekend*.

De keuze van de grens is gecontroleerd: bij 35 en 45 km/u blijft het verschil in 2019 positief (**7,0 en 6,6 procentpunt**). In 2020 verandert het verschil van **−0,8 naar +3,0 procentpunt**. Het verband in 2020 is dus gevoelig voor de indeling. Deze samenhang bewijst geen oorzaak: seizoen en drukte kunnen ook verschillen. De windrichting ontbreekt, dus we onderzoeken geen zijwind. Het gemeten dagmaximum wordt alleen achteraf beschreven en blijft buiten de voorspelling op basis van het vluchtschema.

### Code en controle

- `app.py` regelt het scherm. De functies en zeven codeonderdelen hebben uitleg bij de gebruikte pandas- en Plotly-stappen. Er zijn vier tabs, zes gewone visualisaties (waaronder de kaart) en één tijdtrendgrafiek in een uitklapper. De eindconclusie en verantwoording staan alleen in tab 4.
- `data.py` bevat de voorbereiding en berekeningen. De oorspronkelijke opschoning is behouden; voorspellingen gebruiken gemiddelden en eenvoudige rekenstappen.
- De verbindingslijnen op de kaart zijn **schematische vliegveldverbindingen**, geen werkelijk gevlogen paden. De rode stip markeert Zürich; lijnen volgen de geselecteerde vliegvelden en kunnen worden uitgezet. De kaart gebruikt online achtergrondtegels.
- De uitschieterscontrole vergelijkt percentages én de voorspellingsfout met en zonder extremen in de leer- en testdata. De uurafwijking in 2019 blijft afgerond **11,7 procentpunt** in beide gevallen.
- De code wordt technisch gecontroleerd op brondata, tellingen, testperioden, ontbrekende waarden, kaartlijnen en bediening. De visuele browserweergave is hier niet gecontroleerd. Online publiceren en de live presentatie blijven nog uit te voeren.

### Naloop van de code en inhoud

De opzet sluit inhoudelijk aan op de rubric: context, beschrijvende analyse, toetsing op latere gegevens en een conclusie die de onderzoeksvraag beantwoordt. De weervergelijking gebruikt gekoppelde bronnen en maakt geen oorzakelijke claim. De voorspelling is eenvoudig en heeft flinke afwijkingen; die beperking wordt gemeten en benoemd. Het uiteindelijke cijfer hangt ook af van de verplichte publicatie en de presentatie, waarin we de keuzes en aannames moeten kunnen uitleggen.

- In `app.py` staat het zoeken naar de hoogste rij in één korte hulpfunctie. De twee testtabellen worden voorbereid en daarna opnieuw gebruikt voor de grafiek en conclusie.
- In `data.py` worden groepen en geplande uren opnieuw gebruikt. De tijdtrend heeft een eenvoudige loop; de weekindeling heeft benoemde tussenstappen en uitleg over ontbrekende dagen.
- De functies hebben korte beschrijvingen. Comments leggen de gebruikte stappen en aannames uit, waaronder `map`, `value_counts`, `unstack`, `resample` en de middernachtcorrectie. De berekeningen blijven zonder sklearn.
- Bij deze wijziging is de regenvergelijking vervangen door windstoten. De overige **15 data-uitkomsten** blijven gelijk aan de voorgaande versie. In **drie dashboardstanden** zijn de overige grafieken, kerncijfers, filters en tabellen gelijk gebleven. De windberekening is afzonderlijk gecontroleerd, inclusief de grens van 40 km/u en ontbrekende metingen.

---

## 9. Presentatie (max. 10 minuten)

| Tijd        | Onderdeel                                                          |
| ----------- | ------------------------------------------------------------------ |
| 0:00–0:45  | Voorstellen, **onderzoeksvraag en waarom** |
| 0:45–1:30  | Kort naar **tab 4, verantwoording:** databronnen, opschoonkeuzes en uitschieters |
| 1:30–3:15  | **Context:** verkeer 2019/2020 en kaart; wijs de opvallende bevindingen aan |
| 3:15–5:00  | **Onderzoek:** werkelijke uurpercentages, daarna windstoten per jaar |
| 5:00–7:00  | **Voorspelling:** latere testgegevens, fout en grootste afwijking |
| 7:00–8:30  | Vierweekse tijdtrend in de uitklapper: aanname, horizon en testfout |
| 8:30–9:30  | **Tab 4, conclusie:** antwoord op de vraag en grenzen van het resultaat |

De laatste halve minuut is ruimte voor uitloop, zodat de presentatie binnen tien minuten blijft.

---

## 10. Bronvermelding

| Bron                                                                                                                      | Gebruikt voor                      |
| ------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Brightspace — `schedule_airport.csv`                                                                       | Vluchtrooster     |
| [Kaggle — OpenFlights airports](https://www.kaggle.com/datasets/open-flights/airports-train-stations-and-ferry-terminals) | Coördinaten luchthavens           |
| [Meteostat](https://meteostat.net/) — station 06670                                                                       | Weerdata Zürich-Kloten            |
| [Streamlit-documentatie](https://docs.streamlit.io/develop/api-reference) | Tabs, filters, caching en tabellen |
| [Plotly Express](https://plotly.com/python/plotly-express/) | Grafieken en kaart |
| [Plotly Scattermap](https://plotly.com/python-api-reference/generated/plotly.graph_objects.Scattermap.html) | Verbindingslijnen en Zürich-marker |
| [Meteostat-weereenheden](https://dev.meteostat.net/parameters.html) | Windstoten en gemiddelde windsnelheid in km/u; neerslag in mm |
| [pandas-documentatie](https://pandas.pydata.org/docs/user_guide/) | Data inlezen, koppelen en samenvatten |
| ChatGPT/Codex | Ondersteuning bij code en documentatie; code aangepast aan en gecontroleerd op de aangeleverde data |

---

## 11. Controle vóór inleveren

- [ ] Onderzoeksvraag en definitie van vertrekvertraging staan meteen in beeld. De tabs volgen context → onderzoek → voorspelling → conclusie en verantwoording; de vierde tab beantwoordt precies de onderzoeksvraag.
- [ ] Opschoonlog toont per ingreep de reden, het aantal geraakte observaties en het aantal overgebleven rijen. Uitschieters bewust behouden; relevante conclusie ook zonder deze rijen controleren.
- [ ] Dagelijkse weervergelijking gebruikt alleen vertrekken en beantwoordt een vraag met de gekoppelde datasets.
- [ ] Lijngrafiek: aantallen per week, aankomst/vertrek, vergelijking 2019/2020, x-asinteractie, labels, zichtbare gaten en verantwoorde schaal.
- [ ] Kaart: één punt per vliegveld, legenda, aantallen, gebiedskeuze en geschikte oplopende kleurverdeling.
- [ ] Voorspelling: berekende korte tijdtrend met aanname en horizon; uurpercentages getoetst op latere ongeziene data; fouten en beperkingen besproken.
- [ ] GitHub-repo bevat alle benodigde data en dependencies; dashboard werkt na een schone clone via een Streamlit-link. Overgenomen code heeft bronvermelding en is uitlegbaar.
- [ ] Presentatie live vanuit het dashboard, maximaal 10 minuten, met aangewezen bevindingen en een antwoord op de onderzoeksvraag.

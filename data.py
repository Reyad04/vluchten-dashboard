"""
Data voorbereiden voor het dashboard over vluchten en vertraging op Zürich Airport.

Wat doet dit script?
    1. Vluchten inlezen en opschonen (schedule_airport.csv)
    2. Per vlucht de vertraging uitrekenen
    3. Weer inlezen en opschonen (export.csv)
    4. Luchthavens inlezen (airports-extended.csv) en koppelen aan de bestemmingen
    5. Samenvattingen maken per dag en per bestemming
    6. Uurpercentages en een vierweekse tijdtrend berekenen en toetsen

Wat komt eruit? Vier tabellen:
    flights        1 rij per vlucht
    daily          1 rij per dag, met vertrekvertraging en het weer
    destinations   1 rij per jaar en bestemming, met coordinaten voor de kaart
    log            een tabel met de opschoonstappen en hun effect op het aantal rijen

Lees eerst maak_alle_data(): die roept de voorbereidende functies in volgorde aan.
De functies daaronder maken de tabellen voor de grafieken en de eenvoudige voorspellingen.
Bron voor de pandas-stappen: https://pandas.pydata.org/docs/user_guide/
"""

import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# INSTELLINGEN (hier kun je dingen aanpassen)
# ---------------------------------------------------------------------------

TE_LAAT_VANAF = 15      # een vlucht is "te laat" vanaf 15 minuten
EXTREEM_VANAF = 180     # 180 minuten (3 uur) of meer te vroeg/te laat noemen we "extreem"
WINDSTOOT_GRENS = 40    # km/u: zelfgekozen grens voor de vergelijking, geen officiële windlimiet
DATA_MAP = Path(__file__).resolve().parent / "data"  # werkt ook vanuit een andere werkmap

# Zeven bestemmingen staan in het bestand met 3 letters. Voor de kaart hebben we
# de code van 4 letters nodig (ICAO). Daarom vertalen we ze met dit woordenboek.
IATA_NAAR_ICAO = {
    "BER": "EDDB",
    "ISL": "LTBA",
    "ECN": "LCEN",
    "BGW": "ORBI",
    "GRV": "URMG",
    "DWC": "OMDW",
    "NBC": "UWKE",
}

# Het luchthavenbestand heeft geen kopregel, dus we geven de kolommen zelf een naam.
# De volgorde is dezelfde als in het bestand.
LUCHTHAVEN_KOLOMMEN = ["ID", "Name", "City", "Country", "IATA", "ICAO", "Latitude",
                       "Longitude", "Altitude", "Timezone", "DST", "Tz_database",
                       "Type", "Source"]

# ---------------------------------------------------------------------------
# LOGBOEK: hier schrijven we elke opschoonstap op (handig voor je presentatie)
# ---------------------------------------------------------------------------

def noteer(log, stap, uitleg, aantal_rijen_geraakt, rijen_over):
    """Voeg een opschoonkeuze en de rijtelling toe aan het logboek."""
    log.append({
        "Stap": stap,
        "Wat is er gedaan": uitleg,
        "Rijen geraakt": aantal_rijen_geraakt,
        "Rijen over": rijen_over,
    })

# ---------------------------------------------------------------------------
# STAP 1 en 2: VLUCHTEN
# ---------------------------------------------------------------------------

def laad_vluchten(pad, log):
    """Lees vluchten, bereken vertraging en leg de opschoonkeuzes vast."""
    # Het bestand begint met een onzichtbaar teken (BOM). Met utf-8-sig lezen we dat goed in.
    flights = pd.read_csv(pad, encoding="utf-8-sig")
    noteer(log, "Inlezen", "schedule_airport.csv ingelezen", 0, len(flights))
    # Dubbele rijen: rijen die in alle kolommen precies hetzelfde zijn.
    aantal_voor = len(flights)
    flights = flights.drop_duplicates()
    noteer(log, "Dubbele rijen", "Volledig identieke rijen verwijderd",
           aantal_voor - len(flights), len(flights))
    # In 94 rijen staat bij de bestemming "#N/A". Pandas leest dat als leeg (NaN).
    # We weten niet waar die vluchten heen gingen, maar de vertraging is wel bekend.
    # Daarom houden we de rijen en vullen we "ONBEKEND" in.
    aantal_leeg = flights["Org/Des"].isna().sum()
    flights["Org/Des"] = flights["Org/Des"].fillna("ONBEKEND")
    noteer(log, "Onbekende bestemming", "'#N/A' vervangen door 'ONBEKEND'",
           aantal_leeg, len(flights))
    # De 3-letter codes vervangen door 4-letter codes (zie IATA_NAAR_ICAO bovenaan)
    aantal_omgezet = flights["Org/Des"].isin(IATA_NAAR_ICAO).sum()
    flights["Org/Des"] = flights["Org/Des"].replace(IATA_NAAR_ICAO)
    noteer(log, "ICAO-code", "3-letter codes omgezet naar 4-letter codes",
           aantal_omgezet, len(flights))
    # Datum en tijden staan als tekst in het bestand. We zetten ze om naar echte datums
    # en tijden, zodat we ermee kunnen rekenen.
    # errors="coerce" betekent: kan iets niet gelezen worden, dan wordt het leeg i.p.v. een foutmelding.
    flights["Date"] = pd.to_datetime(flights["STD"], format="%d/%m/%Y", errors="coerce")
    gepland = pd.to_timedelta(flights["STA_STD_ltc"], errors="coerce")
    werkelijk = pd.to_timedelta(flights["ATA_ATD_ltc"], errors="coerce")
    # Datum + tijd = volledig tijdstip
    flights["Planned"] = flights["Date"] + gepland
    flights["Actual"] = flights["Date"] + werkelijk
    # Rijen waarvan het tijdstip niet te lezen was, verwijderen we (in deze data zijn dat er 0)
    aantal_voor = len(flights)
    flights = flights.dropna(subset=["Planned", "Actual"])
    noteer(log, "Onleesbare datum/tijd", "Rijen zonder geldig tijdstip verwijderd",
           aantal_voor - len(flights), len(flights))
    # DE VERTRAGING: werkelijk min gepland, in minuten.
    # Positief = te laat. Negatief = te vroeg.
    verschil = flights["Actual"] - flights["Planned"]
    flights["Delay_minutes"] = verschil.dt.total_seconds() / 60
    # PROBLEEM MET MIDDERNACHT:
    # De datum in het bestand is de GEPLANDE datum. Een vlucht gepland om 22:40 die om 00:05
    # vertrekt, krijgt dan de verkeerde dag. De vertraging wordt dan -1355 minuten
    # in plaats van +85 minuten.
    # AANNAME: een geplande tijd vanaf 18:00 en een werkelijke tijd tot 06:00 hoort bij de volgende dag.
    # Andersom nemen we de vorige dag aan. De echte kalenderdatum van de uitvoering ontbreekt.
    # We corrigeren alleen deze gevallen; andere lange vertragingen blijven behouden.
    plan_uur = flights["Planned"].dt.hour + flights["Planned"].dt.minute / 60
    echt_uur = flights["Actual"].dt.hour + flights["Actual"].dt.minute / 60
    na_middernacht = (plan_uur >= 18) & (echt_uur <= 6)
    voor_middernacht = (plan_uur <= 6) & (echt_uur >= 18)
    # += en -= betekenen: pas de bestaande waarde aan en bewaar de uitkomst.
    flights.loc[na_middernacht, "Delay_minutes"] += 1440  # één dag erbij
    flights.loc[voor_middernacht, "Delay_minutes"] -= 1440  # één dag eraf
    # Met de gecorrigeerde vertraging rekenen we het werkelijke tijdstip opnieuw uit
    flights["Actual"] = flights["Planned"] + pd.to_timedelta(flights["Delay_minutes"], unit="min")
    noteer(log, "Middernacht", "Vertraging gecorrigeerd voor vluchten die over middernacht gingen",
           na_middernacht.sum() + voor_middernacht.sum(), len(flights))
    # Extreme vertragingen markeren we in een aparte kolom. We verwijderen ze NIET,
    # want een grote vertraging is niet automatisch een meetfout. De oorzaak is onbekend.
    flights["Is_extreme"] = flights["Delay_minutes"].abs() >= EXTREEM_VANAF
    noteer(log, "Extreme vertraging", "Gemarkeerd in kolom 'Is_extreme' (niet verwijderd)",
           flights["Is_extreme"].sum(), len(flights))
    # Extra kolommen die handig zijn voor je grafieken
    flights["Flight_type"] = flights["LSV"].map({"L": "Aankomst", "S": "Vertrek"})  # L=landing, S=start
    flights["Is_late"] = flights["Delay_minutes"] >= TE_LAAT_VANAF   # True of False
    flights["Year"] = flights["Date"].dt.year
    flights["Month"] = flights["Date"].dt.month                      # 1 t/m 12
    flights["Year_month"] = flights["Date"].dt.strftime("%Y-%m")     # bijvoorbeeld "2019-03"
    flights["Weekday"] = flights["Date"].dt.day_name()               # Monday, Tuesday, ...
    flights["Weekday_number"] = flights["Date"].dt.dayofweek        # maandag=0, zondag=6
    flights["Planned_hour"] = flights["Planned"].dt.hour             # 0 t/m 23
    flights = flights.drop(columns=["Identifier"])   # deze kolom hebben we niet meer nodig
    flights = flights.reset_index(drop=True)         # rijnummers weer netjes vanaf 0
    return flights

# ---------------------------------------------------------------------------
# STAP 3: WEER
# ---------------------------------------------------------------------------

def laad_weer(pad, log):
    """Lees dagwaarden; onbekende neerslag blijft onbekend."""
    # parse_dates zet de kolom "date" meteen om naar echte datums
    weer = pd.read_csv(pad, encoding="utf-8-sig", parse_dates=["date"])
    noteer(log, "Inlezen weer", "export.csv ingelezen", 0, len(weer))
    # Sneeuw, windrichting en zonuren zijn helemaal leeg. Eerst controleren we of dat echt zo is
    # en dan pas gooien we de kolom weg.
    lege_kolommen = []
    for kolom in ["snow", "wdir", "tsun"]:
        if weer[kolom].isna().all():
            lege_kolommen.append(kolom)
    weer = weer.drop(columns=lege_kolommen)
    noteer(log, "Lege kolommen", "Kolommen die helemaal leeg zijn verwijderd: " + str(lege_kolommen),
           0, len(weer))  # er verdwijnen kolommen, maar geen rijen
    # Op een paar dagen is er geen neerslag gemeten. We laten die leeg.
    # Invullen met 0 zou betekenen dat we doen alsof het droog was, en dat weten we niet.
    noteer(log, "Neerslag ontbreekt", "Dagen zonder neerslag blijven leeg (rij blijft staan)",
           weer["prcp"].isna().sum(), len(weer))
    return weer

# ---------------------------------------------------------------------------
# STAP 4: LUCHTHAVENS
# ---------------------------------------------------------------------------

def laad_luchthavens(pad, log):
    """Houd vliegvelden met een unieke ICAO-code over voor de kaartkoppeling."""
    # - header=None: er is geen kopregel in het bestand
    # - names=...: we geven de kolommen zelf een naam
    # - na_values=["\\N"]: in dit bestand betekent \N "onbekend", dat maken we leeg
    # - keep_default_na=False: anders leest pandas de tekst "NA" ook als leeg
    luchthavens = pd.read_csv(pad, header=None, names=LUCHTHAVEN_KOLOMMEN,
                              encoding="utf-8-sig", na_values=["\\N"], keep_default_na=False)
    noteer(log, "Inlezen luchthavens", "airports-extended.csv ingelezen", 0, len(luchthavens))
    # Het bestand bevat ook treinstations en havens. Wij hebben alleen vliegvelden nodig.
    aantal_voor = len(luchthavens)
    luchthavens = luchthavens[luchthavens["Type"] == "airport"]
    noteer(log, "Alleen vliegvelden", "Treinstations, havens en 'unknown' verwijderd",
           aantal_voor - len(luchthavens), len(luchthavens))
    # Zonder ICAO-code kunnen we niet koppelen, dus die luchthavens verwijderen we
    aantal_voor = len(luchthavens)
    luchthavens = luchthavens.dropna(subset=["ICAO"])
    noteer(log, "Zonder ICAO-code", "Luchthavens zonder ICAO-code verwijderd",
           aantal_voor - len(luchthavens), len(luchthavens))
    # Elke ICAO-code mag maar 1 keer voorkomen, anders krijgen we straks dubbele vluchten
    aantal_voor = len(luchthavens)
    luchthavens = luchthavens.drop_duplicates(subset="ICAO")
    noteer(log, "Dubbele ICAO-codes", "Dubbele ICAO-codes verwijderd",
           aantal_voor - len(luchthavens), len(luchthavens))
    # Controle op onmogelijke coordinaten (breedte moet tussen -90 en 90, lengte tussen -180 en 180)
    fout_breedte = (luchthavens["Latitude"].abs() > 90).sum()
    fout_lengte = (luchthavens["Longitude"].abs() > 180).sum()
    noteer(log, "Controle coordinaten", "Gecontroleerd op onmogelijke waarden (niets aangepast)",
           fout_breedte + fout_lengte, len(luchthavens))
    # We houden alleen de kolommen die we nodig hebben, met duidelijke namen
    luchthavens = luchthavens[["ICAO", "Name", "City", "Country", "Latitude", "Longitude"]]
    luchthavens = luchthavens.rename(columns={"Name": "Airport_name",
                                              "City": "Airport_city",
                                              "Country": "Airport_country"})
    return luchthavens

def koppel_luchthavens(flights, luchthavens, log):
    """Voeg locaties toe op ICAO-code en behoud ook vluchten zonder bekende locatie."""
    aantal_voor = len(flights)
    # We plakken de luchthaventabel aan de vluchtentabel. De code van de bestemming ("Org/Des")
    # in de vluchten hoort bij de "ICAO" in de luchthavens.
    # how="left" betekent: alle vluchten blijven staan, ook als we de luchthaven niet vinden.
    flights = flights.merge(luchthavens, left_on="Org/Des", right_on="ICAO", how="left",
                            validate="many_to_one")  # meerdere vluchten, één luchthaven per code
    flights = flights.drop(columns=["ICAO"])   # dit is nu een kopie van "Org/Des"
    noteer(log, "Koppeling luchthavens", "Gekoppeld op ICAO-code (aantal rijen moet gelijk blijven)",
           aantal_voor - len(flights), len(flights))
    # Vluchten zonder coordinaten komen niet op de kaart, maar blijven wel in de data
    zonder = flights[flights["Latitude"].isna()]
    codes = list(zonder["Org/Des"].unique())
    noteer(log, "Niet op de kaart", "Geen coordinaten voor " + str(codes),
           len(zonder), len(flights))
    # Een paar vluchten hebben Zürich zelf als bestemming. Waarom weten we niet.
    # We verwijderen ze niet, maar markeren ze, zodat je ze op de kaart kunt weglaten.
    flights["Is_Zurich_itself"] = flights["Org/Des"] == "LSZH"
    noteer(log, "Zürich als bestemming", "Gemarkeerd in 'Is_Zurich_itself' (niet verwijderd)",
           flights["Is_Zurich_itself"].sum(), len(flights))
    return flights

# ---------------------------------------------------------------------------
# STAP 5: SAMENVATTINGEN
# ---------------------------------------------------------------------------

def maak_dagtabel(flights, weer, log):
    """Vat vertrekken per dag samen en voeg het weer van die datum toe."""
    # De onderzoeksvraag gaat over vertrekken. Aankomsten tellen hier dus niet mee.
    flights = flights[flights["LSV"] == "S"]
    # groupby("Date") stopt alle vluchten van dezelfde dag bij elkaar.
    # Daarna rekenen we per dag het aantal vluchten en de vertraging uit.
    # Opbouw:  nieuwe_naam = ("kolom", "wat we uitrekenen")
    per_dag = flights.groupby("Date").agg(
        Flights=("Delay_minutes", "count"),         # aantal vluchten
        Delay_mean=("Delay_minutes", "mean"),       # gemiddelde vertraging
        Delay_median=("Delay_minutes", "median"),   # mediaan (middelste waarde)
        Delay_min=("Delay_minutes", "min"),         # kleinste waarde (meest te vroeg)
        Delay_max=("Delay_minutes", "max"),         # grootste waarde (meest te laat)
        Share_late=("Is_late", "mean"),             # aandeel te late vluchten (0 tot 1)
    )
    per_dag = per_dag.reset_index()                     # "Date" weer een gewone kolom maken
    per_dag = per_dag.rename(columns={"Date": "date"})  # zelfde naam als in de weertabel
    # Weer en vertraging aan elkaar plakken op de datum.
    # Een left-join bewaart elke vertrekdag, ook als weer voor een dag ontbreekt.
    daily = per_dag.merge(weer, on="date", how="left", validate="one_to_one")
    noteer(log, "Koppeling weer", "Weer gekoppeld aan vertrekvertraging per dag; geen dagen verwijderd",
           0, len(daily))
    return daily

def maak_bestemmingstabel(flights):
    """Vat alle aankomsten en vertrekken samen per jaar en verbonden vliegveld."""
    # Zelfde idee als hierboven, maar nu groeperen we op jaar EN bestemming.
    # "first" pakt de eerste waarde. Naam en coordinaten zijn voor dezelfde bestemming
    # toch altijd gelijk.
    destinations = flights.groupby(["Year", "Org/Des"]).agg(
        Flights=("Delay_minutes", "count"),
        Delay_mean=("Delay_minutes", "mean"),
        Delay_median=("Delay_minutes", "median"),
        Delay_min=("Delay_minutes", "min"),
        Delay_max=("Delay_minutes", "max"),
        Share_late=("Is_late", "mean"),
        Airport_name=("Airport_name", "first"),
        Airport_city=("Airport_city", "first"),
        Airport_country=("Airport_country", "first"),
        Latitude=("Latitude", "first"),
        Longitude=("Longitude", "first"),
    )
    destinations = destinations.reset_index()
    return destinations

# ---------------------------------------------------------------------------
# ALLES IN EEN KEER (deze functie roep je aan vanuit app.py)
# ---------------------------------------------------------------------------

def maak_alle_data(schedule_pad=DATA_MAP / "schedule_airport.csv",
                   weer_pad=DATA_MAP / "export.csv",
                   luchthavens_pad=DATA_MAP / "airports-extended.csv"):
    """Doorloop de voorbereiding en geef flights, daily, destinations en log terug."""
    log = []   # hier komen alle opschoonstappen in
    flights = laad_vluchten(schedule_pad, log)
    weer = laad_weer(weer_pad, log)
    luchthavens = laad_luchthavens(luchthavens_pad, log)
    flights = koppel_luchthavens(flights, luchthavens, log)
    # Drukte = aantal geplande vertrekken in hetzelfde kalenderuur, niet werkelijke drukte.
    # floor("h") maakt bijvoorbeeld 13:45 tot 13:00; de kalenderdatum blijft behouden.
    geplande_uren = flights["Planned"].dt.floor("h")
    # value_counts telt hoe vaak ieder datum/uur bij de vertrekken voorkomt.
    drukte = geplande_uren[flights["LSV"] == "S"].value_counts()
    # map zoekt de telling per vlucht op; een uur zonder geplande vertrekken krijgt 0.
    flights["Scheduled_departures"] = geplande_uren.map(drukte).fillna(0).astype(int)
    daily = maak_dagtabel(flights, weer, log)
    destinations = maak_bestemmingstabel(flights)
    log = pd.DataFrame(log)   # van de lijst maken we een tabel
    return flights, daily, destinations, log

# ---------------------------------------------------------------------------
# CONTROLE: HANGT DE CONCLUSIE AF VAN DE EXTREME VERTRAGINGEN?
# Lijken de getallen met en zonder extremen op elkaar? Dan niet.
# ---------------------------------------------------------------------------

def controle_extremen(flights):
    """Vergelijk jaarcijfers met en zonder extreme vertragingen."""
    # Maak de jaargroepen één keer; alle uitkomsten hieronder gebruiken diezelfde groepen.
    alles = flights.groupby("Year")
    zonder = flights[flights["Is_extreme"] == False].groupby("Year")
    tabel = pd.DataFrame({
        "Gemiddelde (alles)": alles["Delay_minutes"].mean(),
        "Gemiddelde (zonder extremen)": zonder["Delay_minutes"].mean(),
        "Mediaan (alles)": alles["Delay_minutes"].median(),
        "Te laat % (alles)": alles["Is_late"].mean() * 100,
        "Te laat % (zonder extremen)": zonder["Is_late"].mean() * 100,
    })
    return tabel.round(2)

def maak_weektabel(flights):
    """Tel aankomsten en vertrekken per week; ontbrekende dagen veroorzaken een gat."""
    # unstack zet aankomst en vertrek naast elkaar in kolommen.
    # fillna(0): op een bekende dag krijgt een ontbrekende vluchtsoort het aantal 0.
    dagen = flights.groupby(["Date", "Flight_type"]).size().unstack().fillna(0)
    # reindex voegt alle kalenderdagen toe; dagen zonder brongegevens worden lege waarden.
    kalender = pd.date_range(flights["Date"].min(), flights["Date"].max())
    dagen = dagen.reindex(kalender)
    tabellen = []
    for jaar in [2019, 2020]:
        selectie = dagen[dagen.index.year == jaar]
        weekgroepen = selectie.resample("W-SUN")  # verzamel dagen in weken eindigend op zondag
        weken = weekgroepen.sum(min_count=1)  # een volledig lege week wordt geen onterechte nul
        dagen_per_week = weekgroepen.size()
        # Een dag is aanwezig als zowel aankomst als vertrek een waarde heeft.
        aanwezige_dagen = selectie.notna().all(axis=1)
        getelde_dagen = aanwezige_dagen.resample("W-SUN").sum()
        compleet = getelde_dagen == dagen_per_week
        # ~ draait True/False om: alleen de onvolledige weken krijgen een gat in de grafiek.
        weken.loc[~compleet, ["Aankomst", "Vertrek"]] = float("nan")  # een zichtbaar gat
        weken["Year"] = jaar
        weken["Days"] = dagen_per_week  # eerste/laatste week soms korter
        # Month is alleen voor het maandfilter. De laatste zondag kan in januari vallen,
        # terwijl de getelde vluchten nog van december van het gekozen jaar zijn.
        weken["Month"] = weken.index.month
        weken.loc[weken.index.year != jaar, "Month"] = 12
        tabellen.append(weken)
    return pd.concat(tabellen).rename_axis("Date").reset_index()

def vat_vertraging_samen(vertrekken, kolommen):
    """True telt als 1: de gemiddelde True-waarde is dus het aandeel te late vluchten."""
    tabel = vertrekken.groupby(kolommen, observed=True).agg(
        Flights=("Is_late", "size"), Share_late=("Is_late", "mean"))
    tabel["Late_percent"] = tabel["Share_late"] * 100
    return tabel.reset_index()

def maak_voorspelling(vertrekken):
    """Voorspel het percentage late vertrekken per uur met eerdere percentages.
    Voorbeeld: waren 30 van 100 vertrekken om 10:00 laat, dan is de schatting 30%.
    Dit voorspelt een kans voor een groep, niet of één specifieke vlucht zeker laat is.
    Alleen januari–oktober 2019 wordt gebruikt om de percentages te berekenen.
    De latere vluchten gebruiken we pas bij het toetsen van deze voorspelling.
    """
    leerdata = vertrekken[vertrekken["Date"] < "2019-11-01"]
    percentages = leerdata.groupby("Planned_hour")["Is_late"].mean() * 100
    # True telt als 1 en False als 0. Hun gemiddelde is dus het aandeel late vertrekken.
    # Een uur dat niet in de eerdere data stond krijgt het gemiddelde van alle leerdata.
    gemiddelde = leerdata["Is_late"].mean() * 100
    test = vertrekken[vertrekken["Date"] >= "2019-11-01"].copy()
    test["Voorspeld (%)"] = test["Planned_hour"].map(percentages).fillna(gemiddelde)
    return test

def toets_voorspelling(test, jaar):
    """Vergelijk eerdere uurpercentages met de werkelijke percentages in een later jaar."""
    selectie = test[test["Year"] == jaar]
    # groupby maakt één groep per uur. agg geeft iedere uitkomst een eigen kolomnaam.
    # ('Is_late', 'size') betekent: tel de rijen van die kolom binnen iedere groep.
    # reset_index maakt het groepskenmerk Planned_hour weer een gewone kolom.
    tabel = selectie.groupby("Planned_hour").agg(
        Vertrekken=("Is_late", "size"),
        Werkelijk=("Is_late", "mean"),
        Voorspeld=("Voorspeld (%)", "mean"),
    ).reset_index()
    tabel["Werkelijk"] = tabel["Werkelijk"] * 100
    # Een positieve of negatieve afwijking telt even zwaar: abs() maakt beide positief.
    tabel["Afwijking"] = (tabel["Voorspeld"] - tabel["Werkelijk"]).abs()
    return tabel.rename(columns={"Planned_hour": "Uur", "Werkelijk": "Werkelijk (%)",
                                 "Voorspeld": "Voorspeld (%)", "Afwijking": "Afwijking (procentpunt)"})

def maak_tijdtrend(vertrekken):
    """Bereken een eenvoudige wekelijkse verandering en trek die vier weken door.

    We vergelijken twee blokken van vier leerweken. Bijvoorbeeld: van gemiddeld
    20% naar 16% is -4 procentpunt in vier weken, dus -1 procentpunt per week.
    Vanaf de laatste leerweek passen we die stap toe op vier nieuwe testweken.
    Dit is lineair doortrekken met optellen en delen; er wordt geen sklearn gebruikt.
    """
    weken = vertrekken.set_index("Date")["Is_late"].resample("W-SUN").mean() * 100
    dagen = vertrekken.groupby("Date").size().resample("W-SUN").count()
    weken = weken[dagen == 7].dropna()  # korte/gedeeltelijke weken worden niet gebruikt
    gekozen = weken.loc["2019-10-13":"2019-12-29"]  # 8 leerweken, dan 4 testweken
    tabel = gekozen.rename("Werkelijk (%)").reset_index()
    # iloc[:4] kiest de eerste vier rijen; iloc[4:8] kiest de volgende vier rijen.
    eerste_vier = tabel.iloc[:4]["Werkelijk (%)"].mean()
    laatste_vier = tabel.iloc[4:8]["Werkelijk (%)"].mean()
    stap_per_week = (laatste_vier - eerste_vier) / 4
    startpercentage = tabel.iloc[7]["Werkelijk (%)"]  # de laatste van de acht leerweken

    # Zeven lege plekken: vóór de laatste leerweek tekenen we geen voorspelling.
    voorspellingen = [None] * 7
    for week in range(7, len(tabel)):
        voorspellingen.append(startpercentage + (week - 7) * stap_per_week)
    tabel["Voorspeld (%)"] = voorspellingen
    tabel["Periode"] = "Leerweken"
    tabel.loc[8:, "Periode"] = "Test"
    return tabel, stap_per_week  # testwaarden hebben niet meegedaan aan de berekening

def maak_weervergelijking(daily):
    """Vergelijk dagen op hun hoogste windstoot; onbekende waarden blijven een eigen groep."""
    weer = daily.copy()
    weer["Jaar"] = weer["date"].dt.year.astype(str)  # tekst geeft één kleur per jaar
    # wpgt is de hoogste windstoot van de dag in km/u, niet de gemiddelde windsnelheid.
    # Bron voor deze betekenis en eenheid: https://dev.meteostat.net/parameters.html
    weer["Windstoten"] = f"Onder {WINDSTOOT_GRENS} km/u"
    # loc[voorwaarde, kolom] past alleen de gekozen rijen in die kolom aan.
    weer.loc[weer["wpgt"] >= WINDSTOOT_GRENS, "Windstoten"] = f"Vanaf {WINDSTOOT_GRENS} km/u"
    # Een ontbrekende meting is onbekend; vul haar niet in als weinig wind.
    weer.loc[weer["wpgt"].isna(), "Windstoten"] = "Onbekend"
    tabel = weer.groupby(["Jaar", "Windstoten"]).agg(
        Dagen=("date", "size"), Aandeel=("Share_late", "mean"),
    ).reset_index()
    # Iedere dag telt even zwaar, niet iedere vlucht. Dat zeggen we bij de grafiek.
    tabel["Te laat (%)"] = tabel["Aandeel"] * 100
    return tabel

# ---------------------------------------------------------------------------
# Dit stuk draait alleen als je het bestand zelf start: python data.py
# (Importeer je het in app.py, dan wordt dit overgeslagen.)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    flights, daily, destinations, log = maak_alle_data()
    print("OPSCHOONLOG")
    print(log.to_string(index=False))
    print("\nHANGT DE CONCLUSIE AF VAN DE EXTREMEN?")
    print(controle_extremen(flights))
    print("\nVLUCHTEN (eerste 5 rijen)")
    print(flights.head())
    print("\nPER DAG + WEER (eerste 5 rijen)")
    print(daily.head())
    print("\nPER BESTEMMING (eerste 5 rijen)")
    print(destinations.head())

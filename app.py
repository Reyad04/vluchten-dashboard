"""Dashboard voor Case 3. Starten: python -m streamlit run app.py.

Leesvolgorde: vraag → context → onderzoek → voorspelling → conclusie.
Data.py bevat de berekeningen. Hier kiezen we vooral wat op het scherm staat.
Bronnen: https://docs.streamlit.io/develop/api-reference
         https://plotly.com/python/plotly-express/
         https://plotly.com/python-api-reference/generated/plotly.graph_objects.Scattermap.html
"""

import streamlit as st                 # maakt knoppen, tabs, tekst en tabellen
import plotly.express as px            # maakt de gewone grafieken en kaartpunten
import plotly.graph_objects as go      # voegt de lijnen aan de kaart toe
from math import log10                 # spreidt grote en kleine aantallen in de kaartkleur
from data import (maak_alle_data, maak_weektabel, vat_vertraging_samen,
                  maak_voorspelling, toets_voorspelling, maak_tijdtrend,
                  maak_weervergelijking, controle_extremen, WINDSTOOT_GRENS)

st.set_page_config(page_title="Vluchten Zürich", page_icon="✈", layout="wide")


# ---------- 1. DATA LADEN ----------
# @st.cache_data onthoudt de uitkomst. Zo worden de CSV's niet bij iedere klik herlezen.
# Bron: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data
@st.cache_data
def laad_data():
    """Haal de vier voorbereide tabellen op uit data.py."""
    flights, daily, destinations, log = maak_alle_data()
    # We bewaren alleen de vluchtkolommen die dit dashboard gebruikt; dat scheelt geheugen.
    flights = flights[["Date", "Year", "LSV", "Flight_type", "Planned_hour",
                       "Is_late", "Is_extreme", "Delay_minutes"]]
    return flights, daily, destinations, log


def toon_grafiek(figuur):
    """Laat een Plotly-grafiek de beschikbare schermbreedte gebruiken."""
    st.plotly_chart(figuur, width="stretch")


def hoogste_rij(tabel, kolom):
    """Zoek de rij met het hoogste percentage, aantal of verschil."""
    # We gebruiken deze stap op vier plekken. sort_values zet de hoogste waarde vooraan.
    # iloc[0] kiest de eerste rij van de gesorteerde tabel; de tabel moet minstens één rij hebben.
    return tabel.sort_values(kolom, ascending=False).iloc[0]


def toon_weekgrafiek(weken, jaar, maanden, maximum):
    """Toon alleen het gekozen jaar en maandbereik, met dezelfde schaal voor beide jaren."""
    selectie = weken[weken["Year"] == jaar]
    # between(a, b) houdt de waarden van a tot en met b; maanden[0] is het begin.
    selectie = selectie[selectie["Month"].between(maanden[0], maanden[1])]
    # Twee kolomnamen bij y maken twee lijnen. Er is geen extra omzetting van de tabel nodig.
    figuur = px.line(selectie, x="Date", y=["Aankomst", "Vertrek"], title=str(jaar),
                     hover_data=["Days"],
                     labels={"Date": "Week eindigend op", "value": "Aantal vluchten",
                             "variable": "Vluchtsoort", "Days": "Dagen in week"})
    figuur.update_yaxes(range=[0, maximum])
    figuur.update_traces(connectgaps=False)  # een ontbrekende waarde blijft een zichtbaar gat
    toon_grafiek(figuur)


def maak_kaart(kaart, gebied, lijnen_tonen, hoogste_aantal):
    """Teken vliegvelden en, als dat is aangevinkt, hun verbinding met Zürich."""
    # Deze coördinaten komen uit airports-extended.csv, rij met ICAO-code LSZH.
    zurich_lat = 47.464699
    zurich_lon = 8.54917
    middelpunt = {"lat": 49, "lon": 10}
    zoom = 2
    if gebied == "Wereld":
        middelpunt = {"lat": 20, "lon": 0}
        zoom = 0.5

    # log10 maakt iedere factor 10 in aantallen één kleurstap: 1, 10, 100, 1.000.
    # Daardoor blijven vliegvelden met weinig vluchten ook zichtbaar. De legenda toont aantallen.
    kaart = kaart.copy()
    kaart["Kleur"] = kaart["Flights"].map(log10)
    figuur = px.scatter_map(kaart, lat="Latitude", lon="Longitude", color="Kleur",
                           color_continuous_scale="Blues", range_color=[0, log10(hoogste_aantal)],
                           hover_name="Airport_name", hover_data={"Flights": True, "Kleur": False},
                           labels={"Flights": "Aantal vluchten"}, map_style="carto-positron",
                           center=middelpunt, zoom=zoom)
    figuur.update_traces(marker_size=9)
    figuur.update_layout(coloraxis_colorbar={"title": "Vluchten", "tickvals": [0, 1, 2, 3, 4],
                                             "ticktext": ["1", "10", "100", "1.000", "10.000"]})

    if lijnen_tonen:
        breedtes = []
        lengtes = []
        # Een lijn bestaat uit Zürich, een bestemming en een onderbreking.
        # None onderbreekt de lijn: zo verbinden we geen twee bestemmingen met elkaar.
        # iterrows() geeft het rijnummer en de rij. _ betekent dat we het rijnummer niet gebruiken.
        # extend() voegt de drie waarden aan de lijst toe.
        for _, vliegveld in kaart.iterrows():
            breedtes.extend([zurich_lat, vliegveld["Latitude"], None])
            lengtes.extend([zurich_lon, vliegveld["Longitude"], None])
        figuur.add_trace(go.Scattermap(lat=breedtes, lon=lengtes, mode="lines",
                                       line={"width": 1, "color": "#667788"}, opacity=0.25,
                                       connectgaps=False, hoverinfo="skip", name="Verbindingen"))
    # Zürich krijgt een eigen rode stip, zodat het begin van de lijnen herkenbaar is.
    figuur.add_trace(go.Scattermap(lat=[zurich_lat], lon=[zurich_lon], mode="markers",
                                   marker={"size": 13, "color": "#c43830"}, name="Zürich"))
    return figuur


flights, daily, destinations, log = laad_data()
# [voorwaarde] kiest rijen. LSV == S betekent vertrek; de aankomsten blijven in flights.
vertrekken = flights[flights["LSV"] == "S"]
weken = maak_weektabel(flights)
test = maak_voorspelling(vertrekken)


# ---------- 2. EERSTE BEELD ----------
# De vraag en kerncijfers staan bovenaan. Het antwoord krijgt een eigen plek in tab 4.
st.title("Wanneer vertrekken vluchten uit Zürich te laat?")
st.write("**Onderzoeksvraag:** wanneer vertrekken vluchten vanaf Zürich minstens 15 minuten "
         "te laat, en hoe goed kunnen we dat voorspellen met informatie uit het vluchtschema?")
st.caption("Lees van links naar rechts: 1. context, 2. tijdstip en weer, 3. voorspelling toetsen, "
           "4. conclusie en verantwoording. De analyses van vertraging gaan alleen over vertrekken.")
aantallen = flights.groupby("Year").size()  # size() telt de rijen per jaar
jaaroverzicht = vat_vertraging_samen(vertrekken, ["Year"]).set_index("Year")
kaarten = st.columns(4)  # vier plekken naast elkaar voor de kerncijfers
# Een f-string zet een waarde in tekst. :.1f toont één decimaal; :, voegt duizendtalscheiding toe.
kaarten[0].metric("Alle vluchten 2019", f"{aantallen[2019]:,}")
kaarten[1].metric("Alle vluchten 2020", f"{aantallen[2020]:,}")
kaarten[2].metric("Vertrekken te laat 2019", f"{jaaroverzicht.loc[2019, 'Late_percent']:.1f}%")
kaarten[3].metric("Vertrekken te laat 2020", f"{jaaroverzicht.loc[2020, 'Late_percent']:.1f}%")
# We bereiden de samenvattingen één keer voor, zodat grafieken en conclusie dezelfde cijfers gebruiken.
# Het uurpatroon beschrijft alle vertrekken in ieder jaar. De voorspelling gebruikt apart leerdata.
uurpatroon = vat_vertraging_samen(vertrekken, ["Year", "Planned_hour"])
# Zeer kleine groepen geven snel extreme percentages. Alleen deze grafiek gebruikt de grens van 100.
# De vluchten zelf blijven in de overige analyses en in de oorspronkelijke tellingen staan.
uurpatroon = uurpatroon[uurpatroon["Flights"] >= 100].copy()
uurpatroon["Jaar"] = uurpatroon["Year"].astype(str)  # tekst maakt één lijn per jaar
# Kies eerst het jaar; zoek daarna het hoogste percentage met onze hulpfunctie.
piek_2019 = hoogste_rij(uurpatroon[uurpatroon["Year"] == 2019], "Late_percent")
piek_2020 = hoogste_rij(uurpatroon[uurpatroon["Year"] == 2020], "Late_percent")
weer = maak_weervergelijking(daily)
# Deze labels gebruiken dezelfde grens als de berekening in data.py.
windgroepen = [f"Onder {WINDSTOOT_GRENS} km/u", f"Vanaf {WINDSTOOT_GRENS} km/u", "Onbekend"]
# Een woordenboek koppelt ieder jaar aan een kleur. Uur- en weergrafiek gebruiken dezelfde kleuren.
jaarkleuren = {"2019": "#3366aa", "2020": "#d6791e"}
# Bewaar de twee testtabellen per jaar. Zo gebruiken grafiek en conclusie dezelfde berekening.
uurtests = {2019: toets_voorspelling(test, 2019), 2020: toets_voorspelling(test, 2020)}
# uurtests[2019] haalt de tabel van 2019 op. mean() middelt de afwijkingen per uur.
fout_2019 = uurtests[2019]["Afwijking (procentpunt)"].mean()
fout_2020 = uurtests[2020]["Afwijking (procentpunt)"].mean()

context_tab, onderzoek_tab, voorspelling_tab, conclusie_tab = st.tabs(
    ["1. Context", "2. Vertraging onderzoeken", "3. Voorspelling toetsen",
     "4. Conclusie en verantwoording"])


# ---------- 3. CONTEXT: WAAROM VERGELIJKEN WE DE JAREN APART? ----------
with context_tab:
    st.subheader("Wat veranderde tussen 2019 en 2020?")
    # Deel 2020 door 2019 voor de verhouding. Het deel dat wegvalt is 1 min die verhouding.
    daling = (1 - aantallen[2020] / aantallen[2019]) * 100
    st.write(f"In 2020 waren er **{daling:.1f}% minder vluchten** dan in 2019. "
             "Door dat verschil bekijken we de jaren afzonderlijk bij de vertraging en het weer.")
    maanden = st.slider("Maandbereik in beide jaren", 1, 12, (1, 12))
    # De grootste weektelling bepaalt de schaal; 10% extra ruimte houdt de lijnen leesbaar.
    maximum = max(weken["Aankomst"].max(), weken["Vertrek"].max()) * 1.1
    links, rechts = st.columns(2)
    with links:
        toon_weekgrafiek(weken, 2019, maanden, maximum)
    with rechts:
        toon_weekgrafiek(weken, 2020, maanden, maximum)
    st.caption("Weken maken de ontwikkeling overzichtelijker dan losse dagen. Dezelfde lineaire schaal "
               "maakt de aantallen vergelijkbaar. Aankomsten én vertrekken; weken eindigen op zondag. "
               "De eerste en laatste week kunnen korter zijn. De tooltip toont het aantal dagen. "
               "Ontbrekende brondagen worden niet doorverbonden.")

    # De kaart hoort bij de context: zij laat zien over welke vliegveldverbindingen we spreken.
    st.subheader("Met welke vliegvelden is Zürich verbonden?")
    links, rechts = st.columns(2)
    jaar = links.selectbox("Jaar op de kaart", [2019, 2020])
    gebied = rechts.selectbox("Gebied", ["Europa en omgeving", "Wereld"])
    lijnen_tonen = st.checkbox("Toon verbindingslijnen vanuit Zürich", value=True)
    # Een bestemming komt eenmaal op de kaart. De telling bevat aankomsten én vertrekken.
    kaart = destinations[destinations["Year"] == jaar]
    kaart = kaart[kaart["Org/Des"] != "LSZH"]  # Zürich krijgt apart een rode stip
    kaart = kaart.dropna(subset=["Latitude", "Longitude"])
    if gebied == "Europa en omgeving":
        # Een rechthoekig kaartvenster, geen officiële grens van Europa.
        kaart = kaart[kaart["Latitude"].between(34, 72) & kaart["Longitude"].between(-25, 45)]
    figuur = maak_kaart(kaart, gebied, lijnen_tonen, destinations["Flights"].max())
    toon_grafiek(figuur)
    # De bevinding volgt het gekozen jaar en gebied, net als de kaart.
    drukste = hoogste_rij(kaart, "Flights")
    st.write(f"De selectie toont **{len(kaart)} vliegvelden**. De meeste vluchten zijn verbonden met "
             f"**{drukste['Airport_name']}**: {int(drukste['Flights']):,} aankomsten en vertrekken in {jaar}.")
    st.caption("Blauw toont het aantal vluchten op een logschaal; rood is Zürich. "
               "De lijnen zijn schematische verbindingen, geen werkelijk gevlogen routes. "
               "Beweeg over een stip voor de naam en het aantal vluchten.")
    st.caption("De volgende tab zoomt in op vertrekvertraging: eerst het tijdstip, daarna het weer.")


# ---------- 4. ONDERZOEK: EERST BESCHRIJVEN WAT WE ZIEN ----------
with onderzoek_tab:
    st.subheader("Op welke geplande vertrekuren zien we meer vertraging?")
    st.write("We bekijken het werkelijke aandeel vertrekken met minstens 15 minuten vertraging "
             "over ieder volledig jaar. De aantallen staan in de tooltip.")
    # Dit is dezelfde eenvoudige samenvatting als bij de kerncijfers, nu gegroepeerd op jaar én uur.
    figuur = px.line(uurpatroon, x="Planned_hour", y="Late_percent", color="Jaar", markers=True,
                     color_discrete_map=jaarkleuren, hover_data=["Flights"],
                     labels={"Planned_hour": "Gepland vertrekuur", "Late_percent": "Te late vertrekken (%)",
                             "Flights": "Aantal vertrekken"})
    toon_grafiek(figuur)
    st.write(f"**2019:** het hoogste aandeel is om **{int(piek_2019['Planned_hour']):02d}:00** "
             f"({piek_2019['Late_percent']:.1f}%). **2020:** om "
             f"**{int(piek_2020['Planned_hour']):02d}:00** ({piek_2020['Late_percent']:.1f}%).")
    st.caption("Alleen uren met minstens 100 vertrekken in het betreffende jaar worden getoond. "
               "Dat beperkt de invloed van zeer kleine groepen; het bewijst geen oorzaak van vertraging.")

    # De weeranalyse staat direct in beeld: de koppeling van bronnen is een kernonderdeel van de opdracht.
    st.subheader("Zien we meer vertrekvertraging op dagen met hogere windstoten?")
    figuur = px.bar(weer, x="Windstoten", y="Te laat (%)", color="Jaar", barmode="group", hover_data=["Dagen"],
                    color_discrete_map=jaarkleuren,
                    category_orders={"Windstoten": windgroepen},
                    labels={"Windstoten": "Hoogste windstoot per dag", "Te laat (%)": "Te late vertrekken (%)"})
    toon_grafiek(figuur)
    # Vergelijk de windgroepen binnen hetzelfde jaar; meng 2019 en 2020 niet.
    # Het woordenboek bewaart de verschillen voor de conclusie in tab 4.
    windverschillen = {}
    for jaar in ["2019", "2020"]:
        selectie = weer[weer["Jaar"] == jaar]
        lager = selectie[selectie["Windstoten"] == windgroepen[0]]["Te laat (%)"].iloc[0]
        hoger = selectie[selectie["Windstoten"] == windgroepen[1]]["Te laat (%)"].iloc[0]
        windverschillen[jaar] = hoger - lager
        st.write(f"**{jaar}:** {windgroepen[0].lower()}: {lager:.1f}%; "
                 f"{windgroepen[1].lower()}: {hoger:.1f}%. Verschil: {windverschillen[jaar]:+.1f} procentpunt.")
    st.caption(f"wpgt is de hoogste windstoot van de dag, in km/u. {WINDSTOOT_GRENS} km/u is een "
               "zelfgekozen vergelijkingsgrens, geen officiële windlimiet. We middelen de dagelijkse "
               "percentages; iedere dag telt even zwaar. Het gemeten dagmaximum wordt niet gebruikt in de voorspelling.")
    st.caption("Nu we het uurpatroon hebben gezien, toetsen we in de volgende tab of eerdere "
               "uurpercentages ook bruikbaar zijn voor latere vertrekken.")


# ---------- 5. VOORSPELLING: TOETSEN OP LATERE DATA ----------
with voorspelling_tab:
    st.subheader("Werken eerdere percentages ook voor latere vertrekken?")
    st.write("Voorbeeld: waren eerder 30 van 100 vertrekken om 10:00 te laat, "
             "dan voorspellen we 30% voor nieuwe vertrekken om 10:00.")
    testjaar = st.selectbox("Toets op ongeziene vluchten uit", [2019, 2020])
    tabel = uurtests[testjaar]  # de keuzelijst bepaalt welke voorbereide testtabel we tonen
    figuur = px.line(tabel, x="Uur", y=["Voorspeld (%)", "Werkelijk (%)"], markers=True,
                     hover_data=["Vertrekken"], labels={"Uur": "Gepland vertrekuur",
                     "value": "Vertrekken minstens 15 min te laat (%)", "variable": "Reeks"})
    toon_grafiek(figuur)
    fout = tabel["Afwijking (procentpunt)"].mean()
    st.write(f"Gemiddelde afwijking per vertrekuur: **{fout:.1f} procentpunt**.")
    # We beschrijven alleen uren met minstens 100 vluchten en zoeken de grootste fout.
    genoeg = tabel[tabel["Vertrekken"] >= 100]
    grootste = hoogste_rij(genoeg, "Afwijking (procentpunt)")
    st.write(f"Bij uren met minstens 100 vertrekken is de grootste afwijking om "
             f"**{int(grootste['Uur']):02d}:00**: voorspeld {grootste['Voorspeld (%)']:.1f}%, "
             f"werkelijk {grootste['Werkelijk (%)']:.1f}%.")
    st.caption("Leerdata: januari–oktober 2019. Test: november–december 2019 of heel 2020. "
               "Ieder vertrekuur telt even zwaar in de gemiddelde afwijking; aantallen staan in de tooltip. "
               "Aanname: het patroon per uur blijft gelijk. Seizoen, drukte en corona kunnen dit veranderen.")

    # De tijdtrend hoort bij de rubric; extra details verschijnen pas na een klik.
    with st.expander("Tijdtrend: vier weken vooruit voorspellen"):
        trend, stap = maak_tijdtrend(vertrekken)
        figuur = px.line(trend, x="Date", y=["Werkelijk (%)", "Voorspeld (%)"], markers=True,
                         hover_data=["Periode"], labels={"Date": "Week eindigend op",
                         "value": "Te late vertrekken (%)", "variable": "Reeks"})
        toon_grafiek(figuur)
        # abs() maakt fouten positief; mean() geeft de gemiddelde grootte van de fouten.
        testweken = trend[trend["Periode"] == "Test"]
        afwijking = (testweken["Voorspeld (%)"] - testweken["Werkelijk (%)"]).abs().mean()
        st.write(f"Wekelijkse stap uit de acht leerweken: **{stap:.2f} procentpunt**. "
                 f"Gemiddelde fout op de vier nieuwe weken: **{afwijking:.1f} procentpunt**.")
        st.caption("We vergelijken twee blokken van vier weken en delen de verandering door vier. "
                   "Die stap tellen we vanaf de laatste leerweek steeds op. Leerweken eindigen op "
                   "13 oktober–1 december 2019; testweken op 8–29 december. "
                   "De decemberstijging wordt gemist. De aanname geldt hoogstens kort; feestdagen en corona kunnen haar breken.")


# Alles in dit with-blok verschijnt alleen in het vierde werkblad.
with conclusie_tab:
    # ---------- 6. CONCLUSIE: EXPLICIET ANTWOORD OP ONZE VRAAG ----------
    # De eindconclusie staat alleen in tab 4. Bevindingen blijven bij hun eigen grafiek staan.
    # De samenvatting gaat over beide volledige jaren, dus zij volgt niet één plaatselijk kaartfilter.
    st.subheader("Conclusie: antwoord op de onderzoeksvraag")
    st.write(f"**Wanneer?** Onder uren met minstens 100 vertrekken heeft "
             f"**{int(piek_2019['Planned_hour']):02d}:00 in 2019** het hoogste aandeel te late vertrekken "
             f"({piek_2019['Late_percent']:.1f}%). In 2020 ligt de piek om "
             f"**{int(piek_2020['Planned_hour']):02d}:00** ({piek_2020['Late_percent']:.1f}%). "
             "Een gepland vertrekuur hangt dus samen met verschillen in vertrekvertraging.")
    st.write(f"**Wat voegt het weer toe?** Op dagen met windstoten vanaf {WINDSTOOT_GRENS} km/u "
             f"ligt het gemiddelde dagelijkse aandeel late vertrekken in 2019 "
             f"**{windverschillen['2019']:+.1f} procentpunt** hoger dan op dagen onder die grens. "
             f"In 2020 is het verschil **{windverschillen['2020']:+.1f} procentpunt**; "
             "die uitkomst verandert bij een andere grens. De samenhang bewijst geen oorzaak: "
             "seizoen en drukte kunnen ook verschillen.")
    st.write(f"**Hoe goed voorspellen we?** Eerdere uurpercentages geven een eenvoudige schatting, "
             f"maar de gemiddelde afwijking is **{fout_2019:.1f} procentpunt** op november–december 2019 "
             f"en **{fout_2020:.1f} procentpunt** op 2020. Alleen het vertrekuur biedt hier dus "
             "beperkte voorspelkracht. Een percentage voor een groep zegt niet zeker of één vlucht te laat vertrekt.")
    st.caption("Deze conclusie gaat over de historische gegevens van 2019–2020. "
               "De jaren verschillen in verkeersomvang en aandeel vertraging. De tijdtrend mist de decemberstijging; "
               "seizoen, feestdagen en veranderingen zoals corona kunnen voorspellingen breken.")


    # ---------- 7. VERANTWOORDING ----------
    # Deze informatie hoort bij de beoordeling, maar hoeft niet steeds tegelijk in beeld te staan.
    st.divider()
    st.subheader("Verantwoording")
    with st.expander("Data, opschonen en bronnen"):
        st.dataframe(log, hide_index=True, width="stretch")
        st.write("Vertragingen van minstens 180 minuten zijn gemarkeerd en behouden: groot is niet automatisch fout. "
                 "Onderstaande vergelijking toont het effect van weglaten op de percentages en gemiddelden.")
        st.dataframe(controle_extremen(vertrekken), width="stretch")
        # Bereken de voorspelling nogmaals zonder extremen, zowel in de leer- als testdata.
        test_zonder = maak_voorspelling(vertrekken[vertrekken["Is_extreme"] == False])
        controle = toets_voorspelling(test_zonder, 2019)
        fout_zonder = controle["Afwijking (procentpunt)"].mean()
        st.write(f"Voorspellingsfout per uur op de test uit 2019: met extremen {fout_2019:.1f}, "
                 f"zonder extremen {fout_zonder:.1f} procentpunt.")
        st.caption("96 vluchten hebben geen kaartlocatie; ze blijven in de totale telling. "
                   "Vliegtuigtype, baan en een afzonderlijke druktegrafiek zijn weggelaten om het onderzoek klein te houden.")
        st.markdown("Bronnen: Brightspace (vluchten), "
                    "[OpenFlights/Kaggle](https://www.kaggle.com/datasets/open-flights/airports-train-stations-and-ferry-terminals) "
                    "(locaties) en [Meteostat](https://meteostat.net/) (weer). "
                    "De gebruikte documentatie staat bovenaan de code.")

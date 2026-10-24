# IngeGroundBox – Inżynieryjne Modelowanie Terenu (TIN) & BIM dla IngeTrazo

[![Licencja: GPL v3](https://img.shields.io/badge/Licencja-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Kompatybilność: IngeTrazo](https://img.shields.io/badge/IngeTrazo-v0.x%20%7C%20v1.x-brightgreen.svg)](https://github.com/ingetrazo)
[![BIM: openBIM IFC](https://img.shields.io/badge/BIM-IfcSite%20%2F%20IfcRoad-orange.svg)](https://technical.buildingsmart.org/)
[![Język: EN i PL](https://img.shields.io/badge/J%C4%99zyk-Polski%20%7C%20English-yellow.svg)](#-wsparcie-wieloj%C4%99zyczne)

> **Wersje językowe:** 🇵🇱 **Polski** | 🇬🇧 [Switch to English version (README.md)](README.md)  
> **Instrukcje:** 📖 [Instrukcja Obsługi krok po kroku (Polski)](MANUAL_PL.md) | 📖 [User Manual (English)](MANUAL_EN.md)

---

## 🌍 O Projekcie

**IngeGroundBox** to zaawansowany moduł inżynieryjnego modelowania terenu (siatek TIN – *Triangulated Irregular Network*) dla otwartoźródłowego środowiska CAD/BIM **IngeTrazo**.

Zainspirowany legendarnym zestawem narzędzi *Sandbox Tools* (Piaskownica) ze SketchUpa, **IngeGroundBox** przenosi tę koncepcję na poziom profesjonalnego projektowania architektonicznego, krajobrazowego i drogowego. Łączy intuicyjne, organiczne rzeźbienie pędzlem z **precyzją openBIM (klasyfikacja IFC)**, **automatycznym bilansowaniem mas ziemnych (wykop i nasyp Cut & Fill w $m^3$)**, **generatorem poziomic (slicerem)** oraz **raportami ilościowymi z eksportem do arkuszy kalkulacyjnych CSV**.

```
       [ Linie geodezyjne / Warstwice ]       [ Obrys budynku / Płyta fundamentowa ]
                     │                                     │
                     ▼                                     ▼
        ┌─────────────────────────┐           ┌─────────────────────────┐
        │ Z warstwic (From Cont.) │           │     Odcisk (Stamp)      │
        │  (Delaunay Bowyer-Watson│           │  (Bilans mas Cut & Fill)│
        └────────────┬────────────┘           └────────────┬────────────┘
                     │                                     │
                     └─────────────────┬───────────────────┘
                                       ▼
                       ┌───────────────────────────────┐
                       │     Modelowanie IngeGroundBox │
                       │   • Wytłaczanie (Smoove)      │
                       │   • Rzutowanie dróg (Drape)   │
                       │   • Dodaj detal (Add Detail)  │
                       │   • Odwróć krawędź (Flip Edge)│
                       └───────────────┬───────────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
          ┌─────────────────────┐             ┌─────────────────────┐
          │     openBIM IFC     │             │ Raporty i Obliczenia│
          │  IfcSite / IfcRoad  │             │   Pole 3D, ΔZ, CSV  │
          └─────────────────────┘             └─────────────────────┘
```

---

## 🛠️ Zestaw 7 Narzędzi GroundBox

| Ikona | Narzędzie | Nazwa oryginalna | Działanie i kluczowe właściwości |
| :---: | :--- | :--- | :--- |
| ⬡ | **Od podstaw** | *From Scratch* | Tworzy płaską, poziomą siatkę terenu TIN o zadanym rozstawie i wymiarach. Posiada układ naprzemiennych przekątnych (*diamond pattern* / szachownica) eliminujący asymetrię rzeźbienia lub układ jednolity. Obsługuje rysowanie interaktywne na 3 kliknięcia. |
| 〰 | **Z warstwic** | *From Contours* | Generuje płynną trójwymiarową powierzchnię terenu (TIN) z zaznaczonych linii, polilinii, łuków warstwic oraz tyczek geodezyjnych przy użyciu triangulacji Delaunaya (Bowyer-Watson z fallbackiem do Scipy). |
| 🖌 | **Wytłaczanie** | *Smoove* | Płynne rzeźbienie terenu pędzlem o regulowanym promieniu i sile w osi Z. Oryginalna funkcja opadania kosinusowego (*cosine falloff*), podgląd na żywo w czasie rzeczywistym oraz pełna historia Undo (`Ctrl+Z`). |
| 🔲 | **Odcisk** | *Stamp* | Odciska rzut budynku, tarasu lub parkingu w pofałdowanym terenie. Tworzy poziomą półkę na zadanej wysokości oraz skarpy przejściowe z regulowanym odsunięciem (*batter offset*). |
| ⬇ | **Rzutowanie** | *Drape* | Rzutuje pionowo w dół obrysy dróg, ścieżek i granic działek na powierzchnię terenu. Precyzyjnie rozcina siatkę (*knife cut*) wzdłuż rzutu i nadaje pasom drogowym dedykowane materiały. |
| ➕ | **Dodaj detal** | *Add Detail* | Interaktywne narzędzie: kliknięcie w trójkąt lub krawędź dzieli go na 4 mniejsze z jednoczesnym podziałem trójkątów sąsiednich (eliminacja szczelin i wiszących węzłów). Pozwala miejscowo zagęścić siatkę pod rzeźbienie. |
| 🔄 | **Odwróć krawędź** | *Flip Edge* | Odwraca wspólną przekątną między dwoma trójkątami w czworokącie wypukłym. Kluczowe dla natychmiastowej korekty grzbietów, dolin i naturalnych kierunków spływu wód opadowych. |

---

## 🌟 Funkcje Inżynierskie, Obliczeniowe i BIM

### 1. 🚜 Bilans Robót Ziemnych (Cut & Fill)
Podczas wykonywania operacji **Odcisk (Stamp)** w pofałdowanym terenie algorytm automatycznie oblicza objętości robót ziemnych w metrach sześciennych ($m^3$) metodą pryzm trójkątnych:
* **Objętość wykopu ($V_{\text{cut}}$):** Masa gruntu przeznaczona do wybrania/wywiezienia.
* **Objętość nasypu ($V_{\text{fill}}$):** Masa gruntu konieczna do nawiezienia/zagęszczenia.
* **Bilans netto ($\Delta V$):** Różnica mas ziemnych ułatwiająca optymalizację kosztów inwestycji.

### 2. 🏛️ Natywne Tagowanie openBIM IFC
Wszystkie wygenerowane obiekty są automatycznie przypisywane do właściwych klas standardu buildingSMART IFC:
* Powierzchnia terenu otrzymuje klasę **`IfcSite`** lub **`IfcGeotechnicalStratum`**.
* Wytłoczone drogi i ścieżki (Drape) otrzymują klasę **`IfcRoad`**.
* Płyty fundamentowe i skarpy otrzymują odpowiednie atrybuty budowlane.

### 3. 📈 Generator Poziomic (Slicer)
Potrzebujesz wygenerować mapę warstwicową z ukształtowanego terenu 3D? Wbudowane narzędzie tnie siatkę poziomymi płaszczyznami co zadany skok wysokościowy ($\Delta Z$, np. co 0.5 m, 1.0 m lub 2.0 m) i tworzy trójwymiarowe krzywe warstwic.

### 4. 📊 Raport Ilościowy i Eksport do CSV
W zakładce **Analiza i Raport** możesz natychmiast sprawdzić:
* Rzeczywistą powierzchnię 3D ($m^2$) w porównaniu do powierzchni rzutu 2D ($m^2$).
* Skrajne rzędne wysokościowe ($Z_{\min}, Z_{\max}$) oraz deniwelację terenu ($\Delta Z$).
* Eksport jednym kliknięciem do pliku **CSV** z kodowaniem `utf-8-sig` (pełna kompatybilność z polskimi znakami w programach **Microsoft Excel** i **LibreOffice Calc**).

### 5. 🎨 Dwustronne Materiały i Normalne Newella
Wszystkie ścianki generowane są z poprawną orientacją CCW i posiadają zdefiniowane oba kolory (`attrs["color"]` awers oraz `attrs["back_color"]` rewers), co eliminuje artefakty cieniowania OpenGL:
* 🌿 **Trawa naturalna** (`#6BA652`)
* 🪵 **Ziemia / Grunt** (`#8C7054`)
* 🏖 **Piasek** (`#D1BF8C`)
* 🪨 **Skała** (`#99999E`)
* 🛣 **Asfalt drogowy** (`#47474D`)
* 🧱 **Bruk / Beton** (`#B8B8BD`)

### 6. 🎨 Analiza Spadków i Heatmapa (Slope Analysis)
Narzędzie w zakładce **Analiza i Raport** bada nachylenie każdego trójkąta terenu względem płaszczyzny horyzontu i klasyfikuje spadki według 10 standardowych inżynieryjno-urbanistycznych przedziałów (od 0% do >100%):
* 🟢 **0 – 5% (Płaski):** Teren idealny pod place, boiska, budynki i grawitacyjny spływ wód opadowych.
* 🟢 **5 – 10% (Łagodny):** Dopuszczalny dla chodników pieszych bez spoczników i standardowych ulic dojazdowych.
* 🟢 **10 – 15% (Umiarkowany):** Górna granica dla pochylni garażowych i stromych podjazdów.
* 🟡 **15 – 20% (Średni):** Trudne drogi górskie; granica bezpiecznego koszenia kosiarką kołową.
* 🟡 **20 – 30% (Stromy):** Wymóg zabudowy tarasowej lub schodkowej; wysokie trudności realizacyjne.
* 🟠 **30 – 40% (Bardzo stromy):** Skarpy naturalne umacniane darnią (nachylenia 1:3 do 1:2.5).
* 🟠 **40 – 50% (Skarpa 1:2):** Standardowe inżynieryjne nachylenie skarp nasypów/wykopów (~26.6°).
* 🔴 **50 – 70% (Skarpa 1:1.5):** Strome skarpy drogowe (~33.7°); wymagane umocnienia geosiatkami lub narzutem.
* 🔴 **70 – 100% (Skarpa 1:1):** Ekstremalne skarpy do 45°; wymagana ziemia zbrojona lub kosze gabionowe.
* 🟣 **> 100% (Urwisko / Mur >45°):** Płytowe ściany oporowe, pale, ścianki szczelne i urwiska skalne.
Kolorowanie jest w 100% **nieniszczące** – oryginalne materiały są zapamiętywane w atrybutach ścianek, dzięki czemu jednym kliknięciem (`↺ Przywróć oryginalne materiały`) można powrócić do widoku tekstur.

### 7. 📦 Zamknięcie Bryły 3D w Cokół (Watertight Solid Skirt)
Zwykłe siatki terenu CAD to otwarte powierzchnie typu 2.5D (ang. *open surface*), które nie mają objętości bryłowej. Opcja **Zamknięcie bryły 3D** automatycznie:
* Odnajduje ciągłą krawędź brzegową terenu (nawet o nieregularnym, wklęsłym kształcie).
* Generuje pionowe ściany boczne (*skirt*) opuszczone do poziomu spodu $Z_{\text{base}} = Z_{\min} - \text{offset}$.
* Zamyka dno szczelnym, zorientowanym w dół wielokątem (triangulacja ucha *ear clipping*).
* Tworzy w 100% litą, szczelną bryłę typu **Manifold Solid** (0 otwartych krawędzi), gotową do analiz geotechnicznych, druku 3D oraz eksportu BIM **`IfcGeographicElement`** (*Solid Terrain Base*).

---

## 📁 Struktura Pakietu

```text
Inge_GroundBox/
├── inge_groundbox.py          # Główny punkt wejścia wtyczki
├── README.md                  # Dokumentacja międzynarodowa (English)
├── README_PL.md               # Dokumentacja w języku polskim (Polski)
├── MANUAL_EN.md               # Instrukcja obsługi w języku angielskim (English)
├── MANUAL_PL.md               # Instrukcja obsługi krok po kroku (Polski)
└── inge_groundbox/            # Moduły wewnętrzne wtyczki
    ├── __init__.py            # setup(app), rejestracja paska narzędzi, menu i PPM
    ├── constants.py           # Klasy BIM, parametry domyślne, kolory materiałów
    ├── i18n.py                # Słowniki tłumaczeń (PL / EN) i funkcja tr()
    ├── geometry.py            # Delaunay, ray-casting, profile opadania, matematyka 2D/3D
    ├── terrain_mesh.py        # Algorytmy siatki TIN (From Scratch, Contours, Stamp, Add Detail)
    ├── groundbox_core.py      # Polecenia historii Undo TerrainEditCommand, knife cut, odbudowa siatki
    ├── operations.py          # Warstwa integracji z API IngeTrazo (viewport, scene, BIM)
    ├── tools.py               # Narzędzia interaktywne (Smoove, FromScratch, AddDetail, Stamp...)
    ├── interactive.py         # Interaktywny przebieg narzędzi (3 kliknięcia, przeciąganie Smoove)
    ├── icons.py               # Generatory wektorowych ikon SVG dla monitorów High-DPI
    ├── dialogs.py             # Natywne okna dialogowe parametrów i raportów CSV
    ├── ui.py                  # Dokowalny panel boczny GroundBoxPanel z zakładkami
    └── math_utils.py          # Funkcje pomocnicze algebry liniowej
```

---

## 🚀 Instalacja

### Wspierane Platformy
* **Windows 10 / 11** (64-bit)
* **Linux** (Ubuntu, Debian, Fedora, Arch)
* **macOS** (eksperymentalnie)

### Instrukcja Krok po Kroku
1. Pobierz lub sklonuj to repozytorium:
   ```bash
   git clone https://github.com/twoja-nazwa/Inge_GroundBox.git
   ```
2. Skopiuj plik `inge_groundbox.py` oraz cały katalog `inge_groundbox/` do folderu wtyczek użytkownika IngeTrazo:
   * **Windows:**
     ```text
     %APPDATA%\ingetrazo\plugins\
     ```
     *(np. `C:\Users\<TwojaNazwaUżytkownika>\AppData\Roaming\ingetrazo\plugins\`)*
   * **Linux:**
     ```text
     ~/.local/share/ingetrazo/plugins/
     ```
     *(lub `$XDG_DATA_HOME/ingetrazo/plugins/`)*
3. Uruchom lub zrestartuj **IngeTrazo**.
4. W oknie programu pojawią się:
   * Pasek narzędzi **GroundBox** z 8 ostrymi wektorowymi ikonami.
   * Pozycja **GroundBox** w menu **Extensions**.
   * Dokowalny boczny panel **GroundBox** w zasobniku Tray.

---

## ⌨️ Skróty i Podręczny Wykaz Działań

| Narzędzie / Akcja | Wywołanie | Wskazówki |
| :--- | :--- | :--- |
| **Od podstaw** | Ikona na pasku lub `Extensions ▸ GroundBox ▸ Od podstaw` | 3 kliknięcia: Start → Długość → Szerokość |
| **Z warstwic** | Zaznacz linie → Kliknij ikonę na pasku | Tworzy teren z poziomic o różnych wysokościach Z |
| **Wytłaczanie (Smoove)** | Kliknij teren → Przeciągnij w górę/dół | `Esc` anuluje, puszczenie LPM zatwierdza deformację |
| **Odcisk (Stamp)** | Zaznacz obrys → Kliknij Odcisk → Kliknij teren | Wycina teren, tworzy półkę i skarpy przejściowe |
| **Rzutowanie (Drape)** | Zaznacz linie i teren → Kliknij Rzutowanie | Przecina trójkąty wzdłuż rzutu, tworzy pas drogi |
| **Dodaj detal** | Kliknij na trójkąt lub krawędź w terenie | Dzieli trójkąt na 4 z eliminacją wiszących węzłów |
| **Odwróć krawędź** | Kliknij wspólną krawędź trójkątów | Odwraca przekątną dla korekty spływów wody |
| **Cofnij / Ponów** | `Ctrl+Z` / `Ctrl+Y` | Pełna integracja z historią projektu IngeTrazo |

---

## 🌐 Wsparcie Wielojęzyczne

Wtyczka posiada kompletne tłumaczenia:
* **Polski (PL)** – Domyślny na systemach w języku polskim.
* **Angielski (EN)** – Domyślny dla systemów międzynarodowych.
* **Przełącznik w locie:** W nagłówku panelu bocznego GroundBox znajduje się selektor języka pozwalający jednym kliknięciem przełączyć interfejs między angielskim a polskim.

---

## 📄 Licencja

Projekt objęty licencją **GNU General Public License v3.0 (GPL-3.0-or-later)**. Szczegóły w pliku `LICENSE`.  
Część ekosystemu otwartego oprogramowania **IngeTrazo**.

# IngeGroundBox – Kompletna Instrukcja Obsługi

Oficjalny podręcznik użytkownika wtyczki **IngeGroundBox** – inżynieryjnego modułu modelowania terenu TIN oraz openBIM dla środowiska **IngeTrazo**.

---

## Spis Treści

1. [Wprowadzenie i Podstawowe Pojęcia](#1-wprowadzenie-i-podstawowe-pojęcia)
2. [Instalacja i Uruchomienie](#2-instalacja-i-uruchomienie)
3. [Przegląd Interfejsu Użytkownika](#3-przegląd-interfejsu-użytkownika)
4. [Szczegółowy Opis 7 Narzędzi GroundBox](#4-szczegółowy-opis-7-narzędzi-groundbox)
   - [4.1 Od podstaw (From Scratch)](#41-od-podstaw-from-scratch)
   - [4.2 Z warstwic (From Contours)](#42-z-warstwic-from-contours)
   - [4.3 Wytłaczanie terenu (Smoove)](#43-wytłaczanie-terenu-smoove)
   - [4.4 Odcisk i skarpy (Stamp)](#44-odcisk-i-skarpy-stamp)
   - [4.5 Rzutowanie dróg i linii (Drape)](#45-rzutowanie-dróg-i-linii-drape)
   - [4.6 Dodaj detal (Add Detail)](#46-dodaj-detal-add-detail)
   - [4.7 Odwróć krawędź (Flip Edge)](#47-odwróć-krawędź-flip-edge)
5. [Obliczenia Inżynierskie i openBIM](#5-obliczenia-inżynierskie-i-openbim)
   - [5.1 Bilans mas ziemnych (Wykop i Nasyp Cut & Fill)](#51-bilans-mas-ziemnych-wykop-i-nasyp-cut--fill)
   - [5.2 Generator poziomic (Slicer warstwic)](#52-generator-poziomic-slicer-warstwic)
   - [5.3 Statystyki powierzchniowe i Raport CSV](#53-statystyki-powierzchniowe-i-raport-csv)
   - [5.4 Klasyfikacja i eksport openBIM IFC](#54-klasyfikacja-i-eksport-openbim-ifc)
6. [Dobre Praktyki i Rozwiązywanie Problemów (FAQ)](#6-dobre-praktyki-i-rozwiązywanie-problemów-faq)

---

## 1. Wprowadzenie i Podstawowe Pojęcia

### Czym jest siatka TIN?
Siatka **TIN (Triangulated Irregular Network)** to wektorowa, trójwymiarowa reprezentacja ukształtowania powierzchni terenu złożona z przylegających do siebie trójkątów. W przeciwieństwie do tradycyjnych siatek rastrowych (np. map wysokościowych DEM):
* Dopasowuje się lokalnie do uskoków terenu, murów oporowych, skarp i krawędzi dróg.
* Nie powoduje efektu schodkowania na stromych zboczach.
* Umożliwia przypisywanie materiałów inżynierskich i metadanych BIM do poszczególnych płaszczyzn.

### Dlaczego IngeGroundBox?
Standardowe narzędzia modelowania architektonicznego często traktują teren jako statyczną bryłę. **IngeGroundBox** daje swobodę znaną z narzędzi *Sandbox* (Piaskownica) programu SketchUp, przenosząc ją bezpośrednio do środowiska **IngeTrazo** i uzupełniając o:
* Precyzyjne obliczenia kubatur mas ziemnych w metrach sześciennych ($m^3$).
* Zgodność z międzynarodowym standardem **openBIM IFC** (`IfcSite`, `IfcRoad`).
* 100% integrację z historią cofania operacji (`Ctrl+Z`).
* Algorytmy zapewniające szczelność topologiczną (brak szczelin i wiszących węzłów).

---

## 2. Instalacja i Uruchomienie

### Ścieżki Instalacji
Skopiuj plik `inge_groundbox.py` oraz cały katalog `inge_groundbox/` do folderu wtyczek użytkownika IngeTrazo:

* **Windows:**
  ```text
  %APPDATA%\ingetrazo\plugins\
  ```
  *(Domyślnie: `C:\Użytkownicy\<TwojaNazwa>\AppData\Roaming\ingetrazo\plugins\`)*
* **Linux:**
  ```text
  ~/.local/share/ingetrazo/plugins/
  ```

### Weryfikacja Poprawności
Po uruchomieniu programu IngeTrazo:
1. W górnym obszarze okna pojawi się dokowalny pasek narzędzi **GroundBox** z 8 wektorowymi ikonami.
2. W menu głównym **Extensions** (Rozszerzenia) pojawi się podmenu **GroundBox**.
3. W bocznym zasobniku (Tray) otworzy się wielozakładkowy panel **GroundBox**.
4. Kliknięcie prawym przyciskiem myszy na narysowane warstwice lub zaznaczony teren wyświetli akcje kontekstowe wtyczki.

---

## 3. Przegląd Interfejsu Użytkownika

Wtyczka integruje się z programem na trzy sposoby:

```
┌────────────────────────────────────────────────────────────────────────┐
│ [⬡] [〰] [🖌] [🔲] [⬇] [➕] [🔄]  <-- Pasek narzędzi Toolbar            │
├─────────────────────────────────────────┬──────────────────────────────┤
│                                         │ ╔══════════════════════════╗ │
│                                         │ ║ GroundBox Panel [🇵🇱 PL]  ║ │
│                                         │ ╠══════════════════════════╣ │
│                                         │ ║ [Od podstaw] [Wytłaczanie║ │
│                                         │ ║ [Odcisk] [Rzutowanie]    ║ │
│         Obszar Roboczy 3D (Viewport)    │ ║ [Edycja TIN] [Raport]    ║ │
│                                         │ ║                          ║ │
│                                         │ ║  Suwaki, Pola numeryczne ║ │
│                                         │ ║  i Przyciski akcji       ║ │
│                                         │ ╚══════════════════════════╝ │
└─────────────────────────────────────────┴──────────────────────────────┘
```

1. **Pasek Narzędzi:** Natychmiastowe uruchamianie każdego z 7 narzędzi.
2. **Panel Boczny (Tray):** Dostęp do suwaków promienia pędzla, parametrów skarpowania, materiałów i raportów.
3. **Menu Kontekstowe (PPM):** Szybkie akcje pod prawym przyciskiem myszy dostosowane do zaznaczonego typu geometrii.
4. **Wybór Języka:** W prawym górnym rogu panelu bocznego znajduje się przełącznik `🇵🇱 Polski` / `🇬🇧 English`.

---

## 4. Szczegółowy Opis 7 Narzędzi GroundBox

---

### 4.1 Od podstaw (From Scratch)

Generuje płaską, poziomą prostokątną siatkę terenu złożoną z trójkątów o zadanym rozstawie.

#### Dwa Tryby Pracy:
1. **Tryb Interaktywny na 3 Kliknięcia (Zalecany):**
   * Kliknij przycisk **Rysuj Teren Interaktywnie (3 Kliknięcia)** w panelu bocznym.
   * **Kliknięcie 1:** Wskaż narożnik początkowy $P_0$.
   * **Kliknięcie 2:** Określ długość i kierunek osi X siatki $P_1$.
   * **Kliknięcie 3:** Rozciągnij szerokość w osi Y $P_2$.
2. **Tryb Numeryczny (Okno Dialogowe):**
   * W zakładce **Od podstaw** podaj:
     * **Szerokość X** (np. `60.0 m`), **Długość Y** (np. `60.0 m`).
     * **Rozstaw siatki** (np. `3.0 m` lub `5.0 m`).
     * **Wysokość bazową Z** (np. `0.0 m`).
     * **Układ przekątnych:**
       * *Naprzemienny (Diamond / Szachownica):* **Zalecany!** Usuwa asymetrię deformacji podczas późniejszego rzeźbienia pędzlem Smoove.
       * *Jednolity (Ukośny /):* Wszystkie przekątne w jednym kierunku.
   * Kliknij **Generuj Siatkę Terenu**.

> [!TIP]
> Dla domków jednorodzinnych optymalny rozstaw oczek to **2.0 – 3.0 m**. Dla dużych działek inwestycyjnych używaj rozstawu **5.0 – 10.0 m**, aby zachować płynność działania.

---

### 4.2 Z warstwic (From Contours)

Automatycznie buduje pofałdowaną powierzchnię terenu 3D z zaimportowanych lub narysowanych warstwic geodezyjnych.

#### Przebieg Pracy:
1. Narysuj linie poziomic na ich rzeczywistych wysokościach $Z$ (np. narzędziem Linia lub Łuk) lub zaimportuj podkład geodezyjny DXF/DWG.
2. Zaznacz wszystkie linie warstwic (narzędziem Zaznacz lub w drzewie obiektów Outliner).
3. Kliknij ikonę **Z warstwic** (〰) na pasku narzędzi.
4. W oknie konfiguracji określ:
   * **Maksymalną długość segmentu:** Algorytm dogęszcza długie odcinki dodatkowymi punktami co zadaną odległość (np. co `5.0 m`).
   * **Współczynnik odrzucania zewnętrznego:** Automatycznie usuwa nienaturalnie rozciągnięte, ostre trójkąty na obrzeżach działki.
   * **Zmiękczanie krawędzi (Soft edges):** Włącza gładkie cieniowanie powierzchni (*smooth shading*).
5. Kliknij **OK** – powstały teren zostaje zgrupowany i otagowany klasą `IfcSite`.

---

### 4.3 Wytłaczanie terenu (Smoove)

Organiczny pędzel sferyczny do modelowania wzniesień, nasypów, rowów, skarp i zagłębień w terenie.

#### Przebieg Pracy:
1. Aktywuj narzędzie **Smoove** (🖌) na pasku narzędzi.
2. W panelu bocznym dostosuj **Promień pędzla (m)** oraz **Siłę rzeźbienia**.
3. Wybierz **Profil opadania (Falloff)**:
   * **Kosinusowy (Cosine):** Oryginalny profil SketchUpa – płynne, naturalne przejście od centrum pędzla do jego granicy.
   * **Gaussa:** Kształt dzwonu o bardzo łagodnych krawędziach zewnętrznych.
   * **Liniowy:** Kształt stożka o ostrym wierzchołku.
   * **Smoothstep:** Wielomian sześcienny Hermite'a.
4. **Rzeźbienie w Widoku 3D:**
   * Najedź kursorem na teren – czerwony okrąg pokaże aktualny zasięg pędzla.
   * **Wciśnij lewy przycisk myszy i przeciągnij w górę lub w dół.** Siatka deformuje się płynnie w czasie rzeczywistym.
   * Zwolnij przycisk myszy, aby zatwierdzić operację.
   * Klawisz `Esc` natychmiast anuluje bieżące przeciąganie.

---

### 4.4 Odcisk i skarpy (Stamp)

Wycina w pofałdowanym terenie poziomą platformę pod budynek, parking lub taras, automatycznie formując skarpy przejściowe.

#### Przebieg Pracy:
1. Narysuj płaski obrys (ściankę lub grupę) reprezentujący rzut fundamentu, drogi dojazdowej lub płyty tarasu.
2. Umieść obrys nad pofałdowanym terenem.
3. Zaznacz obrys fundamentu.
4. Kliknij narzędzie **Odcisk (Stamp)** (🔲).
5. Kliknij w pofałdowany teren, w którym chcesz odcisnąć platformę.
6. W wyświetlonym oknie dialogowym ustaw:
   * **Szerokość skarpy / odsunięcie (m):** Pozioma odległość przejścia od krawędzi płyty do naturalnego terenu (decyduje o nachyleniu skarpy).
   * **Wysokość posadowienia Z:** Rzędna docelowa półki (lub zaznacz opcję *Wysokość automatyczna*, która ustawi półkę na średniej wysokości gruntu pod budynkiem).
   * **Materiał półki i skarpy:** np. Bruk/Beton dla półki oraz Grunt dla skarpy.
7. Kliknij **Wykonaj** – teren zostaje uformowany, a na pasku statusu pojawi się dokładna objętość **wykopu** i **nasypu** w $m^3$.

---

### 4.5 Rzutowanie dróg i linii (Drape)

Rzutuje pionowo w dół linie ścieżek, dróg, chodników oraz granic ewidencyjnych działki na pofałdowaną powierzchnię terenu.

#### Przebieg Pracy:
1. Wrysuj linie lub polilinie ścieżek w rzucie z góry (nad terenem).
2. Zaznacz linie oraz grupę terenu docelowego.
3. Kliknij narzędzie **Rzutowanie (Drape)** (⬇).
4. W panelu bocznym wybierz:
   * **Szerokość pasa drogowego = 0.0 m:** Wykonuje precyzyjne cięcie siatki wzdłuż linii (*knife-cut*).
   * **Szerokość pasa drogowego > 0.0 m (np. 3.5 m):** Wytłacza pas drogowy o zadanej szerokości i odciska go na pofałdowanym terenie.
   * Wybierz **Materiał drogi** (Asfalt, Bruk, Żwir, Ścieżka parkowa).
5. Kliknij **Rzutuj Linie na Teren** – siatka terenu zostaje rozcięta, krawędzie drogi stają się twarde (widoczne), a nawierzchnia otrzymuje wybrany materiał oraz klasyfikację `IfcRoad`.

---

### 4.6 Dodaj detal (Add Detail)

Lokalnie zagęszcza wybrane trójkąty siatki w miejscach wymagających dużej precyzji rzeźbienia (np. krawędzie skarp, obrzeża cieków wodnych).

#### Dwa Sposoby Użycia:
1. **Tryb Interaktywny (Klikanie w terenie):**
   * Wybierz narzędzie **Dodaj detal** (➕) z paska narzędzi lub panelu bocznego.
   * Najedź na teren i **kliknij lewym przyciskiem myszy na dowolny trójkąt lub krawędź**.
   * Kliknięty trójkąt zostaje podzielony na 4 mniejsze trójkąty.
   * **Bisekcja konforemna:** Sąsiednie trójkąty dzielące krawędzie są automatycznie dzielone na 2 części, co gwarantuje **100% szczelność siatki** – nie powstają żadne wiszące węzły (*T-junctions*) ani pęknięcia.
   * Możesz klikać wielokrotnie w różne miejsca terenu.
2. **Podział Masowy:**
   * Zaznacz całą grupę terenu.
   * W panelu bocznym w zakładce **Edycja siatki (TIN)** kliknij **◬ Podziel Zaznaczone Trójkąty (x4)**.

---

### 4.7 Odwróć krawędź (Flip Edge)

Odwraca wspólną przekątną między dwoma sąsiednimi trójkątami w czworokącie wypukłym.

#### Przebieg Pracy:
1. Aktywuj narzędzie **Odwróć krawędź** (🔄).
2. Kliknij na wewnętrzną krawędź między dwoma trójkątami.
3. Jeżeli trójkąty tworzą czworokąt wypukły, przekątna natychmiast przeskoczy na drugą parę wierzchołków.
4. **Zastosowanie inżynierskie:**
   * Usuwanie nienaturalnych "garbów" i "schodków" na stokach.
   * Korygowanie kierunku spływu wód opadowych do rowów i studzienek.
   * Wyrównywanie linii grzbietowych zgodnie z dokumentacją projektową.

---

## 5. Obliczenia Inżynierskie i openBIM

### 5.1 Bilans mas ziemnych (Wykop i Nasyp Cut & Fill)
Podczas operacji niwelacyjnych algorytm dokonuje całkowania objętości metodą pryzm trójkątnych:
$$\Delta V = \sum_{i} A_i \cdot \frac{\Delta z_{i,1} + \Delta z_{i,2} + \Delta z_{i,3}}{3}$$
* **Wykop ($m^3$):** Kubatura gruntu rodzimego do usunięcia poniżej pierwotnej rzędnej.
* **Nasyp ($m^3$):** Kubatura gruntu do nawiezienia i zagęszczenia powyżej pierwotnej rzędnej.
* **Bilans netto:** Różnica pozwalająca ocenić zapotrzebowanie na transport kruszywa na plac budowy.

### 5.2 Generator poziomic (Slicer warstwic)
Aby wygenerować mapę warstwicową z uformowanego terenu 3D:
1. Otwórz zakładkę **Analiza & Raport** w panelu bocznym.
2. Wpisz **Skok poziomic (m)**, np. `1.0 m` lub `0.5 m`.
3. Kliknij **Generuj Poziomice z Terenu (Contours)**.
4. Program wygeneruje precyzyjne krzywe 3D na każdej płaszczyźnie poziomej.

### 5.3 Statystyki powierzchniowe i Raport CSV
W zakładce **Analiza & Raport** kliknij **Odśwież Statystyki**:
* **Powierzchnia rzeczywista 3D:** Suma pól wszystkich nachylonych trójkątów (istotna przy wycenie trawy z rolki, darniowania i geowłókniny).
* **Powierzchnia w rzucie 2D:** Rzut płaski działki w osi Z.
* **Skrajne rzędne:** $Z_{\min}$, $Z_{\max}$ oraz całkowita deniwelacja $\Delta Z$.
* **Średni i maksymalny spadek (% i °):** Ważona powierzchnią średnia stromość stoku.
* **Eksport do CSV:** Zapisuje pełną tabelę (łącznie ze spadkami) do pliku CSV z separatorem średnikowym i kodowaniem `utf-8-sig` (gotowy do otwarcia w **Excelu** i **LibreOffice Calc**).

### 5.4 Analiza spadków terenu (Heatmap)
Narzędzie w zakładce **Analiza & Raport** bada nachylenie każdego trójkąta terenu względem płaszczyzny horyzontu i klasyfikuje spadki według 10 standardowych przedziałów inżynieryjno-urbanistycznych:
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

**Jak używać:**
1. Zaznacz grupę terenu.
2. W zakładce **Analiza & Raport** kliknij **🎨 Pokoloruj wg spadków**.
3. Powierzchnia terenu natychmiast wyświetli mapę termiczną z legendą i bilansem powierzchni poszczególnych klas.
4. Aby wrócić do widoku materiałów i tekstur, kliknij **↺ Przywróć oryginalne materiały** (operacja jest w 100% nieniszcząca).

### 5.5 Zamknięcie bryły 3D (Cokół terenu / Watertight Skirt)
Zwykła powierzchnia TIN to tzw. otwarta powłoka 2.5D bez grubości. Aby zamienić ją w pełną bryłę:
1. Zaznacz grupę terenu.
2. W zakładce **Analiza & Raport** ustaw **Głębokość cokołu (m)** (odległość poniżej najniższego punktu $Z_{\min}$, domyślnie `1.0 m`).
3. Wybierz materiał ścian cokołu (np. *Grunt / Podłoże* lub *Beton fundamentowy*).
4. Kliknij **📦 Utwórz bryłę 3D (Cokół)**.
5. Algorytm wygeneruje pionowe ściany boczne oraz szczelne dno (triangulacja ucha). Otrzymana bryła posiada **0 otwartych krawędzi (100% Manifold Solid)** i jest sklasyfikowana jako **`IfcGeographicElement`** (*Solid Terrain Base*). Idealna do druku 3D, przekrojów geotechnicznych i modeli kubaturowych.

### 5.6 Klasyfikacja i eksport openBIM IFC
Wtyczka dba o standardy cyfrowego bliźniaka budynku:
* Model terenu TIN $\to$ klasa **`IfcSite`**
* Warstwa gruntu $\to$ klasa **`IfcGeotechnicalStratum`**
* Zrzutowane drogi $\to$ klasa **`IfcRoad`**
* Lita bryła cokołu 3D $\to$ klasa **`IfcGeographicElement`**

Wyeksportowany plik IFC z IngeTrazo (`Plik ▸ Eksportuj ▸ IFC`) otwiera się poprawnie we wszystkich przeglądarkach BIM (BIM Vision, Solibri, Revit, ArchiCAD).

---

## 6. Dobre Praktyki i Rozwiązywanie Problemów (FAQ)

| Problem | Przyczyna i Rozwiązanie |
| :--- | :--- |
| **Komunikat: "Nie znaleziono grupy terenu"** | Upewnij się, że teren jest obiektem typu Group. Jeśli geometria jest luźna, zaznacz ją i utwórz grupę, lub nadaj grupie nazwę zawierającą słowo "Teren" lub "Terrain". |
| **Ostre, bardzo długie trójkąty na obrzeżach** | W oknie narzędzia *Z warstwic* zwiększ współczynnik odrzucania krawędzi (*Prune Boundary Ratio*) lub ręcznie usuń zewnętrzne trójkąty. |
| **Spadek wydajności przy rzeźbieniu pędzlem Smoove** | Narzędzia *Dodaj detal* używaj wyłącznie lokalnie w miejscach wymagających zagęszczenia. Nie zagęszczaj niepotrzebnie całej siatki liczącej ponad 100 000 trójkątów. |
| **Linie nie przecinają terenu przy rzutowaniu Drape** | Upewnij się, że rzutowane linie w rzucie z góry (XY) leżą całkowicie wewnątrz granic obrysu terenu i znajdują się powyżej jego powierzchni. |
| **Zmiana języka interfejsu** | W prawym górnym rogu panelu bocznego GroundBox wybierz z listy `🇵🇱 Polski` lub `🇬🇧 English`. Zmiana następuje natychmiast. |

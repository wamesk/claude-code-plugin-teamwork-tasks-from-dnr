# DNR Strečnianska v1.2 — Teamwork Task Listy

Zdroj: `tests/fixtures/DNR_Strecnianska_v1.2.docx`
Klient: Družstvo lekárov — Strečnianska
Referencia: PON1107

Sprievodný súbor `*_TeamworkTasks.xlsx` v tom istom adresári je 1:1 import-ready pre Teamwork (Options → Import → Microsoft Excel).

## Konvencie

- **Akceptačné kritériá** sú checkbox list (`- [ ]`), píše sa z pohľadu používateľa.
- **Cieľ** je 1–3 vety pre rýchle pochopenie účelu tasku (Plan-mode friendly).
- **Technický popis** obsahuje cesty súborov, snippety, edge cases.
- **Závislosť** (ak je) je samostatná pod-sekcia v akceptačných kritériách.

## Mapovanie pracnosti

| # | Task list | Tasky | MD | Hodín |
|---|---|---|---|---|
| 1 | 4.1 Ročný zálohový predpis | 9 | 2.5 | 20.0 |
| 2 | 4.2 Automatické párovanie platieb z banky | 8 | 1.5 | 12.0 |
| 3 | 4.3 Ročné zúčtovanie služieb | 8 | 2 | 16.0 |
| **Spolu** | | **25** | **6** | **48.0** |

---

## TASK LIST 1: 4.1 Ročný zálohový predpis

### Pôvodné znenie DNR

> ROZŠÍRENIE Č. 1 — ROČNÝ ZÁLOHOVÝ PREDPIS (DNR sekcia 4.1)
>
> ** 4.1.1 Biznisový účel **
> Namiesto 12 mesačných faktúr vznikne na začiatku roka jeden PDF dokument — ročný zálohový predpis — ktorý slúži ako daňový doklad pre celý fakturačný rok. Obsahuje rozpis 12 rovnakých splátok so splatnosťou k definovanému dňu mesiaca. Nájomca platí 12× ročne s rovnakým variabilným symbolom; systém platby automaticky páruje (viď modul 4.2).
>
> ** Poznámka k mesačnej fakturácii **
> Režim ročného zálohového predpisu nahrádza mesačné faktúry pre konkrétne zmluvy. Existujúca funkcia mesačnej fakturácie zostáva v systéme pre prípadné budúce použitie, no v dennej prevádzke Družstva lekárov sa nebude bežne používať.
>
> ** 4.1.2 Zásadné rozhodnutia **
> • Fakturačné obdobie: Vždy kalendárny rok (január — december).
> • Začiatok zmluvy v priebehu roka: Zmluvy začínajú vždy 1. dňom mesiaca. V rámci mesiaca sa nealikvotuje. Ročný predpis sa pripraví od mesiaca nástupu do decembra; od 1. januára nasledujúceho roka štandardný 12-mesačný predpis. (v1.2)
> • Obsah predpisu: Nájomné (prenajatý priestor + podiel na spoločných priestoroch) + služby spojené s nájmom (elektrina, voda/stočné, UK a TUV). Zoznam je otvorený — v budúcnosti môžu pribudnúť ďalšie položky.
> • Sadzby: Nájomné a spoločné priestory: €/m²/rok. Voda, UK a TUV: €/m²/rok. Elektrina: (1) sadzba €/m²/rok s dynamickým meraním alebo (2) fixná záloha bez merania alebo (3) vlastná prípojka (položka = 0 € alebo vôbec nie je).
> • Členenie po priestoroch: PDF zálohového predpisu zobrazí položky rozčlenené po jednotlivých priestoroch zmluvy (kancelária a sklad ako dva samostatné riadky), aj keď je sadzba rovnaká. Energie sa viažu na priestor a zobrazia sa per priestor. (v1.2)
> • DPH: Každá položka má vlastnú sadzbu DPH. Systém podporuje viacero sadzieb v rámci jedného dokladu.
> • Konštantný symbol: Staticky 0308 pre všetky zálohové predpisy.
> • Variabilný symbol: Trojciferné číslo zmluvy. Pri prechode z papierovej evidencie sa zachovajú pôvodné variabilné symboly, ktoré majú nájomcovia desiatky rokov. Pre nové zmluvy systém priradí ďalšie voľné číslo. (v1.2)
> • Číselný rad: Samostatný oddelený rad pre zálohové predpisy, navrhovaný formát ZP[RRRR]-[NNNN] (napr. ZP2026-0001).
> • Splatnosť: Default 5. deň aktuálneho mesiaca podľa zaužívanej praxe Družstva lekárov (marcová splátka má splatnosť 5. marca). Dátum dodania je posledný deň príslušného mesiaca. Admin môže prepísať per zmluva. (v1.2)
> • Zmena ceny počas roka: Pôvodný predpis zostáva nezmenený. Rozdiel sa vyrieši v ročnom zúčtovaní (viď 4.3). Pre úplne novú položku počas roka (nový priestor, nová služba) sa pripraví dodatková zmluva platná do konca aktuálneho obdobia; od ďalšieho obdobia sa zlúči s pôvodnou zmluvou. (v1.2)
> • Predčasné ukončenie zmluvy: Admin zmení dátum konca zmluvy na skutočný dátum ukončenia. Systém pri ročnom zúčtovaní započíta iba reálne odbehnuté mesiace; prípadný preplatok/nedoplatok sa vyrieši v rámci štandardného ročného zúčtovania, nie počas roka. (v1.2)
> • Preplatok z minulého roka: Preplatok sa NEPRENÁŠA do nového predpisu. Klient ho vyrovná vrátením peňazí nájomcovi mimo systém. Nájomca tak platí celý rok v plnej výške bez zníženia januárovej splátky. (v1.2)
> • Príprava a odoslanie: Dvojkrokový proces: (1) admin zvolí „Pripraviť PDF" v detaile zmluvy, skontroluje položky a sumy, (2) zvolí „Odoslať e-mailom" — PDF odoslané klientovi na e-mail evidovaný u zákazníka.
>
> ** 4.1.3 Scenáre použitia **
>
> Scenár 1 — Ročné pripravenie predpisu (začiatok roka):
> 1. Admin otvorí detail zmluvy a zvolí „Pripraviť ročný zálohový predpis".
> 2. Systém zobrazí formulár: fakturačný rok (default = aktuálny), dátum splatnosti v mesiaci (default 5. deň aktuálneho mesiaca, prepisateľný), dátum dodania (default posledný deň mesiaca), číselný rad. (v1.2)
> 3. Systém zobrazí náhľad — 12 rovnakých splátok, sumarizáciu po položkách a po DPH sadzbách. Admin skontroluje čísla.
> 4. Po potvrdení sa pripraví daňový doklad, mesačný splátkový kalendár a PDF dokument.
> 5. Admin zvolí „Odoslať e-mailom" — PDF ide na e-mail zákazníka.
>
> Scenár 2 — Nový nájomca počas roka (nástup k 1. dňu mesiaca):
> 6. Admin pri vytvorení zmluvy zadá dátum platnosti vždy od 1. dňa mesiaca (napr. 1. 9. 2026).
> 7. Pri pripravení ročného predpisu systém automaticky vytvorí iba toľko splátok, koľko mesiacov zostáva do konca roka.
> 8. Od 1. 1. nasledujúceho roka admin pripraví štandardný 12-mesačný predpis.
>
> Scenár 3 — Zmena ceny počas roka (napr. zvýšenie poplatku za UK od 1. 7.):
> 9. Pôvodný ročný predpis zostáva nedotknutý (daňový doklad sa neupravuje spätne).
> 10. Rozdiel sa prejaví v ročnom zúčtovaní energií na konci roka cez skutočné náklady vs. zaplatené zálohy (viď 4.3).
>
> Scenár 4 — Hromadné pripravenie pre začiatok roka:
> 11. Admin v zozname zmlúv označí všetky aktívne zmluvy roka X (alebo cez filter „aktívne k 1. 1.").
> 12. Zvolí hromadnú akciu „Pripraviť ročné zálohové predpisy".
> 13. Systém zobrazí náhľad tabuľky (zmluva, suma, počet splátok, číselný rad) — admin skontroluje a potvrdí.
> 14. Po potvrdení sa všetky doklady pripravia. Odoslanie je následne hromadné alebo per zmluva.
>
> Scenár 5 — Predčasné ukončenie zmluvy v priebehu roka: (v1.2)
> 15. Nájomca a družstvo sa dohodnú na predčasnom ukončení (napr. k 30. 7.). Admin zmení dátum konca zmluvy.
> 16. Pôvodný ročný zálohový predpis zostáva nedotknutý; nájomca doplatí splátky podľa pôvodného plánu až do skutočného konca prenájmu.
> 17. Pri ročnom zúčtovaní systém započíta iba reálne odbehnuté mesiace zmluvy. Prípadný preplatok/nedoplatok sa vyrieši cez štandardný proces ročného zúčtovania na konci roka — nie počas roka.
>
> ** 4.1.4 Odhad pracnosti **
> Ročný zálohový predpis: 2,5 MD (logika prípravy predpisu, formát PDF podľa vzoru SOMPET, hromadná akcia, alikvótny výpočet).

### Task 1.1 — 4.1.1 Príprava systémových štruktúr pre ročný zálohový predpis

**Priorita:** High · **Odhad:** 2h (120 min)

## Akceptačné kritériá
- [ ] V systéme pribudol nový typ dokladu „Ročný zálohový predpis", ktorý existuje popri faktúre, predfaktúre a dobropise.
- [ ] Pre každý zálohový predpis vie systém uchovať 12 (alebo menej) samostatných mesačných splátok so vlastnou splatnosťou.
- [ ] Platby z banky sa dajú napojiť priamo na konkrétnu splátku, nie iba na master doklad.
- [ ] Existujúce faktúry/predfaktúry/dobropisy fungujú nezmenene.

---

## Cieľ
Pripraviť dátový základ pre ročný zálohový predpis. Existujúca tabuľka `invoices` sa rozšíri o nový typ dokladu (ANNUAL_ADVANCE='4') a pridá sa samostatná tabuľka `invoice_schedule_installments` na uchovanie 12 splátok per master Invoice. Existujúce faktúry / predfaktúry / dobropisy a celý mesačný fakturačný flow zostávajú nedotknuté.

## Technický popis
### Migrácie
1. `database/migrations/<dnes>_add_annual_advance_to_invoice_types.php`:
   - `ALTER TABLE invoices MODIFY COLUMN type ENUM('1','2','3','4') NOT NULL;`
   - Rovnako pre `invoice_patterns.type`.
2. `database/migrations/<dnes>_create_invoice_schedule_installments_table.php`:
   - ulid PK, FK `invoice_id` (cascade), `sequence` (1..12), `year`, `month`, `due_date`, `delivery_date`, `variable_symbol`, `amount_with_tax`/`amount_without_tax` (decimal 10,2), `paid_amount`, status enum (`unpaid/partially_paid/paid/overpay`).
   - UNIQUE (`invoice_id`, `sequence`).
   - `timestampsTz`, `softDeletesTz`.
3. `database/migrations/<dnes>_add_installment_id_to_invoice_payments.php`:
   - FK `installment_id` (nullable, `nullOnDelete`) za `invoice_id`.
   - Nový stĺpec `payment_date` (date, nullable) pre dátum pripísania z bmailu.

### Enum
- `app/Enums/InvoiceType.php` — `case ANNUAL_ADVANCE = '4';`, doplniť `title()` (lang key `invoice.type.annual_advance`) a `invoiceTypeFolderName()` → `'annual_advance'`.

### Edge cases
- Rollback enumu zachová pôvodné `'1','2','3'` — použiť raw `ALTER TABLE`, nie `change()`.
- `payment_date` na `invoice_payments` odlišuje dátum pripísania od `created_at` (potrebné pre bmail import).

### Task 1.2 — 4.1.2 Evidencia mesačných splátok v rámci predpisu

**Priorita:** High · **Odhad:** 1.5h (90 min)

## Akceptačné kritériá
- [ ] Pre každý ročný predpis vie systém zobraziť zoznam splátok s aktuálnym stavom (uhradená / čiastočne / neuhradená / preplatok).
- [ ] Pri každej platbe sa stav príslušnej splátky automaticky aktualizuje.
- [ ] Vývojár vie cez Eloquent jednoducho dotiahnuť všetky splátky predpisu zoradené podľa sekvencie.

---

## Cieľ
Vytvoriť Eloquent model `InvoiceScheduleInstallment` s relations na `Invoice` a `InvoicePayment` a doplniť relations na opačnej strane. Mirror logiky `ChangeInvoiceStatusByPaymentJob` pre prepočet stavu splátky podľa pripojených platieb (UNPAID → PARTIALLY_PAID → PAID → OVERPAY).

## Technický popis
### Modely
1. `app/Models/InvoiceScheduleInstallment.php`:
   - extends `BaseModel`, use `SoftDeletes`, `$guarded = ['id']`.
   - Casty: `due_date`/`delivery_date` → `date`; `amount_*`/`paid_amount` → `decimal:2`.
   - Relations: `invoice()` BelongsTo, `payments()` HasMany (`InvoicePayment`, `'installment_id'`).
   - Metódy: `totalPaid(): float`, `remaining(): float`, `recalculateStatus(): void` (mirror logiky `ChangeInvoiceStatusByPaymentJob` — UNPAID/PARTIALLY_PAID/PAID/OVERPAY).

2. `app/Models/Invoice.php`:
   - `installments(): HasMany` s `orderBy('sequence')`.
   - Helper `isAnnualAdvance(): bool`.

3. `app/Models/InvoicePayment.php`:
   - `installment(): BelongsTo`.

4. `database/factories/InvoiceScheduleInstallmentFactory.php` pre testy.

### Acceptance test
- Pest `InvoiceScheduleInstallmentTest::test_status_changes_with_payments` overí prechod stavov.

### Task 1.3 — 4.1.3 Logika výpočtu ročného zálohového predpisu

**Priorita:** High · **Odhad:** 3h (180 min)

## Akceptačné kritériá
- [ ] Pre zmluvu platnú od 1. 1. systém pripraví 12 rovnakých splátok pre celý rok.
- [ ] Pre zmluvu, ktorá začína v priebehu roka (napr. od 1. 9.), systém pripraví iba toľko splátok, koľko mesiacov zostáva do konca roka.
- [ ] Položky predpisu sú rozčlenené po jednotlivých priestoroch zmluvy.
- [ ] Sumy splátok sú rovnaké; prípadný haliérový rozdiel pri zaokrúhľovaní pohlcuje posledná splátka.
- [ ] Master Invoice obsahuje snapshot kontaktných a fakturačných údajov ku dňu vystavenia.

---

## Cieľ
Vytvoriť service `AnnualAdvanceBuilder`, ktorý pre danú zmluvu, rok a parametre vyrobí master Invoice (type=ANNUAL_ADVANCE) + N splátok (12 alebo menej pre nového nájomcu v priebehu roka) + sumarizáciu po DPH a per priestor. Snapshot kontaktných údajov nasleduje pattern z existujúceho `GenerateInvoiceTrait::createInvoice()`. Zaokrúhľovanie centov vyrieši posledná splátka.

## Technický popis
### Service
`app/Services/Invoice/AnnualAdvanceBuilder.php`:
```php
class AnnualAdvanceBuilder {
    public function __construct(
        private readonly Contract $contract,
        private readonly int $year,
        private readonly int $dueDayOfMonth = 5,
        private readonly ?int $deliveryDayOfMonth = null,
        private readonly ?string $invoicePatternId = null,
    ) {}
    public function preview(): AnnualAdvancePreview;
    public function persist(): Invoice;
}
```

### DTO
`app/Services/Invoice/AnnualAdvancePreview.php` — `items[]`, `installments[]`, `totalsByVat[]`.

### Logika
1. Počiatočný mesiac: ak `contract->valid_from->year === year` → `startMonth = valid_from->month`, inak `1`. `endMonth = 12`.
2. Položky per priestor: iter `contract->items` `groupBy('premise_id')`. Quantity × monthsCount pre fixné. Energie s `dynamic_quantity = ENABLED` → fixná ročná záloha z `contract_items.quantity` (nie z odpočtov). `price = 0` → vlastná prípojka (preskočiť / zachovať 0 € pre transparentnosť).
3. Splátky: iter `startMonth..12`, `due_date = CarbonImmutable::create($year, $month, $dueDayOfMonth)`, `delivery_date = $deliveryDayOfMonth ?? endOfMonth`. VS splátky = `contract->variable_symbol` (Task 1.8). Suma = `totalAnnual / monthsCount`; posledná splátka = `totalAnnual - sum(predošlé)`.
4. Master Invoice: snapshot zákazníka/dodávateľa (pattern z `GenerateInvoiceTrait::createInvoice()`), `type = ANNUAL_ADVANCE`, VS = `invoice_pattern->getNumber()` (ZP2026-0001), `due_date` prvej splátky, `delivery_date` poslednej splátky, `tax_liability` = `due_date` prvej splátky.

### Edge cases
- Položky bez `premise_id` (paušál) → samostatný invoice_item bez priestoru.
- Viacero rovnakých priestorov → zoskupiť per `premise_id` + `title`.

### Task 1.4 — 4.1.4 Funkcia „Pripraviť ročný zálohový predpis" v detaile zmluvy

**Priorita:** High · **Odhad:** 2h (120 min)

## Akceptačné kritériá
- [ ] V detaile zmluvy je tlačidlo „Pripraviť ročný zálohový predpis".
- [ ] Admin vyplní fakturačný rok, deň splatnosti, dátum dodania a vyberie číselný rad.
- [ ] Po potvrdení systém vytvorí daňový doklad so splátkami a presmeruje admina na jeho detail, kde vidí všetky splátky.
- [ ] Akcia je auditovaná v Nova Action Log.

---

## Cieľ
Vystaviť `AnnualAdvanceBuilder` ako Nova action v detaile zmluvy. Formulár (rok, deň splatnosti, dátum dodania, číselný rad), volanie buildera, redirect na vytvorený Invoice s HasMany installments slúžiacim ako preview. Auditovateľné cez Nova Action Log.

## Technický popis
### Nova action
`app/Nova/Actions/PrepareAnnualAdvance.php` extends `Laravel\Nova\Actions\Action`:
- `fields()`:
  - `Number::make('Fakturačný rok', 'year')->default(now()->year)`.
  - `Number::make('Deň splatnosti v mesiaci', 'due_day')->default(5)->min(1)->max(28)`.
  - `Date::make('Dátum dodania', 'delivery_date')->nullable()->help('Prázdne = posledný deň mesiaca')`.
  - `Select::make('Číselný rad', 'invoice_pattern_id')->options(InvoicePattern::where(['company_id' => get_company_id(), 'type' => InvoiceType::ANNUAL_ADVANCE->value])->pluck('title', 'id'))->required()`.
- `handle()`:
  - per `Contract` spustí `AnnualAdvanceBuilder->persist()`.
  - vráti `Action::redirect(config('nova.path').'/resources/invoices/'.$invoice->id)`.

### Registrácia
`app/Nova/Contract.php::actions()` — pridať `(new PrepareAnnualAdvance)->showOnDetail()->confirmButtonText('Vytvoriť predpis')`.

### Preview
- Preview riešený redirectom na Invoice detail s HasMany installments (jednoduché).
- Ak ostane čas — vlastný ResourceTool `nova-components/AnnualAdvancePreview` so side-by-side náhľadom pred submit.

### Task 1.5 — 4.1.5 PDF výstup ročného zálohového predpisu (vzor SOMPET)

**Priorita:** High · **Odhad:** 3h (180 min)

## Akceptačné kritériá
- [ ] PDF dokument vyzerá konzistentne so vzorom SOMPET dodaným klientom.
- [ ] Položky sú rozčlenené po jednotlivých priestoroch zmluvy (kancelária a sklad ako samostatné riadky), aj keď je sadzba rovnaká.
- [ ] Dokument obsahuje tabuľku 12 (alebo menej) splátok s variabilným symbolom a dátumom splatnosti pre každú.
- [ ] V hlavičke platobných údajov je konštantný symbol 0308.
- [ ] Sumarizácia po DPH sadzbách je viditeľná.

### Závislosť
- Pred začatím overiť, že vzor SOMPET je v `docs/podklady/SOMPET_predpis.pdf` (DNR sekcia 8 bod 3, ✅ dodaný).

---

## Cieľ
Pripraviť Blade view `invoice/annual_advance.blade.php` v štýle vzoru SOMPET (referenčný PDF od klienta). Pattern znovupoužiť z existujúceho `invoice/invoice.blade.php`, ale s dvomi rozdielmi: items zoskupené per priestor (kancelária a sklad ako samostatné riadky aj pri rovnakej sadzbe) a samostatná tabuľka 12 splátok s VS a splatnosťami. Konštantný symbol 0308 statický.

## Technický popis
### Blade view
`resources/views/invoice/annual_advance.blade.php` (inšpirácia: `invoice.blade.php`):
- Items zoskupené per `premise_title`:
  ```blade
  @php $grouped = $invoice->items->groupBy('premise_title'); @endphp
  @foreach($grouped as $premiseTitle => $items)
      <tr class="premise-header"><td colspan="5"><strong>{{ $premiseTitle ?: 'Bez priestoru' }}</strong></td></tr>
      @foreach($items as $item) … @endforeach
  @endforeach
  ```
- Sekcia „Mesačný splátkový kalendár":
  ```blade
  <h3>Mesačný splátkový kalendár</h3>
  <table class="installments">
      <thead><tr><th>Mesiac</th><th>VS</th><th>Splatnosť</th><th class="text-right">Suma s DPH</th></tr></thead>
      <tbody>
      @foreach($invoice->installments as $inst)
          <tr>
              <td>{{ $inst->sequence }}/{{ count($invoice->installments) }} — {{ Carbon::create($inst->year, $inst->month)->translatedFormat('F Y') }}</td>
              <td>{{ $inst->variable_symbol }}</td>
              <td>{{ $inst->due_date->format('d.m.Y') }}</td>
              <td class="text-right">{{ \App\Utils\Helpers\Currency::format($inst->amount_with_tax, $invoice->currency) }}</td>
          </tr>
      @endforeach
      </tbody>
  </table>
  ```
- Konštantný symbol `0308` v hlavičke platobných údajov.
- DPH summary `groupBy('tax')` — základ / DPH / spolu per sadzba.

### Controller
`app/Http/Controllers/v1/InvoiceController::generateOnePdf()` funguje automaticky cez `InvoiceType::from()->invoiceTypeFolderName()` → `annual_advance` → view `invoice.annual_advance`.

### CSS
`public/css/invoice.css` — pridať `.installments` (border, padding) a `.premise-header` (light gray bg, bold).

### Task 1.6 — 4.1.6 Hromadné pripravenie zálohových predpisov pre všetky aktívne zmluvy

**Priorita:** Medium · **Odhad:** 2h (120 min)

## Akceptačné kritériá
- [ ] V zozname zmlúv je filter „Aktívne k dátumu" — admin vyberie napr. 1. 1. 2027.
- [ ] Vie hromadne označiť aktívne zmluvy a spustiť hromadnú akciu „Pripraviť ročné zálohové predpisy".
- [ ] Po potvrdení sa pre každú zmluvu vytvorí ročný zálohový predpis.
- [ ] V Nova Action Log je vidieť, ktorých zmlúv sa akcia dotkla.

---

## Cieľ
Bulk variant Task 1.4 cez Nova standalone-false action nad selection v indexe zmlúv + filter `Aktívne k dátumu`. Spustenie v `DB::transaction` per zmluva, chyby zhrnúť v Action response. Slúži na hromadné pripravenie celého roka jedným kliknutím (DNR scenár 4).

## Technický popis
### Nova bulk action
`app/Nova/Actions/PrepareAnnualAdvanceBulk.php` extends `Action`:
- Rovnaké fields ako `PrepareAnnualAdvance`.
- `$standalone = false` (pracuje nad selection).
- `handle()` v `DB::transaction` per zmluva. Errory cez `Action::danger()` zhrnúť per zlyhaná zmluva.

### Filter
`app/Nova/Filters/ContractActiveAtFilter.php`:
```php
public function apply(NovaRequest $request, $query, $value) {
    $date = $value ?: now()->startOfYear()->format('Y-m-d');
    return $query
        ->where('valid_from', '<=', $date)
        ->where(fn ($q) => $q->whereNull('valid_to')->orWhere('valid_to', '>=', $date));
}
```
Registrácia vo `Contract::filters()`.

### Registrácia akcie
`Contract::actions()` — pridať `PrepareAnnualAdvanceBulk`.

### Task 1.7 — 4.1.7 Odoslanie zálohového predpisu nájomcovi e-mailom

**Priorita:** Medium · **Odhad:** 2h (120 min)

## Akceptačné kritériá
- [ ] V detaile ročného zálohového predpisu je tlačidlo „Odoslať e-mailom".
- [ ] Klik na tlačidlo pošle nájomcovi e-mail s PDF prílohou na e-mail evidovaný u zákazníka.
- [ ] E-mail obsahuje sprievodný text s prehľadom 12 splátok a platobnými údajmi (banka, IBAN, konštantný symbol 0308, VS).
- [ ] Po odoslaní systém uloží dátum a čas odoslania.

---

## Cieľ
Mailable `AnnualAdvanceMail` (pattern z existujúceho `InvoiceMail`) + sprievodný e-mail view + integrácia do `InvoiceController::sendEmail()` so switchom podľa `isAnnualAdvance()`. PDF sa pripojí ako príloha (na rozdiel od `InvoiceMail`, kde je attach komentovaný). `sent_at` tracking.

## Technický popis
### Mailable
`app/Mail/AnnualAdvanceMail.php` (pattern z `InvoiceMail.php`):
- Subject: `__('Ročný zálohový predpis :number', ['number' => $invoice->variable_symbol])`.
- View: `email.annual_advance`.
- PDF attach: `$mail->attach(public_path($invoice->pdfPublic()), ['as' => $invoice->variable_symbol.'.pdf']);`.

### View
`resources/views/email/annual_advance.blade.php`:
- Pozdrav, popis: „V prílohe nájdete ročný zálohový predpis pre rok {{ $year }}."
- Skrátený splátkový kalendár (tabuľka 12 riadkov: mesiac, VS, splatnosť, suma).
- Platobné údaje: banka, IBAN, konštantný symbol 0308, VS.

### Controller
`app/Http/Controllers/v1/InvoiceController::sendEmail()`:
```php
if ($invoice->isAnnualAdvance()) {
    Mail::to($invoice->email)->send(new AnnualAdvanceMail($invoice));
} else {
    Mail::to($invoice->email)->send(new InvoiceMail($invoice));
}
$invoice->update(['sent_at' => now()]);
```

### Nova UI
`app/Nova/Invoice/ButtonsCard.php` — tlačidlo „Odoslať e-mailom" musí byť dostupné aj pre `type = '4'`.

### Task 1.8 — 4.1.8 Číselný rad ZP a evidencia variabilných symbolov zmlúv

**Priorita:** High · **Odhad:** 1h (60 min)

## Akceptačné kritériá
- [ ] Systém má samostatný číselný rad pre ročné zálohové predpisy vo formáte ZP[YYYY]-[NNNN] (napr. ZP2026-0001).
- [ ] Každá zmluva má 3-ciferný variabilný symbol (jednoznačné číslo zmluvy).
- [ ] Pri vytvorení novej zmluvy bez VS systém priradí najnižšie voľné číslo.
- [ ] Pri importe historických zmlúv si admin môže ručne ponechať pôvodný VS, ktorý nájomca pozná desiatky rokov.
- [ ] VS musí byť unikátne v rámci firmy.

---

## Cieľ
Pridať pole `variable_symbol` na `contracts` s helperom `nextAvailableVariableSymbol()` (najnižšie voľné 3-ciferné číslo, soft-deleted nepočítať) a auto-priradením cez `ContractObserver::saving()`. Vytvoriť default `InvoicePattern` pre `ANNUAL_ADVANCE` s formátom `ZP[[year]]-[4[number]]`. Master Invoice použije ZP-pattern, splátky používajú 3-ciferný VS zmluvy pre platby z banky.

## Technický popis
### Migrácia
`database/migrations/<dnes>_add_variable_symbol_to_contracts.php`:
```php
Schema::table('contracts', function (Blueprint $table) {
    $table->string('variable_symbol', 10)->nullable()->after('name');
    $table->index('variable_symbol');
});
```

### Model
`app/Models/Contract.php`:
- `$fillable += ['variable_symbol']`.
- Statický helper `Contract::nextAvailableVariableSymbol(string $companyId): string`:
  - Hľadá najnižšie voľné 3-ciferné číslo (`001`..`999`) pre danú company cez `customers->company_id`.
  - Soft-deleted zmluvy nepočítať do obsadených.

### Observer
`app/Observers/ContractObserver::saving()` — ak `variable_symbol` je prázdne, doplniť `Contract::nextAvailableVariableSymbol($companyId)`.

### Nova
`app/Nova/Contract.php` — `Text::make('Variabilný symbol', 'variable_symbol')` s helpom „3-ciferný, prázdne = automaticky priradené".

### Seeder
`database/seeders/AnnualAdvanceInvoicePatternSeeder.php`:
```php
InvoicePattern::create([
    'company_id' => $companyId,
    'title' => 'Ročný zálohový predpis',
    'type' => InvoiceType::ANNUAL_ADVANCE->value,
    'pattern' => 'ZP[[year]]-[4[number]]',
    'number' => 1,
    // address, email, phone, bank — kópia z existujúceho pattern company
]);
```

### Builder
`AnnualAdvanceBuilder::persist()`:
- Master Invoice: VS = `invoice_pattern->getNumber()` → ZP2026-0001.
- Each Installment: VS = `$contract->variable_symbol` → 3-ciferný VS pre platby z banky.

### Edge cases
- Konflikt VS pri importe historického → ValidationException.
- Soft-deleted zmluvy: VS sa môže reusnúť.

### Task 1.9 — 4.1.9 Testovanie a overenie ročného zálohového predpisu

**Priorita:** Medium · **Odhad:** 3.5h (210 min)

## Akceptačné kritériá
- [ ] Pest test sada pokrýva všetky scenáre DNR 4.1.3 (Scenár 1—5).
- [ ] Test prejde pre zmluvu od 1. 1. (12 splátok) aj zmluvu od 1. 9. (4 splátky).
- [ ] Test overí, že zmena ceny počas roka nemení už pripravený predpis (DNR Scenár 3).
- [ ] Test overí, že predčasné ukončenie nezruší ani neupraví existujúci predpis (Scenár 5).
- [ ] Test overí konštantný symbol 0308 a haliérové zaokrúhlenie poslednej splátky.
- [ ] Test overí autorizáciu Nova akcií per rola (Accountant/Manager/Admin/Developer/SuperAdmin).

---

## Cieľ
Pest feature/unit testy pre `AnnualAdvanceBuilder`, Nova akcie a PDF generátor. Pokrytie scenárov DNR 4.1.3 (1-5), edge cases (zmena ceny počas roka, predčasné ukončenie), autorizácia per rola (existujúca konvencia `tests/Feature/NovaApi/{Resource}/{Role}Test.php`).

## Technický popis
### Súbory
1. `tests/Feature/Invoice/AnnualAdvanceBuilderTest.php`:
   - `test_creates_12_installments_for_full_year_contract`.
   - `test_creates_partial_installments_for_mid_year_contract` (od 1. 9. → 4 splátky).
   - `test_keeps_original_when_price_changes_during_year` (Scenár 3).
   - `test_premature_end_does_not_alter_existing_schedule` (Scenár 5).
   - `test_rounding_cents_handled_by_last_installment`.
   - `test_constant_symbol_is_0308`.

2. `tests/Feature/Nova/PrepareAnnualAdvanceActionTest.php`:
   - Per rola (AccountantTest, ManagerTest, AdminTest, DeveloperTest, SuperAdminTest) — autorizácia.

3. `tests/Feature/Invoice/AnnualAdvancePdfTest.php`:
   - `test_pdf_groups_items_by_premise`.
   - `test_pdf_contains_12_installment_rows`.
   - Assert cez `$invoice->pdfExists()` po `generateOnePdf()`.

### Spustenie
```bash
./vendor/bin/pest tests/Feature/Invoice/AnnualAdvance*
```

### Coverage cieľ
≥ 80 % na nové service triedy.

---

## TASK LIST 2: 4.2 Automatické párovanie platieb z banky

### Pôvodné znenie DNR

> ROZŠÍRENIE Č. 2 — AUTOMATICKÉ PÁROVANIE PLATIEB Z BANKY (DNR sekcia 4.2)
>
> ** 4.2.1 Biznisový účel **
> Klient dostáva od Tatra banky mailové notifikácie pri každom pohybe na účte. Systém raz denne načíta nové notifikácie z vyhradenej mailovej schránky, prečíta z nich sumu, variabilný symbol a dátum platby, a automaticky priradí kreditné platby k jednotlivým mesačným splátkam zálohových predpisov.
>
> ** 4.2.2 Zásadné rozhodnutia **
> • Banka: Tatra banka, Slovakia.
> • Mailová schránka: WAME systémová — klient nepotrebuje zriaďovať žiadnu schránku ani podúčet. WAME priradí klientovi unikátnu e-mailovú adresu, ktorú si klient nastaví v internetbankingu ako cieľ notifikácií.
> • Typy platieb: Iba kredity (prichádzajúce platby). Debety (odchádzajúce platby) systém ignoruje.
> • Variabilný symbol: Každá zmluva má unikátne 3-ciferné VS (= číslo zmluvy), preto VS jednoznačne identifikuje zmluvu. (v1.2)
> • Priraďovacie pravidlo: Systém vždy páruje platbu s najstaršou nespárovanou splátkou daného variabilného symbolu, bez ohľadu na to, či zodpovedá aktuálnemu mesiacu. Príklad: ak nájomca v marci nezaplatí a v apríli pošle platbu, spáruje sa s marcovou splátkou. (v1.2)
> • Duplicitná alebo vyššia platba: Druhá platba v rovnakej výške alebo platba vyššia ako splátka sa eviduje ako preplatok a automaticky sa použije na ďalšiu najstaršiu nespárovanú splátku. (v1.2)
> • Čiastočná platba: Eviduje sa ako čiastočná úhrada. Splátka zostáva v stave „neuhradená v plnej sume".
> • Platba pokrývajúca viac splátok naraz: Ak nájomca pošle jednou platbou sumu zodpovedajúcu viacerým splátkam (napr. 1 000 € = 2× 500 €), spáruje sa s najstaršou splátkou a zvyšok ostane ako preplatok. Admin platbu manuálne rozdelí — pôvodnú zníži na sumu prvej splátky a pridá manuálnu platbu pre druhú splátku. (v1.2)
> • Nerozpoznaná platba: Platba s nenalezeným VS → zaradená do zoznamu „Nespárované platby". Admin ju manuálne priradí. Bez automatických notifikácií.
> • Frekvencia spracovania: Raz denne (v nočných hodinách).
> • Počiatočný stav pri spustení systému: Pre každú zmluvu admin vytvorí jednu fiktívnu úvodnú faktúru v sume doteraz zaplatených platieb (saldo k dátumu spustenia) a k nej manuálne pridá uhrádzajúcu platbu v rovnakej sume. Týmto sa stav účtu nájomcu vyrovná a od daného dátumu systém pokračuje štandardne. (v1.2)
>
> ** 4.2.3 Postup párovania **
> 18. Systém raz denne načíta všetky nové e-maily zo systémovej schránky.
> 19. Pre každý e-mail: overí odosielateľa (Tatra banka).
> 20. Prečíta sumu, variabilný symbol, dátum pripísania a smer platby. Ak je smer = debet → preskočí.
> 21. Pre kredit: nájde zmluvu s daným VS. Ak nenájde → zaradí do „Nespárované platby", platba sa neeviduje.
> 22. Ak nájde: spáruje platbu s najstaršou nespárovanou splátkou danej zmluvy. Vytvorí záznam o platbe a systém automaticky prepočíta stav splátky (neuhradená → čiastočne → uhradená → preplatok). Ak je platba vyššia, prebytok sa použije na ďalšiu najstaršiu nespárovanú splátku. (v1.2)
>
> ** 4.2.4 Práca admina **
> • Zoznam „Bmail importy" — chronologický prehľad všetkých prichádzajúcich notifikácií s filtrom podľa stavu (spárované / nespárované / duplicita / ignorované debety).
> • Zoznam „Nespárované platby" — rýchly prehľad platieb, ktoré vyžadujú manuálny zásah. Akcia „Priradiť k zmluve" umožní adminovi vybrať zmluvu a evidovať platbu ručne.
> • Detail zmluvy zobrazuje históriu platieb — chronologický zoznam automatických aj manuálnych platieb s väzbou na pôvodný e-mail.
> • Úprava platby — admin môže existujúcu platbu upraviť (zmeniť sumu) alebo manuálne pridať novú. Slúži najmä na rozdelenie jednej veľkej platby medzi viac splátok pri nájomcoch, ktorí platia naraz za viac mesiacov. (v1.2)
>
> ** Edge-case — platba s historickým VS **
> Môže nastať situácia, kedy príde platba s variabilným symbolom, ktorý existoval v minulosti, no zmluva už nie je aktívna (napr. odsťahovaný nájomca). Takáto platba zostane v stave „Nespárovaná" a vyžaduje manuálne rozhodnutie admina. Bez ďalšej automatizácie.
>
> ** 4.2.5 Odhad pracnosti **
> Automatické párovanie platieb: 1,5 MD (čítanie e-mailov, rozpoznanie obsahu, priraďovacia logika, prehľady pre admina).

### Task 2.1 — 4.2.1 Evidencia notifikácií z banky v systéme

**Priorita:** High · **Odhad:** 1h (60 min)

## Akceptačné kritériá
- [ ] Každá prichádzajúca notifikácia z Tatra banky sa eviduje ako záznam v systéme s pôvodným obsahom a stavom spracovania.
- [ ] Duplicitné notifikácie (z reštartu cronu) sa nezdvojia.
- [ ] Pri každom zázname je jasné, či ide o pripísanie alebo odpis a aký je výsledok automatického párovania.

---

## Cieľ
Vytvoriť tabuľku `bmail_imports` pre 1-záznam-per-notifikácia. Uchová raw body (pre re-analýzu pri zmene formátu banky), parsed dáta (suma, VS, dátum, smer) a stav spracovania. UNIQUE `email_message_id` je defenzíva proti duplicitným importom pri reštarte cronu.

## Technický popis
### Migrácia
`database/migrations/<dnes>_create_bmail_imports_table.php`:
- `ulid` PK.
- FK `company_id` (cascade).
- `email_message_id` varchar UNIQUE (IMAP Message-ID, prevencia duplicit).
- `email_from` varchar(255), `email_subject` varchar(500), `email_received_at` timestampTz.
- `raw_body` longText (celé telo, na re-analýzu pri zmene formátu).
- `direction` enum (`credit/debit/unknown`) default `unknown`.
- `parsed_amount` decimal(10,2) nullable.
- `parsed_variable_symbol` varchar(20) nullable.
- `parsed_payment_date` date nullable.
- `status` enum (`pending/matched/unmatched/duplicate/ignored_debit/parse_failed`) default `pending`.
- FK `invoice_payment_id` nullable `nullOnDelete`.
- `matcher_note` text nullable.
- `timestampsTz`, `softDeletesTz`.
- Index `['status', 'created_at']`, index `'parsed_variable_symbol'`.

### Task 2.2 — 4.2.2 Prehľad bankových notifikácií a manuálny zásah

**Priorita:** High · **Odhad:** 1.5h (90 min)

## Akceptačné kritériá
- [ ] V admin paneli pribudne sekcia „Bmail importy" s chronologickým prehľadom všetkých notifikácií.
- [ ] Admin si môže filtrovať podľa stavu (spárované, nespárované, duplicita, ignorované debety, parse failed).
- [ ] Pre stav „Nespárované" je dostupná akcia „Priradiť k zmluve", ktorou admin manuálne pridelí platbu.
- [ ] Záznamy sú read-only (okrem priradenia k zmluve); mazanie len pre SuperAdmin.

---

## Cieľ
Eloquent `BmailImport` model + read-only Nova resource s farebnými badge na stav, filter podľa stavu, akcia `AssignBmailToContract` pre manuálne pridelenie nespárovaných platieb. Volá rovnakú alokačnú logiku ako automatický matcher (Task 2.5).

## Technický popis
### Model
`app/Models/BmailImport.php`:
- extends `BaseModel`, `SoftDeletes`.
- Casty: `email_received_at` → datetime; `parsed_amount` → decimal:2; `parsed_payment_date` → date.
- Relations: `company()`, `invoicePayment()`.
- Scopes: `scopeUnmatched`, `scopeFailures` (status IN `[unmatched, parse_failed, duplicate]`).

### Nova resource
`app/Nova/BmailImport.php`:
- `$model = BmailImport::class`.
- Fields: ID, Badge `status` (farby), DateTime `email_received_at`, Text `email_subject`, Currency `parsed_amount`, Text `parsed_variable_symbol`, Date `parsed_payment_date`, BelongsTo `invoicePayment` readonly, Code `raw_body`->json()->onlyOnDetail().
- `authorizeToCreate = false`, `authorizeToUpdate = false`; delete len SuperAdmin.
- `indexQuery`: `company_id = get_company_id()`.

### Filter
`app/Nova/Filters/BmailImportStatusFilter.php` (pattern z `InvoiceStatusFilter`).

### Action
`app/Nova/Actions/AssignBmailToContract.php`:
- `Select` `contract_id` (`Contract::active()` v rámci company).
- `Number` `amount` (predvyplnené z `parsed_amount`).
- `Date` `payment_date` (predvyplnené z `parsed_payment_date`).
- `handle()` volá `PaymentMatcher::assignManual($bmailImport, $contractId, $amount, $paymentDate)`.

### Menu
Pridať do `NovaServiceProvider::mainMenu()` položku „Bmail importy".

### Task 2.3 — 4.2.3 Pripojenie systému na bankovú schránku

**Priorita:** High · **Odhad:** 1h (60 min)

## Akceptačné kritériá
- [ ] Systém sa pripojí na vyhradenú IMAP schránku, na ktorú internetbanking Tatra banky posiela notifikácie.
- [ ] WAME prevádzkuje schránku — klient nepotrebuje zriaďovať podúčet.
- [ ] Konfigurácia (host, prihlasovacie údaje, priečinok) je v `.env` a `config/bmail.php`.
- [ ] Vývojár vie cez tinker overiť spojenie pred ostrým nasadením.

---

## Cieľ
Pridať `webklex/laravel-imap` composer balík, nakonfigurovať IMAP pripojenie cez `.env` premenné a `config/bmail.php`. Schránka je WAME-systémová (klient nepotrebuje nič zriaďovať), klient len nastaví v internetbankingu cieľovú adresu pre notifikácie.

## Technický popis
### Composer balík
```bash
composer require webklex/laravel-imap
```

### .env premenné
```
BMAIL_IMAP_HOST=
BMAIL_IMAP_PORT=993
BMAIL_IMAP_ENCRYPTION=ssl
BMAIL_IMAP_USERNAME=bmail-strecnianska@reality.wame.sk
BMAIL_IMAP_PASSWORD=
BMAIL_IMAP_FOLDER=INBOX
BMAIL_IMAP_VALIDATE_CERT=true
BMAIL_TATRA_FROM_PATTERN=/notifikacie@tatrabanka\.sk/i
BMAIL_DEFAULT_COMPANY_ID=
```

### Config
`config/bmail.php`:
```php
return [
    'tatra_banka_from_pattern' => env('BMAIL_TATRA_FROM_PATTERN', '/notifikacie@tatrabanka\.sk/i'),
    'imap' => [
        'host' => env('BMAIL_IMAP_HOST'),
        'port' => (int) env('BMAIL_IMAP_PORT', 993),
        'encryption' => env('BMAIL_IMAP_ENCRYPTION', 'ssl'),
        'username' => env('BMAIL_IMAP_USERNAME'),
        'password' => env('BMAIL_IMAP_PASSWORD'),
        'folder' => env('BMAIL_IMAP_FOLDER', 'INBOX'),
        'validate_cert' => (bool) env('BMAIL_IMAP_VALIDATE_CERT', true),
    ],
    'default_company_id' => env('BMAIL_DEFAULT_COMPANY_ID'),
];
```

### Publish vendor config
```bash
php artisan vendor:publish --provider="Webklex\IMAP\Providers\LaravelServiceProvider"
```

### Závislosti
- Ops vytvorí schránku `bmail-strecnianska@reality.wame.sk` a heslo doplní do `.env`.

### Task 2.4 — 4.2.4 Rozpoznanie obsahu notifikácie z Tatra banky

**Priorita:** High · **Odhad:** 3h (180 min)

## Akceptačné kritériá
- [ ] Systém z textu notifikácie spoľahlivo extrahuje sumu, variabilný symbol, dátum pripísania a smer pohybu.
- [ ] Debetné notifikácie systém ignoruje (status: ignored_debit).
- [ ] Ak sa nepodarí rozpoznať podstatné polia, notifikácia ide do stavu „parse_failed" pre manuálne riešenie.
- [ ] Variabilný symbol zostáva ako reťazec (zachované úvodné nuly: napr. „007").
- [ ] 100 % vzoriek od klienta prejde testom.

### Závislosť
- Pred začatím vyžiadať reálny vzor notifikácie od klienta (DNR sekcia 8 bod 2, ⏳ prisľúbené). Bez vzorky nemá zmysel písať regex.

---

## Cieľ
Service `TatraBankaParser` extrahuje sumu, VS, dátum a smer cez regex z `raw_body` notifikácie. Debety označí ako `ignored_debit`, kreditné s úplnými dátami ako `pending` (čaká na matcher), inak `parse_failed`. Bez vzoru notifikácie od klienta task nezačínať — regex bez vzorky je hra naslepo.

## Technický popis
### Service
`app/Services/Bmail/TatraBankaParser.php`:
```php
public function parse(BmailImport $import): BmailImport {
    $body = $import->raw_body;
    $direction = match(true) {
        preg_match('/(?:prijat[áa]|kredit|prip[ií]san[áa])/iu', $body) === 1 => 'credit',
        preg_match('/(?:odp[ií]san[áa]|debet|prevod von)/iu', $body) === 1 => 'debit',
        default => 'unknown',
    };
    if (preg_match('/(?:suma|amount)[:\s]+([\d\s]+[.,]\d{2})\s*EUR/iu', $body, $m)) {
        $amount = (float) str_replace([' ', ','], ['', '.'], $m[1]);
    }
    if (preg_match('/(?:VS|variabiln[ýy] symbol)[:\s]+(\d{1,15})/iu', $body, $m)) {
        $vs = $m[1]; // string, leading zeros zachovať
    }
    if (preg_match('/(\d{1,2}\.\d{1,2}\.\d{4})/', $body, $m)) {
        $date = Carbon::createFromFormat('d.m.Y', $m[1]);
    }
    $import->fill([
        'direction' => $direction,
        'parsed_amount' => $amount ?? null,
        'parsed_variable_symbol' => $vs ?? null,
        'parsed_payment_date' => $date ?? null,
        'status' => match(true) {
            $direction === 'debit' => 'ignored_debit',
            $direction === 'credit' && isset($amount, $vs) => 'pending',
            default => 'parse_failed',
        },
    ])->save();
    return $import;
}
```

### Fixtures
- `tests/Fixtures/bmail/tatra_credit_sample.txt`
- `tests/Fixtures/bmail/tatra_debit_sample.txt`
- `tests/Fixtures/bmail/tatra_unparseable.txt`

### Edge cases
- VS s leading zeros (`007`) → string, NIE int.
- HTML multipart → preferovať text/plain; fallback `strip_tags($html)`.
- Zmena formátu zo strany banky → status `parse_failed`, manuálne riešenie.

### Task 2.5 — 4.2.5 Automatické párovanie platieb so splátkami

**Priorita:** High · **Odhad:** 3h (180 min)

## Akceptačné kritériá
- [ ] Kreditná platba s rozpoznaným VS sa automaticky priradí k najstaršej nespárovanej splátke danej zmluvy.
- [ ] Vyššia platba (alebo platba pokrývajúca viac splátok) sa rozdelí postupne: najprv najstaršia, zvyšok ďalšia najstaršia atď.
- [ ] Čiastočná platba mení stav splátky na „čiastočne uhradená", splátka zostáva nespárovaná v plnej sume.
- [ ] Platba s neznámym VS alebo s VS ukončenej zmluvy ide do stavu „Nespárovaná" — bez automatickej notifikácie, admin rieši manuálne.
- [ ] Manuálne pridelenie cez Nova akciu „Priradiť k zmluve" funguje rovnakou alokačnou logikou.

---

## Cieľ
Service `PaymentMatcher` lookne zmluvu podľa VS a v cykle alokuje platbu na najstaršie nespárované splátky kým je remainder > 0. Vyššia platba sa rozdelí naprieč viacerými splátkami, neznámy VS / VS ukončenej zmluvy končí ako `unmatched` pre manuálne riešenie.

## Technický popis
### Service
`app/Services/Bmail/PaymentMatcher.php`:
```php
public function match(BmailImport $import): void {
    if ($import->direction !== 'credit' || $import->status !== 'pending') return;
    $contract = Contract::query()
        ->where('variable_symbol', $import->parsed_variable_symbol)
        ->whereHas('customer', fn ($q) => $q->where('company_id', $import->company_id))
        ->first();
    if (!$contract) {
        $import->update(['status' => 'unmatched', 'matcher_note' => 'Zmluva s VS nenájdená']);
        return;
    }
    $remaining = $import->parsed_amount;
    $payments = [];
    while ($remaining > 0.009) {
        $installment = InvoiceScheduleInstallment::query()
            ->whereHas('invoice', fn ($q) => $q->where('contract_id', $contract->id))
            ->whereIn('status', ['unpaid', 'partially_paid'])
            ->orderBy('due_date')->first();
        if (!$installment) break;
        $allocate = min($remaining, $installment->remaining());
        $payment = InvoicePayment::create([
            'invoice_id' => $installment->invoice_id,
            'installment_id' => $installment->id,
            'variable_symbol' => $import->parsed_variable_symbol,
            'price' => $allocate,
            'payment_date' => $import->parsed_payment_date,
            'manual' => false,
            'user_id' => null,
        ]);
        $payments[] = $payment->id;
        $installment->refresh()->recalculateStatus();
        $remaining -= $allocate;
    }
    // update status: matched / unmatched + multi-installment note
}
public function assignManual(BmailImport $i, string $contractId, float $amount, ?Carbon $date = null): void
```

### Contract relation
`app/Models/Contract.php` — pridať `installments(): HasManyDeep` (Invoice → InvoiceScheduleInstallment).

### Edge cases
- VS ukončenej zmluvy → `unmatched` (manuálne).
- Duplicate Message-ID → UNIQUE constraint, try-catch v command.
- `amount <= 0` → `parse_failed`.
- Platba presahujúca všetky splátky: posledná = `overpay`, zvyšok poznámka, manuálne.

### Task 2.6 — 4.2.6 Denné automatické sťahovanie platieb

**Priorita:** High · **Odhad:** 1h (60 min)

## Akceptačné kritériá
- [ ] Systém raz denne v nočných hodinách (02:30) automaticky stiahne nové notifikácie z bankovej schránky.
- [ ] Proces beží bez zásahu admina; zlyhanie posiela e-mail správcovi.
- [ ] Vývojár vie spustiť proces ručne v dry-run režime (bez označenia mailov ako prečítané) pre overovanie.

---

## Cieľ
Artisan command `bmail:import` orchestrácia: pripojenie na IMAP, fetch UNSEEN, filter podľa odosielateľa (Tatra banka regex), vytvor `BmailImport`, spusti `TatraBankaParser` + `PaymentMatcher`, označ Seen. Idempotentnosť cez UNIQUE `email_message_id`. Schedulovať dailyAt 02:30 cez Kernel.

## Technický popis
### Console command
`app/Console/Commands/ImportBmailNotifications.php`:
```php
protected $signature = 'bmail:import {--dry-run}';
public function handle(TatraBankaParser $parser, PaymentMatcher $matcher): int {
    $client = Client::account('default'); $client->connect();
    $folder = $client->getFolderByPath(config('bmail.imap.folder'));
    $messages = $folder->messages()->unseen()->get();
    foreach ($messages as $message) {
        $msgId = $message->getMessageId()->first();
        if (BmailImport::where('email_message_id', $msgId)->exists()) {
            $message->setFlag(['Seen']); continue;
        }
        if (!preg_match(config('bmail.tatra_banka_from_pattern'), $message->getFrom()[0]->mail)) continue;
        $import = BmailImport::create([
            'company_id' => config('bmail.default_company_id'),
            'email_message_id' => $msgId,
            'email_from' => $message->getFrom()[0]->mail,
            'email_subject' => $message->getSubject(),
            'email_received_at' => $message->getDate(),
            'raw_body' => $message->getTextBody() ?: strip_tags($message->getHTMLBody()),
            'status' => 'pending',
        ]);
        $parser->parse($import);
        $matcher->match($import->refresh());
        if (!$this->option('dry-run')) $message->setFlag(['Seen']);
    }
    return self::SUCCESS;
}
```

### Scheduler
`app/Console/Kernel.php`:
```php
$schedule->command('bmail:import')
    ->dailyAt('02:30')
    ->withoutOverlapping()
    ->onOneServer()
    ->emailOutputOnFailure(config('mail.admin'));
```

### Deploy
- Overiť že `crontab -e` na produkcii má `* * * * * cd /path && php artisan schedule:run >> /dev/null 2>&1`.

### Task 2.7 — 4.2.7 Manuálna úprava a rozdelenie platieb

**Priorita:** Medium · **Odhad:** 1h (60 min)

## Akceptačné kritériá
- [ ] V detaile zmluvy je tab „História platieb" s chronologickým zoznamom všetkých platieb (automatických aj manuálnych) s väzbou na pôvodný e-mail.
- [ ] Admin vie existujúcu platbu upraviť (zmeniť sumu) alebo manuálne pridať novú.
- [ ] V detaile platby je akcia „Rozdeliť", ktorá pôvodnú zníži na sumu prvej splátky a pridá manuálnu platbu so zvyšnou sumou pre druhú splátku.
- [ ] Po každej úprave sa stav príslušných splátok automaticky prepočíta.

---

## Cieľ
Nova action `SplitPayment` v detaile `InvoicePayment` rozdelí jednu platbu na dve (pôvodná zostane na pôvodnej splátke, nová s rozdielom ide na inú splátku) a recalculuje stavy oboch splátok. Tab `História platieb` na zmluve agreguje auto + manual platby s odkazom späť na pôvodný `BmailImport`.

## Technický popis
### Nova action SplitPayment
`app/Nova/Actions/SplitPayment.php`:
- ActionFields: `price` (zostáva na pôvodnej platbe), `installment_id` (cieľová splátka novej platby), `new_price` (vypočíta sa `original - price`).
- Implementácia:
  - Zníži pôvodnú `InvoicePayment::price` na zadanú sumu.
  - Vytvorí novú `InvoicePayment` so zvyšnou sumou napojenú na cieľový installment.
  - Spustí `recalculateStatus()` na obe splátky.

### Update Nova
`app/Nova/InvoicePayment.php` — pridať `actions()` s `SplitPayment`.
`app/Nova/Contract.php` — pridať tab „História platieb" (HasMany cez `payments()`) s referenciou na BmailImport (BelongsTo cez `invoicePayment->bmailImport` ak existuje).

### BmailImport assign
- Akcia `AssignBmailToContract` z Task 2.2 už pokrýva manuálne pridelenie.

### Task 2.8 — 4.2.8 Testovanie a overenie párovania platieb

**Priorita:** Medium · **Odhad:** 0.5h (30 min)

## Akceptačné kritériá
- [ ] Pest testy pokrývajú kompletný flow: import e-mailu → parsing → párovanie.
- [ ] Test prejde pre kreditnú platbu (matched), debetnú (ignored_debit), neznámy VS (unmatched).
- [ ] Test overí, že duplicitné Message-ID sa nezdvojia.
- [ ] Test overí, že VS ukončenej zmluvy ostane v stave „Nespárovaná" (DNR edge-case).

---

## Cieľ
Pest feature testy pre kompletný flow `bmail:import` → `TatraBankaParser` → `PaymentMatcher`. Mock IMAP (Webklex Mock alebo vlastný `ImapClientInterface` cez Mockery), fixtures s reálnymi e-mail vzorkami pre kredit, debet, parse-fail a duplicate Message-ID.

## Technický popis
### Súbory
`tests/Feature/Bmail/ImportFlowTest.php`:
- `test_full_flow_credit_matched` — fixture mail → command → `BmailImport.status = matched` + `InvoicePayment` vytvorená.
- `test_full_flow_debit_ignored`.
- `test_full_flow_unknown_vs_unmatched`.
- `test_duplicate_message_id_skipped`.
- `test_historical_vs_for_terminated_contract_stays_unmatched`.

### Mock IMAP
- `Webklex\IMAP\Mock` alebo vlastný `ImapClientInterface` + Mockery.

### Spustenie
```bash
./vendor/bin/pest tests/Feature/Bmail
```

---

## TASK LIST 3: 4.3 Ročné zúčtovanie služieb

### Pôvodné znenie DNR

> ROZŠÍRENIE Č. 3 — ROČNÉ ZÚČTOVANIE SLUŽIEB (DNR sekcia 4.3)
>
> ** 4.3.1 Biznisový účel **
> Raz ročne (za kalendárny rok január — december) sa vykoná finančné vyrovnanie medzi skutočnými nákladmi na služby (elektrina, voda/stočné, UK a TUV) a zálohami zaplatenými nájomcami počas roka. Výstupom je pre každého nájomcu individuálny PDF doklad „Ročné zúčtovanie" ukazujúci: ročné zálohy (koľko zaplatil), skutočná spotreba (koľko spotreboval), preplatok alebo nedoplatok.
>
> ** 4.3.2 Zásadné rozhodnutia **
> • Obdobie: Vždy kalendárny rok (január — december).
> • Zadávanie celkových nákladov budovy: Manuálne po konci roka — admin zadá celkovú ročnú sumu za elektrinu, vodu/stočné, UK a TUV.
> • Druhy zúčtovaných služieb: Elektrina, voda/stočné, UK a TUV — všetky v jednom zúčtovaní (naraz).
> • Rozlíšenie merania na úrovni priestoru: Energie sa viažu na jednotlivé priestory zmluvy. Položka energie v zmluve nesie fixnú zálohovú sumu per priestor; ak má priestor podružné meradlo, do zúčtovania vstupuje aj skutočná spotreba. (v1.2)
> • Algoritmus pre priestory bez merania: Koeficient = (celkový náklad − suma spotreby meraných priestorov) / celková plocha nemeraných priestorov v m². Individuálna spotreba = koeficient × plocha priestoru.
> • Viaceré priestory na jednej zmluve s rôznym režimom merania: Algoritmus pracuje per priestor, nie per zmluvu. Jeden nájomca môže mať jeden priestor s meradlom a iný bez merania — meraná časť sa pripočíta nájomcovi presne podľa odpočtu, nemeraná časť sa rozpočíta alikvotne podľa m². (v1.2)
> • Priestory bez zmluvy (správca, technické): Áno, existujú. Ich m² sa rátajú do deliteľa pre alikvótny rozpočet. Náklad pripadajúci na takéto priestory nesie družstvo (nikoho nezaťažuje).
> • Vlastná prípojka (napr. vlastný odpočet elektriny): V zmluve nie je položka za elektrinu alebo je s cenou 0 €. Takýto priestor sa vo výpočte elektriny vôbec neobjavuje.
> • Jednotková cena: Vypočíta sa z celkového nákladu delené celkovou spotrebou (za meranú aj nemeranú časť).
> • Predčasne ukončené zmluvy: Pri zmluve, ktorá v roku skončila skôr, systém započíta iba reálne odbehnuté mesiace (alikvotne podľa platnosti zmluvy). (v1.2)
> • Výstupy: Individuálne PDF pre každého nájomcu (na odoslanie) a sumárny prehľad v systéme pre kontrolu adminom pred hromadným odoslaním. (v1.2)
> • Manuálna úprava výsledkov pred schválením: Áno — admin môže pred schválením manuálne prepísať jednotlivé hodnoty (napr. dohodnutá zľava, špeciálny prípad). Pôvodná vypočítaná hodnota a meno admina zostávajú v audit logu. (v1.2)
> • Schvaľovanie: Admin si najprv pozrie sumárny prehľad všetkých nájomcov, prípadne ručne upraví jednotlivé položky a zvolí „Schváliť zúčtovanie". Až potom prebehne hromadná príprava PDF.
> • Oprava jednotlivého výsledku po vygenerovaní: Ak sa po vygenerovaní zúčtovania zistí chyba pri jednom nájomcovi, admin môže ručne upraviť hodnoty pre tohto konkrétneho zákazníka a vygenerovať mu opravené PDF. Ostatné zúčtovania sa neprepočítavajú. Bežne sa neočakáva, ide o ošetrenie výnimočných situácií. (v1.2)
> • Pripravený doklad preplatku/nedoplatku: Systém pripraví len informačný dokument „Ročné zúčtovanie" s číslami. Faktúry alebo dobropisy na vyrovnanie rieši klient mimo systém.
>
> ** 4.3.3 Algoritmus výpočtu (príklad pre elektrinu) **
> Vstupy: celkový ročný náklad budovy za elektrinu = 50 000 €. V budove je 20 priestorov (spolu 1 000 m²), z toho:
> • 5 priestorov s podružným meraním (dynamická položka v zmluve) — 300 m², skutočná spotreba 80 000 kWh.
> • 12 priestorov bez merania (fixná záloha v zmluve) — 550 m², bez údajov o spotrebe.
> • 2 priestory s vlastnou prípojkou — 100 m², vôbec nevstupujú do výpočtu.
> • 1 priestor správcu bez zmluvy — 50 m², vstupuje do deliteľa ale náklad ide na družstvo.
>
> Výpočet:
> 23. Jednotková cena za kWh (pre merané) = (50 000 € / (80 000 kWh + alikvótna časť)) — viď krok 3.
> 24. Zostatok pre nemerané + správca = 50 000 € − náklad pripísaný meraným priestorom.
> 25. Koeficient €/m² pre nemerané = zostatok / (550 + 50) m² = zostatok / 600 m².
> 26. Náklad priestoru napr. 40 m² = 40 × koeficient.
> 27. Preplatok/nedoplatok = zálohy zaplatené za rok − skutočný náklad.
>
> ** Dospresnenie algoritmu v príprave **
> Presný vzorec rozdelenia medzi merané a nemerané priestory (či sa jednotková cena počíta spoločne alebo zvlášť) má viacero možných variantov. Na začiatku prípravy prebehne 60—90 minútový analytický workshop s klientom, kde sa rozhodnutie zafixuje a odsúhlasí.
>
> ** 4.3.4 Scenár použitia **
> 28. Admin v januári 2027 v module „Ročné zúčtovania" vytvorí nové zúčtovanie pre rok 2026.
> 29. Systém predvyplní sumu všetkých platieb a spotreby z meraní za rok 2026.
> 30. Admin zadá celkové ročné náklady budovy (elektrina, voda/stočné, UK a TUV).
> 31. Systém vypočíta individuálne pre každú zmluvu: preplatok / nedoplatok per služba a celkovo.
> 32. Admin vidí sumárnu tabuľku všetkých zmlúv — skontroluje čísla.
> 33. Zvolí „Schváliť" — zúčtovanie prejde z prípravného stavu do schváleného.
> 34. Zvolí „Pripraviť a odoslať PDF hromadne" — pre každú zmluvu vznikne individuálny PDF dokument a odošle sa e-mailom.
> 35. Ak sa po vygenerovaní zistí chyba u konkrétneho nájomcu, admin ručne upraví jeho hodnoty a vygeneruje len jeho opravené PDF; ostatné zúčtovania sa neprepočítavajú. (v1.2)
> 36. Klient (družstvo) prípadné preplatky/nedoplatky vyrovná mimo systém.
>
> ** 4.3.5 Odhad pracnosti **
> Ročné zúčtovanie služieb: 2 MD (kalkulačná logika, sumárny prehľad, formát PDF, hromadné pripravenie a odosielanie).

### Task 3.1 — 4.3.1 Evidencia ročného zúčtovania služieb v systéme

**Priorita:** High · **Odhad:** 2h (120 min)

## Akceptačné kritériá
- [ ] V systéme existuje samostatný modul „Ročné zúčtovania", v ktorom je možné pre konkrétny kalendárny rok zaevidovať celkové ročné náklady budovy (elektrina, voda/stočné, UK, TUV).
- [ ] Pre jeden rok v rámci firmy môže existovať len jedno zúčtovanie.
- [ ] Po schválení sa zúčtovanie zamkne pred ďalšími úpravami; výnimkou je oprava jednotlivého nájomcu.

---

## Cieľ
Dve nové tabuľky: `annual_settlements` (master per rok per company) a `annual_settlement_items` (riadkový detail per zmluva × priestor × typ služby). UNIQUE `(company_id, year)` znemožňuje duplicitné zúčtovanie. Stavy draft → approved → sent riadia povolené úpravy.

## Technický popis
### Migrácia 1
`database/migrations/<dnes>_create_annual_settlements_table.php`:
- `ulid` PK.
- FK `company_id` (cascade).
- `year` unsignedSmallInteger.
- `status` enum (`draft/approved/sent`) default `draft`.
- `total_electricity`, `total_water`, `total_heating`, `total_hot_water` (decimal 12,2 nullable).
- `approved_at` timestampTz nullable.
- FK `approved_by` (`users.id`) nullable nullOnDelete.
- `calculation_metadata` JSON nullable (jednotková cena, koeficient, sumár plôch per service).
- `timestampsTz`, `softDeletesTz`.
- UNIQUE (`company_id`, `year`).

### Migrácia 2
`database/migrations/<dnes>_create_annual_settlement_items_table.php`:
- `ulid` PK.
- FK `annual_settlement_id` (cascade), `contract_id` (cascade), `premise_id` (cascade).
- `service_type` enum (`electricity/water/heating/hot_water`).
- `measurement_mode` enum (`metered/unmetered/own_connection`).
- `area_m2` decimal(8,2) nullable.
- `measured_consumption` decimal(10,3) nullable.
- `months_active` decimal(4,2) default 12 (alikvótne).
- `paid_advance` decimal(10,2) default 0.
- `calculated_cost` decimal(10,2) default 0.
- `final_cost` decimal(10,2) default 0 (admin override).
- `balance` decimal(10,2) default 0.
- `audit_log` JSON nullable.
- `timestampsTz`, `softDeletesTz`.
- Index `[annual_settlement_id, contract_id, service_type]`.

### Task 3.2 — 4.3.2 Štruktúra údajov o vyúčtovaní per zmluva a priestor

**Priorita:** High · **Odhad:** 1h (60 min)

## Akceptačné kritériá
- [ ] Pre každé zúčtovanie systém eviduje detail per zmluva, per priestor a per typ služby.
- [ ] Pre každý item je viditeľná: režim merania, plocha, spotreba (ak je merané), počet odbehnutých mesiacov (alikvotne pre predčasné ukončenie), zaplatená záloha, skutočný náklad, rozdiel (preplatok/nedoplatok).
- [ ] Admin vie pred schválením manuálne prepísať skutočný náklad konkrétneho itemu.

---

## Cieľ
Eloquent modely `AnnualSettlement` + `AnnualSettlementItem` so scope-mi a helper-mi (totalsByService, contractsCount, recalculateBalance). Tri enum-y v `app/Enums/` pre `service_type` / `measurement_mode` / `status`. Mutator `setFinalCostAttribute()` zaznamenáva audit_log a prepočíta balance.

## Technický popis
### Modely
1. `app/Models/AnnualSettlement.php`:
   - Relations: `company()`, `items()`, `approvedBy()`.
   - Scopes: `scopeDraft`, `scopeApproved`, `scopeForYear($year)`.
   - Helper `totalsByService(): array` (sum balance per `service_type`).
   - Helper `contractsCount(): int`.

2. `app/Models/AnnualSettlementItem.php`:
   - Relations: `settlement()`, `contract()`, `premise()`.
   - Mutator `setFinalCostAttribute()` — zaznamenať audit_log + recalculateBalance.
   - Helper `recalculateBalance()`: `balance = paid_advance - final_cost`.

### Enumy
- `app/Enums/SettlementServiceType.php` (electricity/water/heating/hot_water).
- `app/Enums/SettlementMeasurementMode.php` (metered/unmetered/own_connection).
- `app/Enums/SettlementStatus.php` (draft/approved/sent).

### Task 3.3 — 4.3.3 Výpočtový engine ročného zúčtovania (kľúčový bod)

**Priorita:** High · **Odhad:** 5h (300 min)

## Akceptačné kritériá
- [ ] Pre každý typ služby (elektrina, voda/stočné, UK, TUV) systém:
- [ ] Z meraných priestorov (s podružným meradlom) vypočíta skutočný náklad podľa odpočtu × jednotková cena.
- [ ] Pre nemerané priestory vypočíta koeficient €/m² = (celkový náklad − súčet nákladov meraných) / (súčet plôch nemeraných priestorov + plochy priestorov bez zmluvy).
- [ ] Pre priestor s vlastnou prípojkou (položka v zmluve s cenou 0 € alebo bez položky) sa elektrina vôbec nepočíta.
- [ ] Pre predčasne ukončenú zmluvu (valid_to skôr ako 31. 12.) započíta iba reálne odbehnuté mesiace.
- [ ] Výsledok dataset DNR 4.3.3 (50 000 €, 5 meraných + 12 nemeraných + 2 vlastná prípojka + 1 správca) súhlasí s ručným výpočtom v Exceli.
- [ ] Algoritmus pracuje per priestor, nie per zmluvu (nájomca môže mať jeden priestor merané + jeden nemerané).

### Závislosť
- Pred začatím prebehne 60—90 min analytický workshop s klientom (DNR „Dospresnenie algoritmu v príprave"). Výstupy workshopu doplniť do tohto tasku.
- Otvorená otázka: mapping `ContractTemplateItem` → `SettlementServiceType` — pravdepodobne nový stĺpec `service_key` (enum) na `contract_template_items`.

---

## Cieľ
Service `AnnualSettlementCalculator` — hlavná kalkulačná logika podľa DNR 4.3.3. Algoritmus pracuje per priestor (nie per zmluvu), rozlišuje 3 režimy (metered, unmetered, own_connection). Koeficient pre nemerané = (celkový náklad − suma meraných) / plocha nemeraných. Predčasne ukončené zmluvy alikvotne podľa odbehnutých mesiacov. Najnáročnejšia časť projektu — pred začatím prebehne workshop s klientom (DNR „Dospresnenie algoritmu v príprave").

## Technický popis
### Service
`app/Services/Settlement/AnnualSettlementCalculator.php`:
```php
public function compute(): void {
    foreach (SettlementServiceType::cases() as $service) {
        $totalCost = $this->settlement->{'total_' . $service->value};
        if ($totalCost === null) continue;
        $this->computeService($service, $totalCost);
    }
}

private function computeService(SettlementServiceType $service, float $totalCost): void {
    $premises = $this->collectPremisesForService($service);
    $unitPrice = $this->resolveUnitPrice($service, $premises, $totalCost);

    $meteredCost = 0;
    foreach ($premises['metered'] as &$row) {
        $row['cost'] = $row['consumption'] * $unitPrice * $row['months_active'] / 12;
        $meteredCost += $row['cost'];
    }

    $unmeteredTotal = $totalCost - $meteredCost;
    $unmeteredArea = collect($premises['unmetered'])->sum('area_m2');
    $coef = $unmeteredArea > 0 ? $unmeteredTotal / $unmeteredArea : 0;
    foreach ($premises['unmetered'] as &$row) {
        $row['cost'] = $row['area_m2'] * $coef * $row['months_active'] / 12;
    }

    foreach (['metered', 'unmetered'] as $mode) {
        foreach ($premises[$mode] as $row) {
            AnnualSettlementItem::updateOrCreate(
                ['annual_settlement_id' => $this->settlement->id, 'contract_id' => $row['contract_id'],
                 'premise_id' => $row['premise_id'], 'service_type' => $service->value],
                ['measurement_mode' => $mode, 'area_m2' => $row['area_m2'],
                 'measured_consumption' => $row['consumption'] ?? null,
                 'months_active' => $row['months_active'],
                 'paid_advance' => $this->paidAdvanceFor(...),
                 'calculated_cost' => $row['cost'],
                 'final_cost' => $row['cost'],
                 'balance' => $this->paidAdvanceFor(...) - $row['cost']]
            );
        }
    }
    $metadata[$service->value] = ['unit_price' => $unitPrice, 'coefficient' => $coef, ...];
    $this->settlement->update(['calculation_metadata' => $metadata]);
}

private function paidAdvanceFor($contractId, $premiseId, $service): float {
    // Sum InvoicePayment kde installment->invoice->contract = contract,
    // invoice_item->premise = premise, item.template->service_key = $service.
}
```

### Stratégia koeficientu
`app/Services/Settlement/UnmeteredCoefficientStrategy.php` — 2 varianty (workshop rozhodne):
- (a) jednotná cena pre merané + nemerané (jednoduchšie),
- (b) cena meraných z odpočtov, zvyšok rozpočítaný na nemerané (DEFAULT, DNR explicit).

### Edge cases
- Viaceré priestory na jednej zmluve s rôznym režimom → algoritmus per priestor.
- Zaokrúhľovanie: 2 desatinné v `final_cost`, vyššia presnosť v `calculation_metadata`.
- Priestor správcu bez zmluvy: m² v deliteľi, ale `final_cost` ide na firmu (samostatný riadok bez contract_id alebo pole `building_overhead` v metadata).

### Task 3.4 — 4.3.4 Rozhranie pre prípravu, kontrolu a schválenie zúčtovania

**Priorita:** High · **Odhad:** 2h (120 min)

## Akceptačné kritériá
- [ ] Admin v module „Ročné zúčtovania" vytvorí nové zúčtovanie pre rok (napr. 2026).
- [ ] Systém predvyplní zálohy a spotrebu z meraní za daný rok.
- [ ] Admin zadá celkové ročné náklady budovy.
- [ ] Po kliknutí na „Vypočítať" systém spočíta individuálne pre každú zmluvu preplatok / nedoplatok per služba a celkovo.
- [ ] V sumárnej tabuľke admin vidí všetkých nájomcov a vie konkrétny `final_cost` manuálne prepísať.
- [ ] Klikom „Schváliť" zúčtovanie prejde do stavu „approved" — od tej chvíle sú hodnoty zamknuté pre bežné úpravy.

---

## Cieľ
Nova resources pre `AnnualSettlement` a `AnnualSettlementItem` s tromi akciami (Vypočítať, Schváliť, Pripraviť PDF a odoslať). Inline edit `final_cost` ide cez observer ktorý zapíše audit_log. Po `approved` sa edit zakáže cez Policy.

## Technický popis
### Nova resource AnnualSettlement
`app/Nova/AnnualSettlement.php`:
- Fields: ID, Number `year`, Currency `total_electricity/water/heating/hot_water`, Badge `status`, DateTime `approved_at`, BelongsTo `approvedBy`.
- HasMany `items`.
- Actions:
  - „Vypočítať" → spustí `AnnualSettlementCalculator->compute()`.
  - „Schváliť" → status = `approved`, `approved_at` = now, `approved_by` = auth.
  - „Pripraviť PDF a odoslať hromadne" (len pre approved) — viď Task 3.6.

### Nova resource AnnualSettlementItem
`app/Nova/AnnualSettlementItem.php`:
- Read-only s výnimkou `final_cost`.
- Observer `AnnualSettlementItemObserver::updating()` — old/new `final_cost` → audit_log (viď Task 3.7).

### Metric
`app/Nova/Metrics/AnnualSettlementOverviewMetric.php` (Value):
- Celkový preplatok mínus celkový nedoplatok, počet zmlúv s nedoplatkom.

### Authorization
- Po `approved`: úprava `final_cost` zakázaná (Policy `update`), zostáva otvorená iba akcia „Regenerovať jedno PDF" (Task 3.7).

### Task 3.5 — 4.3.5 PDF výstup ročného zúčtovania pre nájomcu

**Priorita:** High · **Odhad:** 3h (180 min)

## Akceptačné kritériá
- [ ] Pre každú zmluvu so záznamami v zúčtovaní systém vie vygenerovať individuálny PDF dokument „Ročné zúčtovanie".
- [ ] PDF obsahuje: zúčtovacie obdobie, identifikáciu zmluvy a nájomcu, tabuľku per typ služby a per priestor (plocha, spotreba, jednotková cena, skutočný náklad, zaplatená záloha, rozdiel).
- [ ] Spodný sumár: celkový preplatok alebo nedoplatok zmluvy.
- [ ] Pätička obsahuje informáciu „Vyrovnanie sa rieši mimo systém".
- [ ] Vizuál konzistentný so vzorom minuloročného vyúčtovania (DNR sekcia 8 bod 4, ✅ dodaný).

---

## Cieľ
Blade view `settlement/annual.blade.php` + service `AnnualSettlementPdfGenerator`. PDF zobrazí per service_type per priestor tabuľku (plocha, spotreba, jednotková cena, skutočný náklad, záloha, rozdiel), na konci sumár. Vizuál konzistentný s minuloročným vyúčtovaním klienta (✅ dodané).

## Technický popis
### Blade view
`resources/views/settlement/annual.blade.php`:
- Hlavička: zúčtovacie obdobie (rok), dátum prípravy, číslo zmluvy, nájomca.
- Tabuľka per `service_type` per priestor:
  ```
  Služba | Priestor | Plocha | Spotreba | Jednotková cena | Skutočný náklad | Záloha | Rozdiel
  ```
- Sumár: celkový preplatok / nedoplatok zmluvy.
- Pätička: kontaktné údaje firmy + „Vyrovnanie sa rieši mimo systém".

### Generator service
`app/Services/Settlement/AnnualSettlementPdfGenerator.php`:
```php
public function generate(Contract $contract, AnnualSettlement $settlement): string {
    $items = AnnualSettlementItem::where([
        'annual_settlement_id' => $settlement->id,
        'contract_id' => $contract->id,
    ])->with('premise')->get();
    $pdf = Pdf::loadView('settlement.annual', compact('contract', 'settlement', 'items'));
    $path = "settlement/{$settlement->year}/{$contract->id}.pdf";
    $pdf->save(storage_path("app/public/{$path}"));
    return $path;
}
```

### CSS
`public/css/settlement.css` (analógia k `invoice.css`).

### Task 3.6 — 4.3.6 Hromadné odoslanie ročných zúčtovaní e-mailom

**Priorita:** Medium · **Odhad:** 1h (60 min)

## Akceptačné kritériá
- [ ] Po schválení zúčtovania admin spustí hromadnú akciu „Pripraviť a odoslať PDF hromadne".
- [ ] Pre každú zmluvu so záznamami systém vygeneruje individuálny PDF a pošle ho e-mailom na e-mail evidovaný u zákazníka.
- [ ] E-mail obsahuje sprievodný text so sumárom (preplatok/nedoplatok).
- [ ] Po úspechu sa stav zúčtovania zmení na „sent".
- [ ] Pri zlyhaní jedného nájomcu sa proces nezruší — akcia hlási počet úspechov a neúspechov.

---

## Cieľ
Mailable `AnnualSettlementMail` (pattern z `InvoiceMail`) + sprievodný e-mail view + Nova action `DispatchAnnualSettlementEmails`. Po schválení iter `groupBy('contract_id')`, per zmluva generuj PDF + pošli mail, na konci nastav `status = sent`. Per-zmluva error handling, akcia hlási počet úspechov a neúspechov.

## Technický popis
### Mailable
`app/Mail/AnnualSettlementMail.php` (pattern z `InvoiceMail.php`):
- Subject: `__('Ročné zúčtovanie :year', ['year' => $settlement->year])`.
- View: `email.annual_settlement`.
- Attach PDF z `AnnualSettlementPdfGenerator`.

### View
`resources/views/email/annual_settlement.blade.php`:
- Pozdrav.
- Sumár (1 riadok): preplatok / nedoplatok.
- „Vyrovnanie sa rieši mimo systém".

### Nova action
`app/Nova/Actions/DispatchAnnualSettlementEmails.php`:
- Iter `settlement->items->groupBy('contract_id')`.
- Per zmluva: `AnnualSettlementPdfGenerator->generate()`, `Mail::send(new AnnualSettlementMail(...))`.
- Po úspechu `settlement->status = 'sent'`.
- Error handling per zmluva (log + zhrnutie v ActionResponse).

### Task 3.7 — 4.3.7 Audit log úprav a oprava jednotlivých zúčtovaní

**Priorita:** Low · **Odhad:** 1h (60 min)

## Akceptačné kritériá
- [ ] Pri každej zmene skutočného nákladu (final_cost) sa zapíše audit záznam: pôvodná hodnota, nová hodnota, autor úpravy, čas, stav zúčtovania v čase úpravy.
- [ ] Aj po schválení (status = approved alebo sent) admin vie pre konkrétneho nájomcu opraviť hodnoty a vygenerovať len jeho opravené PDF — ostatné zúčtovania sa neprepočítavajú.
- [ ] Audit log je viditeľný v detaile zúčtovania pre potreby kontroly.

---

## Cieľ
Observer `AnnualSettlementItemObserver::updating()` pri zmene `final_cost` appendne záznam do JSON `audit_log` (user, čas, old/new, stav settlementu) + prepočíta `balance`. Nova action `RegenerateSinglePdf` dovolí opravu konkrétneho nájomcu aj po `approved`/`sent` (DNR 4.3.4 bod 8 — výnimočné situácie).

## Technický popis
### Observer
`app/Observers/AnnualSettlementItemObserver.php`:
```php
public function updating(AnnualSettlementItem $item): void {
    if (!$item->isDirty('final_cost')) return;
    $log = $item->audit_log ?? [];
    $log[] = [
        'user_id' => auth()->id(),
        'changed_at' => now()->toIso8601String(),
        'old_value' => $item->getOriginal('final_cost'),
        'new_value' => $item->final_cost,
        'settlement_status' => $item->settlement->status,
    ];
    $item->audit_log = $log;
    $item->balance = $item->paid_advance - $item->final_cost;
}
```

### Registrácia
V `app/Providers/AppServiceProvider::boot()` zaregistrovať observer.

### Nova action
`app/Nova/Actions/RegenerateSinglePdf.php`:
- Pre items danej zmluvy spustí `AnnualSettlementPdfGenerator->generate(contract, settlement)`.
- Otvorené aj pre status = `sent` (DNR 4.3.4 bod 8).

### Task 3.8 — 4.3.8 Testovanie a overenie ročného zúčtovania

**Priorita:** Medium · **Odhad:** 1h (60 min)

## Akceptačné kritériá
- [ ] Pest test sada pokrýva všetky scenáre DNR 4.3.4 a edge cases z 4.3.2.
- [ ] Test pre dataset DNR 4.3.3 (50 000 €, 5 meraných + 12 nemeraných + 2 vlastná prípojka + 1 správca) vychádza identicky ako ručný Excel.
- [ ] Test pre predčasne ukončenú zmluvu (valid_to = 31. 7.) započíta `months_active = 7`.
- [ ] Test overí, že priestor s vlastnou prípojkou nie je v items pre danú službu.
- [ ] Test overí zámok `final_cost` po schválení (Authorization).

---

## Cieľ
Pest feature testy pre `AnnualSettlementCalculator` (kanonický dataset DNR 4.3.3 — 50 000 €, 5 meraných + 12 nemeraných + 2 vlastná prípojka + 1 správca) a pre approval flow s autorizáciou. Test sa musí zhodovať s ručným Excel výpočtom dôverným klientovi.

## Technický popis
### Súbory
1. `tests/Feature/Settlement/AnnualSettlementCalculatorTest.php`:
   - `test_metered_unmetered_split_for_electricity` (vstup z DNR 4.3.3).
   - `test_premature_contract_termination_alikvot` (`valid_to=31.7` → `months_active = 7`).
   - `test_own_connection_excluded` (price=0 → nie v items).
   - `test_caretaker_premise_in_denominator_only`.
   - `test_recalculate_balance_after_final_cost_change`.

2. `tests/Feature/Settlement/AnnualSettlementApprovalTest.php`:
   - `test_admin_can_create_compute_approve_send`.
   - `test_final_cost_locked_after_approval` (Authorization).

### Spustenie
```bash
./vendor/bin/pest tests/Feature/Settlement
```

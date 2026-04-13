# models_jpk_v7m_minimal.py
from datetime import date
from decimal import Decimal
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ====================== ENUMY ======================
class CelZlozenia(str):
  PIERWSZE = "1"
  KOREKTA = "2"


class DowodSprzedazy(str):
  RO = "RO"
  WEW = "WEW"
  FP = "FP"


class DowodZakupu(str):
  MK = "MK"
  VAT_RR = "VAT_RR"
  WEW = "WEW"


class Wybor1(int):
  TAK = 1


# ====================== NAGŁÓWEK ======================
class Naglowek(BaseModel):
  model_config = ConfigDict(validate_by_name=True)

  kod_formularza: Literal["JPK_VAT"] = "JPK_VAT"
  kod_systemowy: Literal["JPK_V7M (3)"] = "JPK_V7M (3)"
  wersja_schemy: Literal["1-0E"] = "1-0E"
  wariant_formularza: Literal[3] = 3
  data_wytworzenia_jpk: str = Field(..., description="np. 2026-02-11T10:00:00Z")
  nazwa_systemu: Optional[str] = Field(None, max_length=240)
  cel_zlozenia: Literal["1", "2"]
  kod_urzedu: str
  rok: int = Field(..., ge=2026, le=2090)
  miesiac: int = Field(..., ge=1, le=12)


# ====================== PODMIOT ======================
class OsobaFizyczna(BaseModel):
  model_config = ConfigDict(validate_by_name=True)

  nip: str
  pesel: str # !! do zrobienia
  imie_pierwsze: str
  nazwisko: str
  data_urodzenia: date
  email: str
  telefon: Optional[str] = None


class OsobaNiefizyczna(BaseModel):
  model_config = ConfigDict(validate_by_name=True)

  nip: str
  pelna_nazwa: str
  email: str
  telefon: Optional[str] = None


class Podmiot1(BaseModel):
  model_config = ConfigDict(validate_by_name=True)

  osoba_fizyczna: Optional[OsobaFizyczna] = None
  osoba_niefizyczna: Optional[OsobaNiefizyczna] = None
  rola: Literal["Podatnik"] = "Podatnik"


# ====================== NAGŁÓWEK DEKLARACJI ======================
class DeklaracjaNaglowek(BaseModel):
  """Nagłówek deklaracji VAT-7 zgodny ze schematem XSD"""
  model_config = ConfigDict(validate_by_name=True, populate_by_name=True)

  kod_formularza_dekl: Literal["VAT-7"] = Field("VAT-7", alias="KodFormularzaDekl")
  kod_systemowy: Literal["VAT-7 (23)"] = "VAT-7 (23)"
  kod_podatku: Literal["VAT"] = "VAT"
  rodzaj_zobowiazania: Literal["Z"] = "Z"
  wersja_schemy: Literal["1-0E"] = "1-0E"


# ====================== DEKLARACJA ======================
class Deklaracja(BaseModel):
  """Deklaracja VAT-7 dla JPK_V7M zgodna ze schematem XSD"""
  model_config = ConfigDict(validate_by_name=True)

  naglowek: DeklaracjaNaglowek
  pozycje_szczegolowe: PozycjeSzczegolowe
  pouczenia: Literal[1] = 1


# ====================== EWIDENCJA ======================
class SprzedazWiersz(BaseModel):
  model_config = ConfigDict(validate_by_name=True)

  lp_sprzedazy: int
  TIN: Optional[str] = None
  nr_kontrahenta: str
  nazwa_kontrahenta: str
  dowod_sprzedazy: str
  data_wystawienia: date
  data_sprzedazy: Optional[date] = None
  ksef_numer: str
  typ_dokumentu: Optional[Literal["", "RO", "WEW", "FP"]] = None
  k_10: Optional[Decimal] = None
  k_11: Optional[Decimal] = None
  k_12: Optional[Decimal] = None
  k_13: Optional[Decimal] = None
  k_14: Optional[Decimal] = None
  k_15: Optional[Decimal] = None
  k_16: Optional[Decimal] = None
  k_17: Optional[Decimal] = None
  k_18: Optional[Decimal] = None
  k_19: Optional[Decimal] = None
  k_20: Optional[Decimal] = None
  k_21: Optional[Decimal] = None
  k_22: Optional[Decimal] = None
  k_23: Optional[Decimal] = None
  k_24: Optional[Decimal] = None
  k_25: Optional[Decimal] = None
  k_26: Optional[Decimal] = None
  k_27: Optional[Decimal] = None
  k_28: Optional[Decimal] = None
  k_29: Optional[Decimal] = None
  k_30: Optional[Decimal] = None
  k_31: Optional[Decimal] = None
  k_32: Optional[Decimal] = None
  k_33: Optional[Decimal] = None
  k_34: Optional[Decimal] = None
  k_35: Optional[Decimal] = None
  k_36: Optional[Decimal] = None
  k_360: Optional[Decimal] = None

  # Pola GTU i procedur
  GTU_01: Optional[Literal[1]] = None
  GTU_02: Optional[Literal[1]] = None
  GTU_03: Optional[Literal[1]] = None
  GTU_04: Optional[Literal[1]] = None
  GTU_05: Optional[Literal[1]] = None
  GTU_06: Optional[Literal[1]] = None
  GTU_07: Optional[Literal[1]] = None
  GTU_08: Optional[Literal[1]] = None
  GTU_09: Optional[Literal[1]] = None
  GTU_10: Optional[Literal[1]] = None
  GTU_11: Optional[Literal[1]] = None
  GTU_12: Optional[Literal[1]] = None
  GTU_13: Optional[Literal[1]] = None
  WSTO_EE: Optional[Literal[1]] = None
  IED: Optional[Literal[1]] = None
#  TP: Optional[Literal[1]] = None
  podmiot_powiazany: Optional[bool]=None
  TT_WNT: Optional[Literal[1]] = None
  TT_D: Optional[Literal[1]] = None
  MR_T: Optional[Literal[1]] = None
  MR_UZ: Optional[Literal[1]] = None
  I_42: Optional[Literal[1]] = None
  I_63: Optional[Literal[1]] = None
  B_SPV: Optional[Literal[1]] = None
  B_SPV_DOSTAWA: Optional[Literal[1]] = None
  B_MPV_PROWIZJA: Optional[Literal[1]] = None


class ZakupWiersz(BaseModel):
  model_config = ConfigDict(validate_by_name=True)

  lp_zakupu: int
  TIN: Optional[str] = None
  nr_dostawcy: str
  nazwa_dostawcy: str
  dowod_zakupu: str
  data_zakupu: date
  ksef_numer: str
  k_40: Optional[Decimal] = None
  k_41: Optional[Decimal] = None
  k_42: Optional[Decimal] = None
  k_43: Optional[Decimal] = None
  k_44: Optional[Decimal] = None
  k_45: Optional[Decimal] = None
  k_46: Optional[Decimal] = None
  k_47: Optional[Decimal] = None


class Ewidencja(BaseModel):
  model_config = ConfigDict(validate_by_name=True)

  sprzedaz_wiersze: List[SprzedazWiersz] = Field(default_factory=list)
  sprzedaz_ctrl: Optional[dict] = None
  zakup_wiersze: List[ZakupWiersz] = Field(default_factory=list)
  zakup_ctrl: Optional[dict] = None
  przeniesienie : Decimal = 0
  #imp: Optional[Decimal] = None
  #imp_vat: Optional[Decimal] = None


# ====================== GŁÓWNY JPK ======================
class Jpk(BaseModel):
  model_config = ConfigDict(validate_by_name=True)

  naglowek: Naglowek
  podmiot1: Podmiot1
  deklaracja: Optional[Deklaracja] = None
  ewidencja: Optional[Ewidencja] = None

# ====================== ENUMY ======================
class DowodSprzedazy0(str):
    RO = "RO"
    WEW = "WEW"
    FP = "FP"

class DowodSprzedazy1:
    RO = "RO"
    WEW = "WEW"
    FP = "FP"



# ====================== POZYCJE SZCZEGÓŁOWE DEKLARACJI ======================
class PozycjeSzczegolowe_bak(BaseModel):
  """
  Pozycje szczegółowe deklaracji VAT-7 zgodne ze schematem JPK_V7M (1-0E)
  Wszystkie pola są Optional - wypełniasz tylko te, które występują
  """

  # ========== CZĘŚĆ A.1 - PODSTAWA OPODATKOWANIA I PODATEK NALEŻNY ==========
  # Dostawa towarów oraz świadczenie usług na terytorium kraju - zwolnione
  p_10: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu dostawy towarów oraz świadczenia usług na terytorium kraju, zwolnionych od podatku",
                                  ge=0)

  # Dostawa towarów oraz świadczenie usług poza terytorium kraju
  p_11: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu dostawy towarów oraz świadczenia usług poza terytorium kraju",
                                  ge=0)
  p_12: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu świadczenia usług, o których mowa w art. 100 ust. 1 pkt 4 ustawy",
                                  ge=0)

  # Dostawa towarów oraz świadczenie usług na terytorium kraju - stawka 0%
  p_13: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu dostawy towarów oraz świadczenia usług na terytorium kraju, opodatkowanych stawką 0%",
                                  ge=0)
  p_14: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu dostawy towarów, o której mowa w art. 129 ustawy",
                                  ge=0)

  # Dostawa towarów oraz świadczenie usług na terytorium kraju - stawka 5%
  p_15: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu dostawy towarów oraz świadczenia usług na terytorium kraju, opodatkowanych stawką 5%, oraz korekty dokonanej zgodnie z art. 89a ust. 1 i 4 ustawy",
                                  ge=0)
  p_16: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku należnego z tytułu dostawy towarów oraz świadczenia usług na terytorium kraju, opodatkowanych stawką 5%, oraz korekty dokonanej zgodnie z art. 89a ust. 1 i 4 ustawy")

  # Dostawa towarów oraz świadczenie usług na terytorium kraju - stawka 7% albo 8%
  p_17: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu dostawy towarów oraz świadczenia usług na terytorium kraju, opodatkowanych stawką 7% albo 8%, oraz korekty dokonanej zgodnie z art. 89a ust. 1 i 4 ustawy",
                                  ge=0)
  p_18: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku należnego z tytułu dostawy towarów oraz świadczenia usług na terytorium kraju, opodatkowanych stawką 7% albo 8%, oraz korekty dokonanej zgodnie z art. 89a ust. 1 i 4 ustawy")

  # Dostawa towarów oraz świadczenie usług na terytorium kraju - stawka 22% albo 23%
  p_19: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu dostawy towarów oraz świadczenia usług na terytorium kraju, opodatkowanych stawką 22% albo 23%, oraz korekty dokonanej zgodnie z art. 89a ust. 1 i 4 ustawy",
                                  ge=0)
  p_20: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku należnego z tytułu dostawy towarów oraz świadczenia usług na terytorium kraju, opodatkowanych stawką 22% albo 23%, oraz korekty dokonanej zgodnie z art. 89a ust. 1 i 4 ustawy")

  # Wewnątrzwspólnotowa dostawa towarów
  p_21: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu wewnątrzwspólnotowej dostawy towarów",
                                  ge=0)

  # Eksport towarów
  p_22: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu eksportu towarów",
                                  ge=0)

  # Wewnątrzwspólnotowe nabycie towarów
  p_23: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu wewnątrzwspólnotowego nabycia towarów",
                                  ge=0)
  p_24: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku należnego z tytułu wewnątrzwspólnotowego nabycia towarów")

  # Import towarów rozliczany zgodnie z art. 33a ustawy
  p_25: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu importu towarów rozliczanego zgodnie z art. 33a ustawy",
                                  ge=0)
  p_26: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku należnego z tytułu importu towarów rozliczanego zgodnie z art. 33a ustawy")

  # Import usług (z wyłączeniem usług od podatników VAT od wartości dodanej)
  p_27: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu importu usług, z wyłączeniem usług nabywanych od podatników podatku od wartości dodanej, do których stosuje się art. 28b ustawy",
                                  ge=0)
  p_28: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku należnego z tytułu importu usług, z wyłączeniem usług nabywanych od podatników podatku od wartości dodanej, do których stosuje się art. 28b ustawy")

  # Import usług od podatników podatku od wartości dodanej
  p_29: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu importu usług nabywanych od podatników podatku od wartości dodanej, do których stosuje się art. 28b ustawy",
                                  ge=0)
  p_30: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku należnego z tytułu importu usług nabywanych od podatników podatku od wartości dodanej, do których stosuje się art. 28b ustawy")

  # Dostawa towarów - podatnikiem jest nabywca (art. 17 ust. 1 pkt 5)
  p_31: Optional[Decimal] = Field(None,
                                  description="Wysokość podstawy opodatkowania z tytułu dostawy towarów, dla których podatnikiem jest nabywca zgodnie z art. 17 ust. 1 pkt 5 ustawy",
                                  ge=0)
  p_32: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku należnego z tytułu dostawy towarów, dla których podatnikiem jest nabywca zgodnie z art. 17 ust. 1 pkt 5 ustawy")

  # Podatek od towarów objętych spisem z natury
  p_33: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku należnego od towarów objętych spisem z natury, o którym mowa w art. 14 ust. 5 ustawy",
                                  ge=0)

  # Zwrot odliczonej/zwróconej kwoty na zakup kas rejestrujących
  p_34: Optional[Decimal] = Field(None,
                                  description="Wysokość zwrotu odliczonej lub zwróconej kwoty wydanej na zakup kas rejestrujących, o którym mowa w art. 111 ust. 6 ustawy",
                                  ge=0)

  # Podatek od WNT środków transportu - do wpłaty w terminie art. 103 ust. 3
  p_35: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku należnego od wewnątrzwspólnotowego nabycia środków transportu, wykazana w wysokości podatku należnego z tytułu określonego w P_24, podlegająca wpłacie w terminie, o którym mowa w art. 103 ust. 3, w związku z ust. 4 ustawy",
                                  ge=0)

  # Podatek od WNT towarów - do wpłaty w terminie art. 103 ust. 5a i 5ac
  p_36: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku od wewnątrzwspólnotowego nabycia towarów, o których mowa w art. 103 ust. 5aa ustawy, podlegająca wpłacie w terminach, o których mowa w art. 103 ust. 5a i 5ac ustawy",
                                  ge=0)

  # Podatek od niezwróconej kaucji za opakowania na napoje
  p_360: Optional[Decimal] = Field(None,
                                   description="Wysokość podatku od niezwróconej kaucji pobranej za produkty w opakowaniach na napoje objęte systemem kaucyjnym, podlegająca wpłacie w terminie, o którym mowa w art. 103 ust. 5da ustawy",
                                   ge=0)

  # Łączna wysokość podstawy opodatkowania
  p_37: Optional[Decimal] = Field(None,
                                  description="Łączna wysokość podstawy opodatkowania. Suma kwot z P_10, P_11, P_13, P_15, P_17, P_19, P_21, P_22, P_23, P_25, P_27, P_29, P_31",
                                  ge=0)

  # Łączna wysokość podatku należnego
  p_38: Decimal = Field(...,
                        description="Łączna wysokość podatku należnego. Suma kwot z P_16, P_18, P_20, P_24, P_26, P_28, P_30, P_32, P_33, P_34 pomniejszona o kwotę z P_35, P_36 i P_360")

  # ========== CZĘŚĆ A.2 - PODATEK NALICZONY ==========
  # Nadwyżka podatku naliczonego nad należnym z poprzedniej deklaracji
  p_39: Optional[Decimal] = Field(None,
                                  description="Wysokość nadwyżki podatku naliczonego nad należnym z poprzedniej deklaracji",
                                  ge=0)

  # Nabycie towarów i usług - środki trwałe
  p_40: Optional[Decimal] = Field(None,
                                  description="Wartość netto z tytułu nabycia towarów i usług zaliczanych u podatnika do środków trwałych",
                                  ge=0)
  p_41: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku naliczonego z tytułu nabycia towarów i usług zaliczanych u podatnika do środków trwałych")

  # Nabycie pozostałych towarów i usług
  p_42: Optional[Decimal] = Field(None,
                                  description="Wartość netto z tytułu nabycia pozostałych towarów i usług",
                                  ge=0)
  p_43: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku naliczonego z tytułu nabycia pozostałych towarów i usług")

  # Korekta podatku naliczonego - środki trwałe
  p_44: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku naliczonego z tytułu korekty podatku naliczonego od nabycia towarów i usług zaliczanych u podatnika do środków trwałych")

  # Korekta podatku naliczonego - pozostałe
  p_45: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku naliczonego z tytułu korekty podatku naliczonego od nabycia pozostałych towarów i usług")

  # Korekta podatku naliczonego - art. 89b ust. 1 (zmniejszenie)
  p_46: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku naliczonego z tytułu korekty podatku naliczonego, o której mowa w art. 89b ust. 1 ustawy",
                                  le=0)

  # Korekta podatku naliczonego - art. 89b ust. 4 (zwiększenie)
  p_47: Optional[Decimal] = Field(None,
                                  description="Wysokość podatku naliczonego z tytułu korekty podatku naliczonego, o której mowa w art. 89b ust. 4 ustawy",
                                  ge=0)

  # Łączna wysokość podatku naliczonego do odliczenia
  p_48: Optional[Decimal] = Field(None,
                                  description="Łączna wysokość podatku naliczonego do odliczenia. Suma kwot z P_39, P_41, P_43, P_44, P_45, P_46 i P_47")

  # ========== CZĘŚĆ B - ROZLICZENIE PODATKU ==========
  # Kwota wydana na zakup kas rejestrujących - do odliczenia
  p_49: Optional[Decimal] = Field(None,
                                  description="Kwota wydana na zakup kas rejestrujących, do odliczenia w danym okresie rozliczeniowym pomniejszająca wysokość podatku należnego",
                                  ge=0)

  # Podatek objęty zaniechaniem poboru
  p_50: Optional[Decimal] = Field(None, description="Wysokość podatku objęta zaniechaniem poboru",
                                  ge=0)

  # Kwota do wpłaty do urzędu skarbowego
  p_51: Decimal = Field(...,
                        description="Wysokość podatku podlegająca wpłacie do urzędu skarbowego",
                        ge=0)

  # Kwota wydana na zakup kas rejestrujących - do zwrotu lub przeniesienia
  p_52: Optional[Decimal] = Field(None,
                                  description="Kwota wydana na zakup kas rejestrujących, do odliczenia w danym okresie rozliczeniowym przysługująca do zwrotu w danym okresie rozliczeniowym lub powiększająca wysokość podatku naliczonego do przeniesienia na następny okres rozliczeniowy",
                                  ge=0)

  # Nadwyżka podatku naliczonego nad należnym
  p_53: Optional[Decimal] = Field(None,
                                  description="Wysokość nadwyżki podatku naliczonego nad należnym",
                                  ge=0)

  # ========== CZĘŚĆ C - ZWROT PODATKU ==========
  # Wysokość zwrotu
  p_54: Optional[Decimal] = Field(None,
                                  description="Wysokość nadwyżki podatku naliczonego nad należnym do zwrotu na rachunek wskazany przez podatnika",
                                  ge=0)

  # Wybór terminu zwrotu (tylko jeden z poniższych może być 1)
  p_540: Optional[Literal[1]] = Field(None,
                                      description="Zwrot na rachunek rozliczeniowy podatnika w terminie 15 dni: 1 - tak")
  p_55: Optional[Literal[1]] = Field(None,
                                     description="Zwrot na rachunek VAT podatnika w terminie 25 dni: 1 - tak")
  p_56: Optional[Literal[1]] = Field(None,
                                     description="Zwrot na rachunek rozliczeniowy podatnika w terminie 25 dni (art. 87 ust. 6 ustawy): 1 - tak")
  p_560: Optional[Literal[1]] = Field(None,
                                      description="Zwrot na rachunek rozliczeniowy podatnika w terminie 40 dni: 1 - tak")
  p_58: Optional[Literal[1]] = Field(None,
                                     description="Zwrot na rachunek rozliczeniowy podatnika w terminie 180 dni: 1 - tak")

  # Zaliczenie zwrotu na poczet przyszłych zobowiązań
  p_59: Optional[Literal[1]] = Field(None,
                                     description="Zaliczenie zwrotu podatku na poczet przyszłych zobowiązań podatkowych: 1 - tak")
  p_60: Optional[Decimal] = Field(None,
                                  description="Wysokość zwrotu do zaliczenia na poczet przyszłych zobowiązań podatkowych",
                                  gt=0)
  p_61: Optional[str] = Field(None, description="Rodzaj przyszłego zobowiązania podatkowego",
                              max_length=512)

  # Nadwyżka do przeniesienia na następny okres
  p_62: Optional[Decimal] = Field(None,
                                  description="Wysokość nadwyżki podatku naliczonego nad należnym do przeniesienia na następny okres rozliczeniowy",
                                  ge=0)

  # ========== CZĘŚĆ D - INFORMACJE UZUPEŁNIAJĄCE ==========
  # Wykonywane czynności specjalne
  p_63: Optional[Literal[1]] = Field(None,
                                     description="Podatnik wykonywał w okresie rozliczeniowym czynności, o których mowa w art. 119 ustawy: 1 - tak")
  p_64: Optional[Literal[1]] = Field(None,
                                     description="Podatnik wykonywał w okresie rozliczeniowym czynności, o których mowa w art. 120 ust. 4 lub 5 ustawy: 1 - tak")
  p_65: Optional[Literal[1]] = Field(None,
                                     description="Podatnik wykonywał w okresie rozliczeniowym czynności, o których mowa w art. 122 ustawy: 1 - tak")
  p_66: Optional[Literal[1]] = Field(None,
                                     description="Podatnik wykonywał w okresie rozliczeniowym czynności, o których mowa w art. 136 ustawy: 1 - tak")
  p_660: Optional[Literal[1]] = Field(None,
                                      description="Podatnik ułatwiał w okresie rozliczeniowym dokonanie czynności, o których mowa w art. 109b ust. 4 ustawy: 1 - tak")
  p_67: Optional[Literal[1]] = Field(None,
                                     description="Podatnik korzysta z obniżenia zobowiązania podatkowego, o którym mowa w art. 108d ustawy: 1 - tak")

  # Korekta podstawy opodatkowania i podatku należnego - art. 89a ust. 1
  p_68: Optional[Decimal] = Field(None,
                                  description="Wysokość korekty podstawy opodatkowania, o której mowa w art. 89a ust. 1 ustawy",
                                  le=0)
  p_69: Optional[Decimal] = Field(None,
                                  description="Wysokość korekty podatku należnego, o której mowa w art. 89a ust. 1 ustawy",
                                  le=0)

  # Uzasadnienie korekty
  p_ORDZU: Optional[str] = Field(None, description="Uzasadnienie przyczyn złożenia korekty",
                                 max_length=2048)

  # ====================== WALIDATORY ======================
  @model_validator(mode='after')
  def validate_p_38_calculation(self) -> 'PozycjeSzczegolowe':
    """Walidacja czy P_38 jest sumą odpowiednich pól"""
    if self.p_38 is not None:
      # Suma podatku należnego
      suma_nalezny = sum([
        self.p_16 or Decimal('0'),
        self.p_18 or Decimal('0'),
        self.p_20 or Decimal('0'),
        self.p_24 or Decimal('0'),
        self.p_26 or Decimal('0'),
        self.p_28 or Decimal('0'),
        self.p_30 or Decimal('0'),
        self.p_32 or Decimal('0'),
        self.p_33 or Decimal('0'),
        self.p_34 or Decimal('0')
      ])

      # Suma zmniejszeń
      suma_zmniejszen = sum([
        self.p_35 or Decimal('0'),
        self.p_36 or Decimal('0'),
        self.p_360 or Decimal('0')
      ])

      expected_p_38 = suma_nalezny - suma_zmniejszen

      # Sprawdź czy różnica jest mniejsza niż 0.01 (zaokrąglenia)
      if abs(self.p_38 - expected_p_38) > Decimal('0.01'):
        raise ValueError(
          f"P_38 ({self.p_38}) nie zgadza się z obliczoną wartością ({expected_p_38})")

    return self

  @model_validator(mode='after')
  def validate_p_48_calculation(self) -> 'PozycjeSzczegolowe':
    """Walidacja czy P_48 jest sumą odpowiednich pól"""
    if self.p_48 is not None:
      expected_p_48 = sum([
        self.p_39 or Decimal('0'),
        self.p_41 or Decimal('0'),
        self.p_43 or Decimal('0'),
        self.p_44 or Decimal('0'),
        self.p_45 or Decimal('0'),
        self.p_46 or Decimal('0'),
        self.p_47 or Decimal('0')
      ])

      if abs(self.p_48 - expected_p_48) > Decimal('0.01'):
        raise ValueError(
          f"P_48 ({self.p_48}) nie zgadza się z obliczoną wartością ({expected_p_48})")

    return self

  @model_validator(mode='after')
  def validate_p_51_calculation(self) -> 'PozycjeSzczegolowe':
    """Walidacja poprawności obliczenia P_51"""
    if self.p_38 is not None and self.p_51 is not None:
      p_48 = self.p_48 or Decimal('0')
      p_49 = self.p_49 or Decimal('0')
      p_50 = self.p_50 or Decimal('0')

      roznica = self.p_38 - p_48 - p_49 - p_50

      if roznica > Decimal('0'):
        expected_p_51 = roznica
      else:
        expected_p_51 = Decimal('0')

      if abs(self.p_51 - expected_p_51) > Decimal('0.01'):
        raise ValueError(
          f"P_51 ({self.p_51}) nie zgadza się z obliczoną wartością ({expected_p_51})")

    return self

  @model_validator(mode='after')
  def validate_zwrot_choice(self) -> 'PozycjeSzczegolowe':
    """Walidacja - tylko jeden sposób zwrotu może być wybrany"""
    zwrot_fields = [self.p_540, self.p_55, self.p_56, self.p_560, self.p_58]
    selected = [f for f in zwrot_fields if f == 1]

    if len(selected) > 1:
      raise ValueError(
        "Można wybrać tylko jeden sposób zwrotu podatku (P_540, P_55, P_56, P_560, P_58)")

    return self

  @model_validator(mode='after')
  def validate_p_54_with_zwrot(self) -> 'PozycjeSzczegolowe':
    """Walidacja - jeśli wybrano sposób zwrotu, musi być kwota do zwrotu"""
    zwrot_fields = [self.p_540, self.p_55, self.p_56, self.p_560, self.p_58]
    has_zwrot = any(f == 1 for f in zwrot_fields)

    if has_zwrot and (self.p_54 is None or self.p_54 <= Decimal('0')):
      raise ValueError("Wybrano sposób zwrotu podatku, ale nie podano kwoty zwrotu (P_54)")

    if self.p_54 and self.p_54 > Decimal('0') and not has_zwrot:
      raise ValueError("Podano kwotę zwrotu (P_54), ale nie wybrano sposobu zwrotu")

    return self

  @model_validator(mode='after')
  def validate_p_59_p_60_p_61(self) -> 'PozycjeSzczegolowe':
    """Walidacja grupy pól dotyczących zaliczenia zwrotu"""
    if self.p_59 == 1:
      if self.p_60 is None:
        raise ValueError("Przy wybraniu P_59=1 należy podać kwotę zaliczenia (P_60)")
      if self.p_61 is None:
        raise ValueError("Przy wybraniu P_59=1 należy podać rodzaj zobowiązania (P_61)")
    else:
      if self.p_60 is not None:
        raise ValueError("P_60 można podać tylko gdy P_59=1")
      if self.p_61 is not None:
        raise ValueError("P_61 można podać tylko gdy P_59=1")

    return self

  @model_validator(mode='after')
  def validate_p_62_with_p_53(self) -> 'PozycjeSzczegolowe':
    """Walidacja związku między P_62 a P_53 i P_54"""
    if self.p_62 is not None and self.p_53 is not None:
      expected_p_62 = self.p_53 - (self.p_54 or Decimal('0'))
      if abs(self.p_62 - expected_p_62) > Decimal('0.01'):
        raise ValueError(f"P_62 ({self.p_62}) nie zgadza się z P_53 - P_54 ({expected_p_62})")

    return self

  @model_validator(mode='after')
  def validate_p_68_p_69(self) -> 'PozycjeSzczegolowe':
    """Walidacja korekt art. 89a"""
    if self.p_68 is not None and self.p_68 > Decimal('0'):
      raise ValueError("P_68 może być tylko ujemne lub zero")

    if self.p_69 is not None and self.p_69 > Decimal('0'):
      raise ValueError("P_69 może być tylko ujemne lub zero")

    # Jeśli podano jedno, należy podać oba
    if (self.p_68 is None) != (self.p_69 is None):
      raise ValueError("Należy podać zarówno P_68 jak i P_69, albo żadne")

    return self

  class Config:
    json_schema_extra = {
      "example": {
        "p_10": "1000.00",
        "p_15": "5000.00",
        "p_16": "250.00",
        "p_19": "10000.00",
        "p_20": "2300.00",
        "p_38": "2550.00",
        "p_42": "8000.00",
        "p_43": "1840.00",
        "p_51": "710.00"
      }
    }

class PozycjeSzczegolowe(BaseModel):
  model_config = ConfigDict(validate_by_name=True)

  # CZĘŚĆ A.1 - PODSTAWA OPODATKOWANIA I PODATEK NALEŻNY
  p_10: Optional[Decimal] = Field(None, ge=0)
  p_11: Optional[Decimal] = Field(None, ge=0)
  p_12: Optional[Decimal] = Field(None, ge=0)
  p_13: Optional[Decimal] = Field(None, ge=0)
  p_14: Optional[Decimal] = Field(None, ge=0)
  p_15: Optional[Decimal] = Field(None, ge=0)
  p_16: Optional[Decimal] = None
  p_17: Optional[Decimal] = Field(None, ge=0)
  p_18: Optional[Decimal] = None
  p_19: Optional[Decimal] = Field(None, ge=0)
  p_20: Optional[Decimal] = None
  p_21: Optional[Decimal] = Field(None, ge=0)
  p_22: Optional[Decimal] = Field(None, ge=0)
  p_23: Optional[Decimal] = Field(None, ge=0)
  p_24: Optional[Decimal] = None
  p_25: Optional[Decimal] = Field(None, ge=0)
  p_26: Optional[Decimal] = None
  p_27: Optional[Decimal] = Field(None, ge=0)
  p_28: Optional[Decimal] = None
  p_29: Optional[Decimal] = Field(None, ge=0)
  p_30: Optional[Decimal] = None
  p_31: Optional[Decimal] = Field(None, ge=0)
  p_32: Optional[Decimal] = None
  p_33: Optional[Decimal] = Field(None, ge=0)
  p_34: Optional[Decimal] = Field(None, ge=0)
  p_35: Optional[Decimal] = Field(None, ge=0)
  p_36: Optional[Decimal] = Field(None, ge=0)
  p_360: Optional[Decimal] = Field(None, ge=0)
  p_37: Optional[Decimal] = Field(None, ge=0)
  p_38: Decimal = Field(..., description="Łączna wysokość podatku należnego")

  # CZĘŚĆ A.2 - PODATEK NALICZONY
  p_39: Optional[Decimal] = Field(None, ge=0)
  p_40: Optional[Decimal] = Field(None, ge=0)
  p_41: Optional[Decimal] = None
  p_42: Optional[Decimal] = Field(None, ge=0)
  p_43: Optional[Decimal] = None
  p_44: Optional[Decimal] = None
  p_45: Optional[Decimal] = None
  p_46: Optional[Decimal] = Field(None, le=0)
  p_47: Optional[Decimal] = Field(None, ge=0)
  p_48: Optional[Decimal] = None

  # CZĘŚĆ B - ROZLICZENIE PODATKU
  p_49: Optional[Decimal] = Field(None, ge=0)
  p_50: Optional[Decimal] = Field(None, ge=0)
  p_51: Decimal = Field(..., ge=0)
  p_52: Optional[Decimal] = Field(None, ge=0)
  p_53: Optional[Decimal] = Field(None, ge=0)

  # CZĘŚĆ C - ZWROT PODATKU
  p_54: Optional[Decimal] = Field(None, ge=0)
  p_540: Optional[Literal[1]] = None
  p_55: Optional[Literal[1]] = None
  p_56: Optional[Literal[1]] = None
  p_560: Optional[Literal[1]] = None
  p_58: Optional[Literal[1]] = None
  p_59: Optional[Literal[1]] = None
  p_60: Optional[Decimal] = Field(None, gt=0)
  p_61: Optional[str] = Field(None, max_length=512)
  p_62: Optional[Decimal] = Field(None, ge=0)

  # CZĘŚĆ D - INFORMACJE UZUPEŁNIAJĄCE
  p_63: Optional[Literal[1]] = None
  p_64: Optional[Literal[1]] = None
  p_65: Optional[Literal[1]] = None
  p_66: Optional[Literal[1]] = None
  p_660: Optional[Literal[1]] = None
  p_67: Optional[Literal[1]] = None
  p_68: Optional[Decimal] = Field(None, le=0)
  p_69: Optional[Decimal] = Field(None, le=0)
  p_ORDZU: Optional[str] = Field(None, max_length=2048)

  # Walidatory (skrócone dla czytelności - zachowaj swoje pełne walidatory)
  @model_validator(mode='after')
  def validate_p_38(self) -> 'PozycjeSzczegolowe':
    # Twoja logika walidacji
    return self

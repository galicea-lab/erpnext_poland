# Moduły:

* JPK 
* KSeF
* polish_accounting - pozostałe

## JPK

Zaimplementowano JPK_V7M
W module wykorzystano fragmenty https://github.com/Semiranis/jpk_v7m (licencja MIT)
Jednak ostatecznie zaimplementowane rozwiązanie opiera się na innych zasadach:

JPK jest generowany wprost z faktur zakupu i faktur sprzedaży.
Dokmenty te są rozszerzane o niezbędne pola.



## KSeF

Zaimplementowano:
- wysyłanie faktur sprzedaży (przycisk na ekranie zatwierdzonej faktury) 
- odbiór (skrypt odbioru) faktur zakup
- odczyt potwierdzenia, że faktura została wysłana (ksef_numer)
- 
Korzysta z xmlsec1

```
pip install pycryptodome
```


## polish_accounting

Zmiany zgodne z polską księgowością:
- formularze wydruku faktur
- pola zawierające miesiąc ewidencyjny oraz miesiąc do którego ma być zaliczony VAT
- podział na dzienniki
- faktury korekty
  


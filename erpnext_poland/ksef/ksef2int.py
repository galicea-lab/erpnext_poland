# ksef2int.py


import base64
import time
import requests

from Crypto.Random import get_random_bytes

from .ksef2client.invoice_utils import create_encryption_info, create_send_invoice_request, prepare_invoice_for_sending

from datetime import datetime, timedelta, timezone

from .ksef2client.models import (
  OpenOnlineSessionRequest, FormCode, OpenOnlineSessionResponse,
  InvoiceQueryFilters, InvoiceQueryDateRange, InvoiceQuerySubjectType,
  InvoiceQueryDateType, SessionInvoicesResponse
)
from .ksef2client.client import KSeFClient
from .ksef2client.auth_utils import create_auth_request_xml2
from .ksef2client.signing import sign_auth_request_with_xmlsec as sign_xades2

from .config import settings


def authenticate_with_certificate_ksef2(ksef_client: KSeFClient, certificate_path: str, password: str, nip: str):
    # Funkcja uwierzytelniania certyfikatem w KSeF 2.0.
    try:
        # 1Pobierz challenge
        print("1. Pobieranie challenge...")
        challenge_response = ksef_client.challenge()
        print(f"   Otrzymano challenge: {challenge_response.challenge}")

        # Przygotuj XML do podpisania
        auth_request_xml = create_auth_request_xml2(
            challenge=challenge_response.challenge,
            identifier_type="Nip",
            identifier_value=nip
        )

        # Podpisz XML podpisem XAdES
        print("2. Podpisywanie żądania XML...")
        signed_xml = sign_xades2(auth_request_xml, certificate_path, password)

        # Wyślij podpisany XML
        print("3. Inicjowanie uwierzytelniania podpisem...")
        init_response = ksef_client.auth_by_xades_signature(signed_xml)
        print(f"   Numer referencyjny operacji: {init_response.referenceNumber}")

        temp_auth_token = init_response.authenticationToken.token

        # Sprawdzaj status operacji, aż do uzyskania statusu 200
        print("4. Sprawdzanie statusu operacji (oczekiwanie na kod 200)...")
        while True:
            status_response = ksef_client.auth_status(init_response.referenceNumber, temp_auth_token)
            print(f"Aktualny status: {status_response.status.code} - {status_response.status.description}")
            if status_response.status.code == 200:
                break
            elif status_response.status.code >= 400:
                print(f"Uwierzytelnienie nie powiodło się. Powód: {status_response.status.description}")
                return None

            time.sleep(2)

        # Tokeny dostępowe
        print("5. Uwierzytelnianie zakończone. Pobranie tokenów sesji...")
        tokens = ksef_client.redeem_token(temp_auth_token)

        # Ustaw główny token dostępu w kliencie
        ksef_client.set_access_token(tokens.accessToken.token)
        print("Tokeny pobrane.")

        return tokens

    except requests.exceptions.HTTPError as e:
        print(f"Wystąpił błąd HTTP: {e.response.status_code}")
        print(f"Treść odpowiedzi: {e.response.text}")
        return None
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")
        return None

def get_mf_public_key(ksef_client: KSeFClient, usage: str = "SymmetricKeyEncryption") -> str:
    # Pobiera i konwertuje aktualny klucz publiczny MF.
    try:
        public_keys = ksef_client.get_public_keys()
        for key in public_keys:
          for u in key.usage:
            if usage == u.value:
                der_cert = base64.b64decode(key.certificate)
                return convert_der_to_pem(der_cert)
        raise Exception(f"Nie znaleziono klucza publicznego dla użycia: {usage}")
    except Exception as e:
        raise Exception(f"Błąd pobierania klucza publicznego MF: {e}")

def convert_der_to_pem(der_data: bytes) -> str:
    # Konwertuje certyfikat z formatu DER do PEM.
    pem_data = base64.b64encode(der_data).decode('ascii')
    pem_lines = [f"-----BEGIN CERTIFICATE-----"]
    pem_lines.extend(pem_data[i:i + 64] for i in range(0, len(pem_data), 64))
    pem_lines.append(f"-----END CERTIFICATE-----")
    return "\n".join(pem_lines)

def ksef2_open_online_session(ksef_client: KSeFClient, public_key_pem: str) -> tuple[OpenOnlineSessionResponse, bytes, bytes]:
    #  Otwiera sesję online, wysyła żądanie do KSeF i zwraca odpowiedź serwera   oraz użyty klucz symetryczny i IV.

    symmetric_key = get_random_bytes(32)
    iv = get_random_bytes(16)

    encryption_info = create_encryption_info(symmetric_key, public_key_pem, iv)

    session_request = OpenOnlineSessionRequest(
        formCode=FormCode(systemCode="FA (2)", schemaVersion="1-0E", value="FA"),
        encryption=encryption_info
    )

    # Wywołanie klienta w celu otwarcia sesji
    session_response = ksef_client.online_session_open(session_request)

    # Zwracamy odpowiedź serwera oraz klucz i IV do późniejszego użycia
    return session_response, symmetric_key, iv

def ksef2_send_invoice_in_session(ksef_client: KSeFClient, session_ref: str, invoice_data: bytes, symmetric_key: bytes, iv: bytes):
    # Szyfruje i wysyła fakturę w ramach już otwartej sesji, używając podanego klucza.
     # Używa klucza i IV z otwartej sesji

    # Szyfrowanie faktury z użyciem klucza sesji
    encrypted_content, _, _ = prepare_invoice_for_sending(invoice_data, symmetric_key, iv)

    # Utwórz request - EncryptionInfo nie jest potrzebne, bo jest już w sesji
    send_request = create_send_invoice_request(
        xml_content=invoice_data,
        encrypted_xml_content=encrypted_content,
        encryption_info=None, # Nie jest wymagane przy wysyłce faktury
        offline_mode=False
    )

    return ksef_client.online_session_send_invoice(session_ref, send_request)

### odbiór

# --- FUNKCJE POMOCNICZE  ---

def authenticate_with_certificate_ksef2(ksef_client: KSeFClient, certificate_path: str, password: str, nip: str):
    try:
        print("1. Pobieranie challenge...")
        challenge_response = ksef_client.challenge()
        print(f"   Otrzymano challenge: {challenge_response.challenge}")

        auth_request_xml = create_auth_request_xml2(
            challenge=challenge_response.challenge,
            identifier_type="Nip",
            identifier_value=nip
        )

        print("2. Podpisywanie żądania XML...")
        signed_xml = sign_xades2(auth_request_xml, certificate_path, password)

        print("3. Inicjowanie uwierzytelniania podpisem...")
        init_response = ksef_client.auth_by_xades_signature(signed_xml)
        print(f"   Numer referencyjny operacji: {init_response.referenceNumber}")

        temp_auth_token = init_response.authenticationToken.token

        print("4. Sprawdzanie statusu operacji (oczekiwanie na kod 200)...")
        while True:
            status_response = ksef_client.auth_status(init_response.referenceNumber, temp_auth_token)
            print(f"Aktualny status: {status_response.status.code} - {status_response.status.description}")
            if status_response.status.code == 200:
                break
            elif status_response.status.code >= 400:
                print(f"Uwierzytelnienie nie powiodło się. Powód: {status_response.status.description}")
                return None
            time.sleep(2)

        print("5. Uwierzytelnianie zakończone. Pobranie tokenów sesji...")
        tokens = ksef_client.redeem_token(temp_auth_token)
        ksef_client.set_access_token(tokens.accessToken.token)
        print("Tokeny pobrane.")
        return tokens

    except requests.exceptions.HTTPError as e:
        print(f"Wystąpił błąd HTTP: {e.response.status_code}")
        print(f"Treść odpowiedzi: {e.response.text}")
        return None
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")
        return None


def get_mf_public_key(ksef_client: KSeFClient, usage: str = "SymmetricKeyEncryption") -> str:
    try:
        public_keys = ksef_client.get_public_keys()
        for key in public_keys:
            for u in key.usage:
                if usage == u.value:
                    der_cert = base64.b64decode(key.certificate)
                    return convert_der_to_pem(der_cert)
        raise Exception(f"Nie znaleziono klucza publicznego dla użycia: {usage}")
    except Exception as e:
        raise Exception(f"Błąd pobierania klucza publicznego MF: {e}")


def convert_der_to_pem(der_data: bytes) -> str:
    pem_data = base64.b64encode(der_data).decode('ascii')
    pem_lines = [f"-----BEGIN CERTIFICATE-----"]
    pem_lines.extend(pem_data[i:i + 64] for i in range(0, len(pem_data), 64))
    pem_lines.append(f"-----END CERTIFICATE-----")
    return "\n".join(pem_lines)


def ksef2_open_online_session(ksef_client: KSeFClient, public_key_pem: str) -> tuple[
    OpenOnlineSessionResponse, bytes, bytes]:
    symmetric_key = get_random_bytes(32)
    iv = get_random_bytes(16)
    encryption_info = create_encryption_info(symmetric_key, public_key_pem, iv)
    session_request = OpenOnlineSessionRequest(
        #formCode=FormCode(systemCode="FA (2)", schemaVersion="1-0E", value="FA"),
      formCode=FormCode(systemCode="FA (3)",schemaVersion="1-0E",value="FA"),

    encryption=encryption_info
    )
    session_response = ksef_client.online_session_open(session_request)
    return session_response, symmetric_key, iv


def ksef2_send_invoice_in_session(ksef_client: KSeFClient, session_ref: str, invoice_data: bytes, symmetric_key: bytes,
                                  iv: bytes):
    encrypted_content, _, _ = prepare_invoice_for_sending(invoice_data, symmetric_key, iv)
    send_request = create_send_invoice_request(
        xml_content=invoice_data,
        encrypted_xml_content=encrypted_content,
        encryption_info=None,
        offline_mode=False
    )
    return ksef_client.online_session_send_invoice(session_ref, send_request)


# --- POBIERANIE LISTY I FAKTUR ---

def list_incoming_invoices(ksef_client: KSeFClient, days_back: int = 30):
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)

    query_filters = InvoiceQueryFilters(
        subjectType=InvoiceQuerySubjectType.Subject2,
        dateRange=InvoiceQueryDateRange(
            dateType=InvoiceQueryDateType.Invoicing,
            from_=start_date,
            to=end_date
        )
    )

    try:
        # Pobieranie metadanych (stronicowanie jest tu uproszczone do 1 strony dla czytelności)
        # należy obsłużyć pętlę while response.hasMore:
        response = ksef_client.query_invoices_metadata(query_filters, page_size=100)

        for inv in response.invoices:
            print(f"{str(inv.invoicingDate):<25} | {inv.ksefNumber:<35} | {inv.seller.nip:<15} | {inv.grossAmount}")

        return response.invoices

    except Exception as e:
        print(f"Błąd podczas pobierania listy faktur: {e}")
        return []


def download_invoice_xml(ksef_client: KSeFClient, ksef_number: str, output_dir: str = "."):
    """Pobiera XML faktury i zapisuje na dysku."""
    #ksef = KSeFClient(base_url=settings.ksef2.api_url)
    try:
        # Wymaga dodania metody get_invoice_content w client.py!
        xml_content = ksef_client.get_invoice_content(ksef_number)
        filename = f"{ksef_number}.xml" #os.path.join(output_dir, f"/{ksef_number}.xml")
        with open(filename, "wb") as f:
            f.write(xml_content)
        return filename
    except Exception as e:
        print(f"Błąd pobierania faktury: {e}")
        return None


def ksef2_receive_invoices_test():
  for ident in ['5170359458-20260203-020040A96756-AA',]:
    yield ident

def ksef2_receive_invoices():
    ksef = KSeFClient(base_url=settings.ksef2.api_url)
    tokens = authenticate_with_certificate_ksef2(
        ksef,
        nip=settings.ksef2.nip,
        certificate_path=settings.ksef2.cert_pfx,
        password=settings.ksef2.cert_pass
    )
    if not tokens:
        return ""
    try:
        public_key = get_mf_public_key(ksef, "SymmetricKeyEncryption")
    except Exception as e:
        print(f"   Błąd pobierania klucza: {e}")
        return ""
    session_ref = None
    try:
        session_response, sym_key, iv = ksef2_open_online_session(ksef, public_key)
        session_ref = session_response.referenceNumber
        ilist = list_incoming_invoices(ksef, days_back=30)
        for inv in ilist:
            download_invoice_xml(ksef, ksef_number=inv.ksefNumber)
            yield inv.ksefNumber
    except Exception as e:
        print(f"   Wystąpił błąd podczas wysyłki: {e}")
        return ""
    finally:
        if session_ref:
            ksef.online_session_terminate(session_ref)

###############################################
def ksef2_send_invoice(invoice_data : str, nip: str, certificate_path : str, password: str):
    ksef = KSeFClient(base_url=settings.ksef2.api_url)
    tokens = authenticate_with_certificate_ksef2(
        ksef,
        nip=nip,
        certificate_path=certificate_path,
        password=password
    )
    if not tokens:
        return ""
    try:
        public_key = get_mf_public_key(ksef, "SymmetricKeyEncryption")
    except Exception as e:
        print(f"   Błąd pobierania klucza: {e}")
        return ""
    session_ref = None
    try:
        session_response, sym_key, iv = ksef2_open_online_session(ksef, public_key)
        session_ref = session_response.referenceNumber
        send_response = ksef2_send_invoice_in_session(ksef, session_ref, invoice_data, sym_key, iv)
        return (send_response.referenceNumber, session_ref)
    except Exception as e:
        print(f"   Wystąpił błąd podczas wysyłki: {e}")
        return ("",session_ref)
    finally:
        if session_ref:
            ksef.online_session_terminate(session_ref)


def ksef2_get_nr(token, ksef_reference_nr) ->(SessionInvoicesResponse,str):
  ksef = KSeFClient(base_url=settings.ksef2.api_url)
  if not token:
    tokens = authenticate_with_certificate_ksef2(
      ksef,
      nip=settings.ksef2.nip,
      certificate_path=settings.ksef2.cert_pfx,
      password=settings.ksef2.cert_pass
    )
    if not tokens:
      return None,""
    try:
      public_key = get_mf_public_key(ksef, "SymmetricKeyEncryption")
    except Exception as e:
      print(f"   Błąd pobierania klucza: {e}")
      return None,""
    #session_ref = None
    try:
      #session_response, sym_key, iv = ksef2_open_online_session(ksef, public_key)
      #session_ref = session_response.referenceNumber
      response = ksef.get_session_invoices(ksef_reference_nr) # SessionInvoiceStatusResponse[]
      return response, token
    except Exception as e:
      print(f"   Wystąpił błąd podczas wysyłki: {e}")
      return None,""
    finally:
      pass
    #return None,""
      #if session_ref:
      #  ksef.online_session_terminate(session_ref)


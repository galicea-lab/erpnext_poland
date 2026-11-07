# ksef2.py

import argparse
import base64
import os
import time
import requests

from Crypto.Random import get_random_bytes

from ksef2client.invoice_utils import create_encryption_info, create_send_invoice_request, prepare_invoice_for_sending
from ksef2client.models import OpenOnlineSessionRequest, FormCode, OpenOnlineSessionResponse
from ksef2client.client import KSeFClient
from ksef2client.auth_utils import create_auth_request_xml2
from ksef2client.signing import sign_auth_request_with_xmlsec as sign_xades2

from .config import get_accounting_settings

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
        print("2. Signing the XML request...")
        signed_xml = sign_xades2(auth_request_xml, certificate_path, password)

        # Wyślij podpisany XML
        print("3. Initiating certificate authentication...")
        init_response = ksef_client.auth_by_xades_signature(signed_xml)
        print(f"   Operation reference number: {init_response.referenceNumber}")

        temp_auth_token = init_response.authenticationToken.token

        # Sprawdzaj status operacji, aż do uzyskania statusu 200
        print("4. Checking the operation status (waiting for code 200)...")
        while True:
            status_response = ksef_client.auth_status(init_response.referenceNumber, temp_auth_token)
            print(f"Current status: {status_response.status.code} - {status_response.status.description}")
            if status_response.status.code == 200:
                break
            elif status_response.status.code >= 400:
                print(f"Authentication failed. Reason: {status_response.status.description}")
                return None

            time.sleep(2)

        # Tokeny dostępowe
        print("5. Authentication finished. Fetching session tokens...")
        tokens = ksef_client.redeem_token(temp_auth_token)

        # Ustaw główny token dostępu w kliencie
        ksef_client.set_access_token(tokens.accessToken.token)
        print("Tokens retrieved.")

        return tokens

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
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
        raise Exception(f"No public key found for usage: {usage}")
    except Exception as e:
        raise Exception(f"Error fetching the MF public key: {e}")

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
# ksef2.py

import argparse
import base64
import os
import time
import requests
from datetime import datetime, timedelta, timezone

from Crypto.Random import get_random_bytes

from ksef2client.invoice_utils import create_encryption_info, create_send_invoice_request, prepare_invoice_for_sending
from ksef2client.models import (
    OpenOnlineSessionRequest, FormCode, OpenOnlineSessionResponse,
    InvoiceQueryFilters, InvoiceQueryDateRange, InvoiceQuerySubjectType,
    InvoiceQueryDateType
)
from ksef2client.client import KSeFClient
from ksef2client.auth_utils import create_auth_request_xml2
from ksef2client.signing import sign_auth_request_with_xmlsec as sign_xades2

from .config import get_accounting_settings


# --- FUNKCJE POMOCNICZE (BEZ ZMIAN) ---

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

        print("2. Signing the XML request...")
        signed_xml = sign_xades2(auth_request_xml, certificate_path, password)

        print("3. Initiating certificate authentication...")
        init_response = ksef_client.auth_by_xades_signature(signed_xml)
        print(f"   Operation reference number: {init_response.referenceNumber}")

        temp_auth_token = init_response.authenticationToken.token

        print("4. Checking the operation status (waiting for code 200)...")
        while True:
            status_response = ksef_client.auth_status(init_response.referenceNumber, temp_auth_token)
            print(f"Current status: {status_response.status.code} - {status_response.status.description}")
            if status_response.status.code == 200:
                break
            elif status_response.status.code >= 400:
                print(f"Authentication failed. Reason: {status_response.status.description}")
                return None
            time.sleep(2)

        print("5. Authentication finished. Fetching session tokens...")
        tokens = ksef_client.redeem_token(temp_auth_token)
        ksef_client.set_access_token(tokens.accessToken.token)
        print("Tokens retrieved.")
        return tokens

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def get_mf_public_key(ksef_client: KSeFClient, usage: str = "SymmetricKeyEncryption") -> str:
    try:
        public_keys = ksef_client.get_public_keys()
        for key in public_keys:
            for u in key.usage:
                if usage == u.value:
                    der_cert = base64.b64decode(key.certificate)
                    return convert_der_to_pem(der_cert)
        raise Exception(f"No public key found for usage: {usage}")
    except Exception as e:
        raise Exception(f"Error fetching the MF public key: {e}")


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
        formCode=FormCode(systemCode="FA (2)", schemaVersion="1-0E", value="FA"),
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
    """Pobiera listę faktur zakupowych (Subject2) z ostatnich X dni."""
    print(f"\n--- Fetching incoming invoices (last {days_back} days) ---")

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)


    # Filtrowanie: Subject2 oznacza Nabywcę (faktury u nas jako zakupowe)
    # DateType: Invoicing (data wpłynięcia do KSeF)
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
        # W produkcji należy obsłużyć pętlę while response.hasMore:
        response = ksef_client.query_invoices_metadata(query_filters, page_size=100)

        print(f"Invoices found: {len(response.invoices)}")
        print(f"{'Received':<25} | {'KSeF number':<35} | {'Seller (NIP)':<15} | {'Gross amount'}")
        print("-" * 100)

        for inv in response.invoices:
            print(f"{str(inv.invoicingDate):<25} | {inv.ksefNumber:<35} | {inv.seller.nip:<15} | {inv.grossAmount}")

        return response.invoices

    except Exception as e:
        print(f"Error while fetching the invoice list: {e}")
        return []


def download_invoice_xml(ksef_client: KSeFClient, ksef_number: str, output_dir: str = "."):
    """Pobiera XML faktury i zapisuje na dysku."""
    print(f"\n--- Pobieranie faktury {ksef_number} ---")
    try:
        # Wymaga dodania metody get_invoice_content w client.py!
        xml_content = ksef_client.get_invoice_content(ksef_number)

        filename = os.path.join(output_dir, f"{ksef_number}.xml")
        with open(filename, "wb") as f:
            f.write(xml_content)

        print(f"Success! Invoice saved as: {filename}")
        return filename
    except Exception as e:
        print(f"Error fetching the invoice: {e}")
        return None


###############################################
def test_send_invoice_flow(nip: str, invoice_path: str, certificate_path : str, password: str):
    settings = get_accounting_settings()
    ksef = KSeFClient(base_url=settings.ksef2.api_url)

    print("--- Krok 1: Uwierzytelnianie ---")
    tokens = authenticate_with_certificate_ksef2(
        ksef,
        nip=nip,
        certificate_path=certificate_path,
        password=password
    )
    if not tokens:
        return

    print("\n--- Step 2: Fetching the MF public key ---")
    try:
        public_key = get_mf_public_key(ksef, "SymmetricKeyEncryption")
        print("   Public key fetched successfully.")
    except Exception as e:
        print(f"   Error fetching the key: {e}")
        return

    session_ref = None
    try:
        print("\n--- Step 3: Opening the interactive session ---")
        session_response, sym_key, iv = ksef2_open_online_session(ksef, public_key)
        session_ref = session_response.referenceNumber
        print(f"   Session opened, reference number: {session_ref}")

        print("\n--- Step 4: Sending the invoice ---")
        with open(invoice_path, "rb") as f:
            invoice_data = f.read()

        send_response = ksef2_send_invoice_in_session(ksef, session_ref, invoice_data, sym_key, iv)
        print(f"   Invoice sent, invoice reference number: {send_response.referenceNumber}")

    except Exception as e:
        print(f"   An error occurred while sending: {e}")
    finally:
        if session_ref:
            print("\n--- Step 5: Closing the session ---")
            ksef.online_session_terminate(session_ref)
            print("   The session has been closed.")



def sign_auth_file(ksef_client: KSeFClient, certificate_path: str, password: str, fn : str):
    try:
        xml=open(fn).read()
        # Podpisz XML podpisem XAdES
        print("Signing the XML request...")
        signed_xml = sign_xades2(xml, certificate_path, password)
        xades=open(fn+'.xades','bw+')
        xades.write(signed_xml)
        xades.close()
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    settings = get_accounting_settings()
    parser = argparse.ArgumentParser(description='KSeF 2.0 client test')
    parser.add_argument('cmd', choices=['login', 'send', 'inbox', 'download', 'sign'], help='Operation to perform.')
    parser.add_argument('--nip', help='Taxpayer NIP (required for login/inbox).', default=settings.ksef2.nip)
    parser.add_argument('--file', help='Path to the file (for send).')
    parser.add_argument('--ksef-num', help='KSeF invoice number (for download).')
    parser.add_argument('--days', type=int, default=30, help='How many days back to look for invoices (for inbox).')

    args = parser.parse_args()

    path_pfx = str(os.path.join(os.path.dirname(__file__), settings.ksef2.cert_pfx))

    # Inicjalizacja klienta (wspólna)
    ksef_client = KSeFClient(base_url=settings.ksef2.api_url)

    if args.cmd == 'login':
        authenticate_with_certificate_ksef2(
            ksef_client, nip=args.nip, certificate_path=path_pfx, password=settings.cert_pass
        )

    elif args.cmd == 'send' and args.file:
        # przykład: send --file invoice.xml
        test_send_invoice_flow(args.nip, args.file, certificate_path=path_pfx, password=settings.ksef2.cert_pass)

    elif args.cmd == 'sign' and args.file:
        sign_auth_file(ksef_client,  certificate_path=path_pfx, password=settings.ksef2.cert_pass, fn=args.file)

    elif args.cmd == 'inbox':
        # 1. Logowanie
        if authenticate_with_certificate_ksef2(ksef_client, nip=args.nip, certificate_path=path_pfx,
                                               password=settings.ksef2.cert_pass):
            # 2. Pobranie listy
            list_incoming_invoices(ksef_client, days_back=args.days)
            # 3. Wylogowanie (zamknięcie tokena sesyjnego autoryzacji)
            try:
                ksef_client.revoke_current_session()
            except Exception as e:
                print(e)

    elif args.cmd == 'download' and args.ksef_num:
        # 1. Logowanie
        if authenticate_with_certificate_ksef2(ksef_client, nip=args.nip, certificate_path=path_pfx,
                                               password=settings.ksef2.cert_pass):
            # 2. Pobranie pliku
            download_invoice_xml(ksef_client, args.ksef_num)
            # 3. Wylogowanie
            try:
                ksef_client.revoke_current_session()
            except:
                pass
    else:
        parser.print_help()

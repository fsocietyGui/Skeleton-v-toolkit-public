#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Skeleton V
Public OSINT / Defensive Recon Toolkit
Python 3.11

Установка:
    pip install requests dnspython

Запуск:
    python skeleton.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

try:
    import requests
except ImportError:
    print("[!] Установи requests:")
    print("    python -m pip install requests")
    sys.exit(1)

try:
    import dns.resolver
except ImportError:
    print("[!] Установи dnspython:")
    print("    python -m pip install dnspython")
    sys.exit(1)


VERSION = "2.0.0"
TIMEOUT = 8
REPORT_DIR = Path("reports")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "*/*",
}


# ============================================================
# BANNER
# ============================================================

BANNER = r"""
 ███████╗██╗  ██╗███████╗██╗     ███████╗████████╗ ██████╗ ███╗   ██╗
 ██╔════╝██║ ██╔╝██╔════╝██║     ██╔════╝╚══██╔══╝██╔═══██╗████╗  ██║
 ███████╗█████╔╝ █████╗  ██║     █████╗     ██║   ██║   ██║██╔██╗ ██║
 ╚════██║██╔═██╗ ██╔══╝  ██║     ██╔══╝     ██║   ██║   ██║██║╚██╗██║
 ███████║██║  ██╗███████╗███████╗███████╗   ██║   ╚██████╔╝██║ ╚████║
 ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝
"""


# ============================================================
# UI
# ============================================================

def clear():
    print("\033[2J\033[H", end="")


def banner():
    print(BANNER)
    print("                    S K E L E T O N   V")
    print("                Skeleton-v TOOLKIT")
    print(f"                         v{VERSION}")
    print()


def line():
    print("─" * 72)


def title(text: str):
    print()
    line()
    print(f"  {text}")
    line()


def success(text: str):
    print(f"[+] {text}")


def info(text: str):
    print(f"[*] {text}")


def warning(text: str):
    print(f"[!] {text}")


def error(text: str):
    print(f"[-] {text}")


# ============================================================
# HELPERS
# ============================================================

def clean_domain(value: str) -> str:
    value = value.strip()

    if "://" in value:
        value = urlparse(value).hostname or value

    value = value.split("/")[0]
    value = value.split(":")[0]

    return value.lower().strip(".")


def valid_domain(domain: str) -> bool:
    if len(domain) > 253:
        return False

    pattern = (
        r"^(?=.{1,253}$)"
        r"([a-zA-Z0-9]"
        r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
        r"[a-zA-Z]{2,63}$"
    )

    return bool(re.match(pattern, domain))


def valid_username(username: str) -> bool:
    return bool(
        re.fullmatch(
            r"[A-Za-z0-9_.-]{1,50}",
            username
        )
    )


def save_report(name: str, data):
    REPORT_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d_%H%M%S")

    path = REPORT_DIR / f"{name}_{timestamp}.json"

    report = {
        "tool": "Skeleton V",
        "version": VERSION,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "data": data,
    }

    path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    success(f"Отчёт: {path}")


def request_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


# ============================================================
# CAT HACKER
# ============================================================

def run_cat_hacker():
    """
    Запускает cathacker.exe из:

        папка проекта/
            cathacker/
                cathacker.exe
    """

    exe_path = (
        Path(__file__).resolve().parent
        / "cathacker"
        / "cathacker.exe"
    )

    title("CAT HACKER")

    if not exe_path.is_file():
        error(
            "cathacker.exe не найден."
        )
        print()
        print(f"Ожидаемый путь:")
        print(f"  {exe_path}")
        return

    try:
        subprocess.Popen(
            [str(exe_path)],
            cwd=str(exe_path.parent)
        )

        success(
            "cathacker.exe запущен."
        )

    except OSError as exc:
        error(
            f"Ошибка запуска: {exc}"
        )


# ============================================================
# DNS
# ============================================================

def dns_lookup(domain: str):
    domain = clean_domain(domain)

    title(f"DNS ENUMERATION — {domain}")

    if not valid_domain(domain):
        error("Некорректный домен.")
        return None

    record_types = [
        "A",
        "AAAA",
        "MX",
        "NS",
        "TXT",
        "CNAME",
        "SOA",
        "CAA",
    ]

    result = {
        "domain": domain,
        "records": {},
    }

    resolver = dns.resolver.Resolver()
    resolver.timeout = TIMEOUT
    resolver.lifetime = TIMEOUT

    for record_type in record_types:

        try:
            answers = resolver.resolve(
                domain,
                record_type
            )

            values = [
                answer.to_text()
                for answer in answers
            ]

            if values:
                result["records"][record_type] = values

                print(f"\n[{record_type}]")

                for value in values:
                    print(f"  {value}")

        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
        ):
            pass

        except Exception as exc:
            warning(
                f"{record_type}: {type(exc).__name__}"
            )

    return result


# ============================================================
# DOMAIN RECON
# ============================================================

def domain_recon(domain: str):
    domain = clean_domain(domain)

    title(f"DOMAIN RECON — {domain}")

    if not valid_domain(domain):
        error("Некорректный домен.")
        return None

    result = {
        "domain": domain,
        "ips": [],
        "dns": {},
    }

    try:
        addresses = socket.getaddrinfo(
            domain,
            443,
            proto=socket.IPPROTO_TCP
        )

        ips = sorted({
            item[4][0]
            for item in addresses
        })

        result["ips"] = ips

        print("\n[RESOLVED IP]")

        for ip in ips:
            print(f"  {ip}")

    except socket.gaierror:
        warning("DNS resolution failed.")

    dns_result = dns_lookup(domain)

    if dns_result:
        result["dns"] = dns_result["records"]

    return result


# ============================================================
# IP INTELLIGENCE
# ============================================================

def ip_intel(ip: str):
    title(f"IP INTELLIGENCE — {ip}")

    try:
        socket.inet_pton(
            socket.AF_INET,
            ip
        )
    except OSError:

        try:
            socket.inet_pton(
                socket.AF_INET6,
                ip
            )
        except OSError:
            error("Некорректный IP.")
            return None

    result = {
        "ip": ip,
        "ptr": None,
        "public_info": {},
    }

    try:
        hostname = socket.gethostbyaddr(ip)[0]

        result["ptr"] = hostname

        print("\n[PTR]")
        print(f"  {hostname}")

    except socket.herror:
        warning("PTR не найден.")

    try:
        response = requests.get(
            f"https://ipwho.is/{quote(ip)}",
            headers=HEADERS,
            timeout=TIMEOUT
        )

        if response.ok:
            data = response.json()

            connection = data.get(
                "connection",
                {}
            )

            public_info = {
                "continent": data.get(
                    "continent"
                ),
                "country": data.get(
                    "country"
                ),
                "region": data.get(
                    "region"
                ),
                "city": data.get(
                    "city"
                ),
                "latitude": data.get(
                    "latitude"
                ),
                "longitude": data.get(
                    "longitude"
                ),
                "isp": connection.get(
                    "isp"
                ),
                "organization": connection.get(
                    "org"
                ),
                "asn": connection.get(
                    "asn"
                ),
            }

            result["public_info"] = public_info

            print("\n[PUBLIC IP DATA]")

            for key, value in public_info.items():
                if value is not None:
                    print(
                        f"  {key:<15}: {value}"
                    )

    except requests.RequestException as exc:
        warning(
            f"IP API недоступен: {exc}"
        )

    return result


# ============================================================
# HTTP HEADERS
# ============================================================

def http_headers(url: str):
    title(f"HTTP HEADERS — {url}")

    if not url.startswith(
        ("http://", "https://")
    ):
        url = "https://" + url

    result = {
        "target": url,
        "status": None,
        "final_url": None,
        "headers": {},
    }

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        result["status"] = response.status_code
        result["final_url"] = response.url

        print(
            f"\nHTTP: {response.status_code}"
        )

        print(
            f"Final URL: {response.url}"
        )

        print("\n[HEADERS]")

        for name, value in response.headers.items():
            result["headers"][name] = value
            print(f"{name}: {value}")

        security_headers = {
            "strict-transport-security":
                "HSTS",
            "content-security-policy":
                "CSP",
            "x-content-type-options":
                "X-Content-Type-Options",
            "x-frame-options":
                "X-Frame-Options",
            "referrer-policy":
                "Referrer-Policy",
            "permissions-policy":
                "Permissions-Policy",
        }

        print("\n[SECURITY HEADERS]")

        existing = {
            name.lower()
            for name in response.headers
        }

        for header, name in security_headers.items():

            if header in existing:
                success(
                    f"{name}: PRESENT"
                )
            else:
                warning(
                    f"{name}: NOT DETECTED"
                )

        return result

    except requests.RequestException as exc:
        error(str(exc))
        return None


# ============================================================
# URL ANALYZER
# ============================================================

def url_analyzer(url: str):
    title(f"URL ANALYZER — {url}")

    if not url.startswith(
        ("http://", "https://")
    ):
        url = "https://" + url

    parsed = urlparse(url)

    result = {
        "url": url,
        "scheme": parsed.scheme,
        "hostname": parsed.hostname,
        "port": parsed.port,
        "path": parsed.path,
        "query": parsed.query,
        "fragment": parsed.fragment,
        "warnings": [],
    }

    print(f"\nScheme:   {parsed.scheme}")
    print(f"Hostname: {parsed.hostname}")
    print(
        f"Port:     "
        f"{parsed.port or 'default'}"
    )
    print(
        f"Path:     "
        f"{parsed.path or '/'}"
    )

    if parsed.query:
        print(
            f"Query:    {parsed.query}"
        )

    if parsed.scheme != "https":
        result["warnings"].append(
            "Не используется HTTPS."
        )

    if parsed.username or parsed.password:
        result["warnings"].append(
            "URL содержит userinfo."
        )

    if "@" in url:
        result["warnings"].append(
            "Обнаружен символ @."
        )

    if parsed.hostname:

        if parsed.hostname.startswith(
            "xn--"
        ):
            result["warnings"].append(
                "Домен использует Punycode."
            )

        if parsed.hostname.count(".") > 4:
            result["warnings"].append(
                "Очень много уровней поддоменов."
            )

    if len(url) > 200:
        result["warnings"].append(
            "URL необычно длинный."
        )

    print("\n[ANALYSIS]")

    if result["warnings"]:
        for item in result["warnings"]:
            warning(item)
    else:
        success(
            "Явных подозрительных признаков нет."
        )

    return result


# ============================================================
# USERNAME OSINT
# ============================================================

USERNAME_SITES = {
    "GitHub":
        "https://github.com/{u}",

    "GitLab":
        "https://gitlab.com/{u}",

    "Reddit":
        "https://www.reddit.com/user/{u}/",

    "X":
        "https://x.com/{u}",

    "Twitch":
        "https://www.twitch.tv/{u}",

    "PyPI":
        "https://pypi.org/user/{u}/",

    "Keybase":
        "https://keybase.io/{u}",

    "Medium":
        "https://medium.com/@{u}",

    "Dev.to":
        "https://dev.to/{u}",

    "CodePen":
        "https://codepen.io/{u}",

    "Replit":
        "https://replit.com/@{u}",

    "Docker Hub":
        "https://hub.docker.com/u/{u}",

    "HackerOne":
        "https://hackerone.com/{u}",

    "Bugcrowd":
        "https://bugcrowd.com/{u}",

    "Lichess":
        "https://lichess.org/@/{u}",

    "Chess.com":
        "https://www.chess.com/member/{u}",

    "SoundCloud":
        "https://soundcloud.com/{u}",

    "Patreon":
        "https://www.patreon.com/{u}",

    "Steam":
        "https://steamcommunity.com/id/{u}",
}


def username_osint(username: str):
    title(
        f"USERNAME OSINT — {username}"
    )

    username = username.strip()

    if not valid_username(username):
        error(
            "Недопустимый username."
        )
        return None

    session = request_session()

    results = []

    print()
    info(
        "Проверяются публичные страницы..."
    )

    for site, template in USERNAME_SITES.items():

        encoded = quote(
            username,
            safe=""
        )

        url = template.format(
            u=encoded
        )

        try:
            response = session.get(
                url,
                timeout=TIMEOUT,
                allow_redirects=True
            )

            status = response.status_code

            if status == 200:

                print()
                success(
                    f"{site}: FOUND"
                )

                print(
                    f"    LINK: "
                    f"{response.url}"
                )

                results.append({
                    "site": site,
                    "status": status,
                    "url": response.url,
                    "found": True,
                })

            elif status == 404:

                print(
                    f"[-] {site}: "
                    f"not found"
                )

                results.append({
                    "site": site,
                    "status": status,
                    "url": url,
                    "found": False,
                })

            elif status in (
                401,
                403
            ):

                warning(
                    f"{site}: "
                    f"access restricted "
                    f"(HTTP {status})"
                )

                results.append({
                    "site": site,
                    "status": status,
                    "url": url,
                    "found": None,
                })

            elif status == 429:

                warning(
                    f"{site}: "
                    f"rate limited"
                )

                results.append({
                    "site": site,
                    "status": status,
                    "url": url,
                    "found": None,
                })

            else:

                print(
                    f"[?] {site}: "
                    f"HTTP {status}"
                )

                results.append({
                    "site": site,
                    "status": status,
                    "url": url,
                    "found": None,
                })

        except requests.Timeout:

            warning(
                f"{site}: timeout"
            )

        except requests.RequestException as exc:

            warning(
                f"{site}: "
                f"{type(exc).__name__}"
            )

    found = [
        item
        for item in results
        if item.get("found") is True
    ]

    print()
    line()

    print(
        f" FOUND: {len(found)}"
    )

    line()

    if found:

        print(
            "\nПУБЛИЧНЫЕ ССЫЛКИ:\n"
        )

        for item in found:

            print(
                f"[+] {item['site']}"
            )

            print(
                f"    {item['url']}"
            )

    else:

        print(
            "\n[-] Подтверждённых "
            "публичных страниц не найдено."
        )

    return {
        "username": username,
        "results": results,
        "found": found,
    }


# ============================================================
# EMAIL OSINT
# ============================================================

def email_osint(email: str):
    title(
        f"EMAIL OSINT — {email}"
    )

    email = email.strip().lower()

    match = re.fullmatch(
        r"[^@\s]+@([^@\s]+\.[^@\s]+)",
        email
    )

    if not match:
        error(
            "Некорректный email."
        )
        return None

    domain = match.group(1)

    result = {
        "email": email,
        "domain": domain,
        "mx": [],
    }

    print(
        f"\nDomain: {domain}"
    )

    resolver = dns.resolver.Resolver()

    try:

        answers = resolver.resolve(
            domain,
            "MX"
        )

        print("\n[MX RECORDS]")

        for answer in answers:

            mx = answer.exchange.to_text()
            mx = mx.rstrip(".")

            result["mx"].append(mx)

            print(
                f"  {mx}"
            )

    except Exception:
        warning(
            "MX-записи не найдены."
        )

    print()
    info(
        "Skeleton V не пытается "
        "подключаться к почтовому ящику."
    )

    return result


# ============================================================
# FILE METADATA
# ============================================================

def file_metadata(path: str):
    title(
        f"FILE METADATA — {path}"
    )

    file = Path(path)

    if not file.is_file():
        error(
            "Файл не найден."
        )
        return None

    stat = file.stat()

    result = {
        "file": str(
            file.resolve()
        ),
        "name": file.name,
        "extension": file.suffix,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(
            stat.st_mtime,
            timezone.utc
        ).isoformat(),
    }

    print(
        f"\nName:      {file.name}"
    )

    print(
        f"Extension: "
        f"{file.suffix or 'unknown'}"
    )

    print(
        f"Size:      "
        f"{stat.st_size} bytes"
    )

    print(
        f"Modified:  "
        f"{result['modified']}"
    )

    sha256 = hashlib.sha256()

    with file.open("rb") as handle:

        while chunk := handle.read(
            1024 * 1024
        ):
            sha256.update(chunk)

    result["sha256"] = (
        sha256.hexdigest()
    )

    print(
        f"SHA-256:   "
        f"{result['sha256']}"
    )

    return result


# ============================================================
# SUBDOMAIN ENUMERATION
# ============================================================

def subdomain_enum(domain: str):
    domain = clean_domain(domain)

    title(
        f"SUBDOMAIN ENUMERATION — {domain}"
    )

    if not valid_domain(domain):
        error(
            "Некорректный домен."
        )
        return None

    prefixes = [
        "www",
        "mail",
        "webmail",
        "smtp",
        "imap",
        "pop",
        "ftp",
        "api",
        "dev",
        "test",
        "staging",
        "cdn",
        "static",
        "docs",
        "blog",
        "shop",
        "portal",
        "vpn",
        "status",
    ]

    resolver = dns.resolver.Resolver()
    resolver.timeout = 3
    resolver.lifetime = 3

    found = []

    for prefix in prefixes:

        host = (
            f"{prefix}.{domain}"
        )

        try:

            answers = resolver.resolve(
                host,
                "A"
            )

            ips = [
                answer.to_text()
                for answer in answers
            ]

            success(
                f"{host:<35} "
                f"{', '.join(ips)}"
            )

            found.append({
                "hostname": host,
                "ips": ips,
            })

        except Exception:
            pass

    print()
    info(
        f"Найдено: {len(found)}"
    )

    return {
        "domain": domain,
        "found": found,
    }


# ============================================================
# REPORT
# ============================================================

def report(name: str, data):
    if data is None:
        return

    save_report(
        name,
        data
    )


# ============================================================
# CLI
# ============================================================

def cli_parser():
    parser = argparse.ArgumentParser(
        prog="skeleton",
        description=(
            "Skeleton V — "
            "Public OSINT Toolkit"
        )
    )

    parser.add_argument(
        "--version",
        action="version",
        version=(
            f"Skeleton V {VERSION}"
        )
    )

    sub = parser.add_subparsers(
        dest="command"
    )

    p = sub.add_parser(
        "domain",
        help="Domain reconnaissance"
    )
    p.add_argument(
        "domain"
    )

    p = sub.add_parser(
        "dns",
        help="DNS enumeration"
    )
    p.add_argument(
        "domain"
    )

    p = sub.add_parser(
        "subdomain",
        help="Public DNS subdomain checks"
    )
    p.add_argument(
        "domain"
    )

    p = sub.add_parser(
        "ip",
        help="IP intelligence"
    )
    p.add_argument(
        "ip"
    )

    p = sub.add_parser(
        "headers",
        help="HTTP security headers"
    )
    p.add_argument(
        "url"
    )

    p = sub.add_parser(
        "url",
        help="URL analysis"
    )
    p.add_argument(
        "url"
    )

    p = sub.add_parser(
        "username",
        help="Public username OSINT"
    )
    p.add_argument(
        "username"
    )

    p = sub.add_parser(
        "email",
        help="Email/domain OSINT"
    )
    p.add_argument(
        "email"
    )

    p = sub.add_parser(
        "file",
        help="Local file metadata"
    )
    p.add_argument(
        "path"
    )

    # CAT HACKER
    p = sub.add_parser(
        "cat",
        help="Launch local cathacker.exe"
    )
    p.add_argument(
        "program",
        nargs="?",
        default="hacker.exe"
    )

    return parser


# ============================================================
# INTERACTIVE MENU
# ============================================================

def interactive():
    while True:

        clear()
        banner()

        print("""
╔════════════════════════════════════════════════════════════════╗
║                         SKELETON V                            ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  [1] Domain Recon          [7] Username OSINT                 ║
║  [2] DNS Enumeration       [8] Email OSINT                    ║
║  [3] Subdomain OSINT       [9] File Metadata                  ║
║  [4] IP Intelligence       [10] HTTP Headers                  ║
║  [5] URL Analyzer          [11] Все модули CLI                ║
║  [6] Username Search       [12] Cat Hacker                    ║
║  [0] Выход                                                     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
""")

        choice = input(
            "Skeleton V > "
        ).strip()

        if choice == "1":

            domain = input(
                "Domain > "
            )

            data = domain_recon(
                domain
            )

            report(
                "domain",
                data
            )

        elif choice == "2":

            domain = input(
                "Domain > "
            )

            data = dns_lookup(
                domain
            )

            report(
                "dns",
                data
            )

        elif choice == "3":

            domain = input(
                "Domain > "
            )

            data = subdomain_enum(
                domain
            )

            report(
                "subdomain",
                data
            )

        elif choice == "4":

            ip = input(
                "IP > "
            )

            data = ip_intel(
                ip
            )

            report(
                "ip",
                data
            )

        elif choice == "5":

            url = input(
                "URL > "
            )

            data = url_analyzer(
                url
            )

            report(
                "url",
                data
            )

        elif choice in ("6", "7"):

            username = input(
                "Username > "
            )

            data = username_osint(
                username
            )

            report(
                "username",
                data
            )

        elif choice == "8":

            email = input(
                "Email > "
            )

            data = email_osint(
                email
            )

            report(
                "email",
                data
            )

        elif choice == "9":

            path = input(
                "File > "
            )

            data = file_metadata(
                path
            )

            report(
                "file",
                data
            )

        elif choice == "10":

            url = input(
                "URL > "
            )

            data = http_headers(
                url
            )

            report(
                "headers",
                data
            )

        elif choice == "11":

            print("""
CLI EXAMPLES:

  python skeleton.py domain example.com
  python skeleton.py dns example.com
  python skeleton.py subdomain example.com
  python skeleton.py ip 8.8.8.8
  python skeleton.py username username123
  python skeleton.py email test@example.com
  python skeleton.py url https://example.com
  python skeleton.py headers https://example.com
  python skeleton.py file ./photo.jpg
  python skeleton.py cat hacker.exe
""")

        elif choice == "12":

            run_cat_hacker()

        elif choice == "0":

            print(
                "\n[*] Skeleton V closed."
            )
            break

        else:

            warning(
                "Неизвестная команда."
            )

        input(
            "\nНажми Enter..."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    # Windows CMD / Terminal:
    # красный текст, чёрный фон
    if sys.platform == "win32":
        os.system("color 4")

    parser = cli_parser()

    args = parser.parse_args()

    if not args.command:

        clear()
        banner()
        interactive()

        return

    if args.command == "domain":

        data = domain_recon(
            args.domain
        )

        report(
            "domain",
            data
        )

    elif args.command == "dns":

        data = dns_lookup(
            args.domain
        )

        report(
            "dns",
            data
        )

    elif args.command == "subdomain":

        data = subdomain_enum(
            args.domain
        )

        report(
            "subdomain",
            data
        )

    elif args.command == "ip":

        data = ip_intel(
            args.ip
        )

        report(
            "ip",
            data
        )

    elif args.command == "headers":

        data = http_headers(
            args.url
        )

        report(
            "headers",
            data
        )

    elif args.command == "url":

        data = url_analyzer(
            args.url
        )

        report(
            "url",
            data
        )

    elif args.command == "username":

        data = username_osint(
            args.username
        )

        report(
            "username",
            data
        )

    elif args.command == "email":

        data = email_osint(
            args.email
        )

        report(
            "email",
            data
        )

    elif args.command == "file":

        data = file_metadata(
            args.path
        )

        report(
            "file",
            data
        )

    elif args.command == "cat":

        run_cat_hacker()


if __name__ == "__main__":
    main()
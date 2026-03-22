# vCard (Electronic Business Card)

> **Standard:** [RFC 6350](https://www.rfc-editor.org/rfc/rfc6350) | **Category:** Data Format | **Wireshark filter:** N/A (data format, not wire protocol)

vCard is a text-based data format for representing contact information — names, phone numbers, email addresses, physical addresses, photos, and more. It is the universal interchange format for contacts across platforms: phones share contacts as `.vcf` files, email clients attach vCards to signatures, QR codes encode them for business cards, and sync protocols like CardDAV use vCard as their native data format. vCard is to contacts what iCalendar is to calendar events.

## Format

A vCard is plain text wrapped in `BEGIN:VCARD` / `END:VCARD` delimiters, with one property per line in the form `PROPERTY;PARAMETER=VALUE:property-value`:

```
BEGIN:VCARD
VERSION:4.0
FN:Grace Hopper
N:Hopper;Grace;Murray;Rear Admiral;
TEL;TYPE=work;VALUE=uri:tel:+1-202-555-0143
TEL;TYPE=cell;VALUE=uri:tel:+1-202-555-0187
EMAIL;TYPE=work:grace.hopper@navy.mil
ADR;TYPE=work:;;1200 Navy Pentagon;Washington;DC;20350;USA
ORG:United States Navy
TITLE:Computer Scientist
PHOTO;MEDIATYPE=image/jpeg:https://example.com/hopper.jpg
URL:https://en.wikipedia.org/wiki/Grace_Hopper
BDAY:19061209
NOTE:Pioneer of computer programming. Invented the first compiler.
REV:20240315T120000Z
UID:urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf6
END:VCARD
```

## Example Annotated

```
BEGIN:VCARD                          ← Start delimiter
VERSION:4.0                          ← vCard version (required, must be first after BEGIN)
FN:Grace Hopper                      ← Formatted name (display name, required in v4.0)
N:Hopper;Grace;Murray;Rear Admiral;  ← Structured name: last;first;middle;prefix;suffix
TEL;TYPE=work;VALUE=uri:tel:+1-...   ← Telephone with type parameter
EMAIL;TYPE=work:grace.hopper@...     ← Email with type parameter
ADR;TYPE=work:;;1200 Navy...         ← Structured address: PO;ext;street;city;region;postal;country
ORG:United States Navy               ← Organization name
TITLE:Computer Scientist             ← Job title
PHOTO;MEDIATYPE=image/jpeg:https://  ← Photo as URI (can also be base64-embedded)
URL:https://en.wikipedia.org/...     ← Associated URL
BDAY:19061209                        ← Birthday (YYYYMMDD)
NOTE:Pioneer of computer...          ← Free-text notes
REV:20240315T120000Z                 ← Last revision timestamp
UID:urn:uuid:f81d4fae-...            ← Globally unique identifier
END:VCARD                            ← End delimiter
```

## Key Properties

| Property | Required | Description |
|----------|----------|-------------|
| VERSION | Yes | vCard version (2.1, 3.0, or 4.0) |
| FN | Yes (v3+) | Formatted name — the display name as a single string |
| N | Yes (v3), Optional (v4) | Structured name: last;first;middle;prefix;suffix |
| TEL | No | Telephone number (with TYPE=work, cell, home, fax, voice, etc.) |
| EMAIL | No | Email address |
| ADR | No | Structured address: PO box;extended;street;city;region;postal code;country |
| ORG | No | Organization name (can be multi-level: `ORG:Company;Division;Team`) |
| TITLE | No | Job title or position |
| PHOTO | No | Photo — base64-encoded data or URI reference |
| URL | No | Associated web URL |
| NOTE | No | Free-text notes |
| BDAY | No | Birthday (date or date-time) |
| GEO | No | Geographic coordinates (v4: `geo:37.386,-122.083`; v3: `37.386;-122.083`) |
| TZ | No | Time zone |
| REV | No | Last revision timestamp |
| UID | No | Globally unique identifier for this contact |
| CATEGORIES | No | Comma-separated category tags |
| IMPP | No | Instant messaging handle (e.g., `xmpp:user@example.com`) |
| LOGO | No | Organization logo (base64 or URI) |
| KEY | No | Public encryption key (base64 or URI) |
| SOUND | No | Name pronunciation audio |
| ROLE | No | Role within organization |
| NICKNAME | No | Nickname(s) |

### v4.0 Additions

| Property | Description |
|----------|-------------|
| KIND | Contact type: `individual` (default), `group`, `org`, `location` |
| GENDER | Gender identity (e.g., `M`, `F`, `O`, `N`, `U`) |
| ANNIVERSARY | Wedding or other anniversary date |
| RELATED | Relationship to another contact (with TYPE=spouse, child, parent, etc.) |
| MEMBER | Group membership (used when KIND:group) — references other vCard UIDs |
| LANG | Language preference(s) |

## Parameters

Parameters modify properties, appearing between the property name and the colon:

| Parameter | Description | Example |
|-----------|-------------|---------|
| TYPE | Categorizes the value (work, home, cell, fax, voice) | `TEL;TYPE=cell:+1-555-0123` |
| VALUE | Specifies the value data type (text, uri, date, etc.) | `TEL;VALUE=uri:tel:+1-555-0123` |
| PREF | Preference ranking (1 = highest) | `EMAIL;PREF=1:primary@example.com` |
| MEDIATYPE | MIME type for URI values | `PHOTO;MEDIATYPE=image/png:https://...` |
| LANGUAGE | Language of the property value | `NOTE;LANGUAGE=en:Some note` |
| ENCODING | Encoding method (b = base64 in v3.0) | `PHOTO;ENCODING=b;TYPE=JPEG:[base64 data]` |
| CHARSET | Character set (v2.1 only; v4.0 mandates UTF-8) | `N;CHARSET=UTF-8:...` |

## Structured Address Format (ADR)

The ADR property uses semicolons to separate seven ordered fields:

```
ADR;TYPE=work:PO Box;Extended Address;Street;City;Region;Postal Code;Country
```

| Position | Field | Example |
|----------|-------|---------|
| 1 | PO Box | `PO Box 42` |
| 2 | Extended address | `Suite 300` |
| 3 | Street address | `1600 Pennsylvania Ave` |
| 4 | City (locality) | `Washington` |
| 5 | Region (state/province) | `DC` |
| 6 | Postal code | `20500` |
| 7 | Country | `USA` |

Empty fields are represented by consecutive semicolons: `ADR:;;123 Main St;Springfield;IL;62704;USA`

## Line Folding

Lines longer than 75 octets must be folded by inserting a CRLF followed by a single space or tab character. The receiving parser reassembles the original line by stripping CRLF + whitespace sequences:

```
NOTE:This is a very long note that exceeds the 75-octet line length lim
 it and must be folded onto the next line with a leading space character
 to indicate continuation.
```

## Version Differences

| Feature | v2.1 | v3.0 (RFC 2426) | v4.0 (RFC 6350) |
|---------|------|-----------------|-----------------|
| Encoding | Quoted-Printable, Base64 | B (base64) | UTF-8 only; binary via URI |
| Character set | CHARSET parameter | UTF-8 default | UTF-8 mandatory |
| PHOTO format | Inline base64 with TYPE | Inline base64 with ENCODING=b | URI preferred; data: URI for inline |
| FN property | Optional | Required | Required |
| N property | Required | Required | Optional (FN sufficient) |
| GEO format | `GEO:lat;lon` | `GEO:lat;lon` | `GEO:geo:lat,lon` (RFC 5870 URI) |
| TEL format | Plain number | Plain number | `VALUE=uri:tel:+1-555-0123` preferred |
| KIND property | N/A | N/A | Supported (individual, group, org, location) |
| GENDER | N/A | N/A | Supported |
| IMPP | N/A | N/A | Supported |
| RELATED | N/A | N/A | Supported |
| MIME type | text/x-vcard | text/vcard | text/vcard |
| Line ending | CRLF | CRLF | CRLF |

## File Format

| Property | Value |
|----------|-------|
| MIME type | `text/vcard` (v3+), `text/x-vcard` (v2.1) |
| File extension | `.vcf` or `.vcard` |
| Character encoding | UTF-8 (mandatory in v4.0) |
| Line ending | CRLF (`\r\n`) |
| Line length limit | 75 octets (fold longer lines) |
| Multiple contacts | Multiple vCards concatenated in one `.vcf` file |

## jCard (JSON Representation)

jCard ([RFC 7095](https://www.rfc-editor.org/rfc/rfc7095)) maps vCard to a JSON array format, used by RDAP and some REST APIs:

```json
["vcard", [
  ["version", {}, "text", "4.0"],
  ["fn", {}, "text", "Grace Hopper"],
  ["n", {}, "text", ["Hopper", "Grace", "Murray", "Rear Admiral", ""]],
  ["tel", {"type": "work"}, "uri", "tel:+1-202-555-0143"],
  ["email", {"type": "work"}, "text", "grace.hopper@navy.mil"],
  ["org", {}, "text", "United States Navy"]
]]
```

Each property is a JSON array: `[name, parameters-object, value-type, value]`.

## Common Uses

| Use Case | How vCard Is Used |
|----------|-------------------|
| CardDAV sync | Native data format for contact synchronization |
| Email signatures | `.vcf` attachment for easy contact import |
| QR codes | vCard or MECARD encoding on printed business cards |
| NFC tags | vCard payload for tap-to-share contacts |
| Phone contacts | Export/import format for contact lists |
| CRM systems | Contact import/export interchange format |
| LDAP directories | vCard mapping for directory entries |

## Standards

| Document | Title |
|----------|-------|
| [RFC 6350](https://www.rfc-editor.org/rfc/rfc6350) | vCard Format Specification (v4.0) |
| [RFC 2426](https://www.rfc-editor.org/rfc/rfc2426) | vCard MIME Directory Profile (v3.0) |
| [RFC 2425](https://www.rfc-editor.org/rfc/rfc2425) | MIME Content-Type for Directory Information |
| [RFC 7095](https://www.rfc-editor.org/rfc/rfc7095) | jCard: The JSON Format for vCard |
| [RFC 6868](https://www.rfc-editor.org/rfc/rfc6868) | Parameter Value Encoding in iCalendar and vCard |
| [RFC 6474](https://www.rfc-editor.org/rfc/rfc6474) | vCard Format Extensions: Place of Birth, Death |

## See Also

- [CardDAV](../web/carddav.md) — sync protocol that uses vCard as its data format
- [iCalendar](icalendar.md) — sister format for calendar/event data
- [LDAP](../naming/ldap.md) — directory protocol often mapped to/from vCard
- [SMTP](../email/smtp.md) — vCards are commonly sent as email attachments
- [HTTP](../web/http.md) — jCard is used in REST APIs

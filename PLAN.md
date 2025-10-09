# Svarog CLI Tool Plan

Here is a list of useful command-line tools that can be included in the `svarog` CLI tool.

## Data Conversion & Validation

### JSON Tool

- **Description**: A tool for working with JSON data, including formatting, validation, and conversion.
- **Commands**:
  - `svarog tool json format <file.json>`
  - `svarog tool json validate <file.json>`
  - `svarog tool json minify <file.json>`
  - `svarog tool json to-yaml <file.json>`
  - `svarog tool json to-xml <file.json>`

### YAML Tool

- **Description**: A tool for working with YAML data, including validation and conversion.
- **Commands**:
  - `svarog tool yaml validate <file.yaml>`
  - `svarog tool yaml to-json <file.yaml>`
  - `svarog tool yaml to-xml <file.yaml>`

### XML Tool

- **Description**: A tool for formatting and validating XML data.
- **Commands**:
  - `svarog tool xml format <file.xml>`
  - `svarog tool xml validate <file.xml>`
  - `svarog tool xml minify <file.xml>`
  - `svarog tool xml to-json <file.xml>`
  - `svarog tool xml to-yaml <file.xml>`

### CSV Tool

- **Description**: A tool for converting CSV data to JSON and vice versa.
- **Commands**:
  - `svarog tool csv to-json <file.csv>`
  - `svarog tool csv to-yaml <file.json>`
  - `svarog tool csv to-xml <file.json>`

## Encoding & Hashing

### HEX Tool

- **Description**: A tool for encoding and decoding hexadecimal data.
- **Commands**:
  - `svarog tool hex encode <string>`
  - `svarog tool hex decode <hex_string>`

### Hash Generator

- **Description**: A tool for generating various types of hashes.
- **Commands**:
  - `svarog tool hash md5 <string>`
  - `svarog tool hash sha1 <string>`
  - `svarog tool hash sha256 <string>`

### JWT Tool

- **Description**: A tool for decoding and validating JSON Web Tokens (JWT).
- **Commands**:
  - `svarog tool jwt decode <token>`
  - `svarog tool jwt encode --header '{"alg":"HS256"}' --payload '{"sub":"123"}' --secret 'secret'`

## Generators

### QR Code Generator

- **Description**: A tool for generating QR codes for various types of data.
- **Commands**:
  - `svarog tool qr link "https://example.com" --output qr.png`
  - `svarog tool qr email "user@example.com" --output qr.png`
  - `svarog tool qr wifi-login --ssid "SSID" --password "password" --output qr.png`
  - `svarog tool qr vcard --full-name "John Doe" --email "user@example.com" --output qr.png`

### Lorem Ipsum Generator

- **Description**: A tool for generating Lorem Ipsum placeholder text.
- **Commands**:
  - `svarog tool lorem --words 100`
  - `svarog tool lorem --paragraphs 3`

### Password Generator

- **Description**: A tool for generating secure random passwords.
- **Commands**:
  - `svarog tool password --length 16 --uppercase --lowercase --numbers --symbols`

### Passphrase Generator

- **Description**: A tool for generating memorable passphrases.
- **Commands**:
  - `svarog tool passphrase --length 4 --capitals --numbers --separator "-"`

### UUID/GUID Generator

- **Description**: A tool for generating and parsing UUIDs.
- **Commands**:
  - `svarog tool uuid create`
  - `svarog tool uuid create --version 4`
  - `svarog tool uuid parse <uuid> # Show version, variant, timestamp (if applicable)`
  - `svarog tool uuid create --version 7 --uppercase --bulk 100 --collision-check`
  - `svarog tool uuid create --min "00000000-0000-0000-0000-000000000000" --max "ffffffff-ffff-ffff-ffff-ffffffffffff"`

## Text & Case Manipulation

### Case Converter

- **Description**: A tool for converting text between different case styles.
- **Commands**:
  - `svarog tool case camel-to-snake "camelCaseString"`
  - `svarog tool case snake-to-camel "snake_case_string"`
  - `svarog tool case camel-to-kebab "camelCaseString"`
  - `svarog tool case kebab-to-camel "kebab-case-string"`

### Text Diff Tool

- **Description**: A tool for comparing two text files and highlighting differences.
- **Commands**:
  - `svarog tool diff file1.txt file2.txt`
  - `svarog tool diff file1.txt file2.txt --color`

## Web & Network

### HTTP Status Code Lookup

- **Description**: A tool for looking up the meaning of HTTP status codes.
- **Commands**:
  - `svarog tool http-status 200`
  - `svarog tool http-status 404`

### MIME Type Lookup

- **Description**: A tool for looking up MIME types by file extension.
- **Commands**:
  - `svarog tool mime .json`
  - `svarog tool mime .pdf`

### IP Address Info Lookup

- **Description**: A tool for looking up information about an IP address.
- **Commands**:
  - `svarog tool ip 8.8.8.8`

## Utilities

### Color Converter

- **Description**: A tool for converting colors between different formats.
- **Commands**:
  - `svarog tool color rgb-to-hex 255 0 0`
  - `svarog tool color hex-to-rgb "#FF0000"`
  - `svarog tool color rgb-to-hsl 255 0 0`
  - `svarog tool color rgb-to-hex`
  - `svarog tool color rgb-to-hsl`
  - `svarog tool color rgb-to-cmyk`
  - `svarog tool color hex-to-rgb`
  - `svarog tool color hex-to-hsl`
  - `svarog tool color hex-to-cmyk`
  - `svarog tool color hsl-to-rgb`
  - `svarog tool color hsl-to-cmyk`
  - `svarog tool color hsl-to-hex`
  - `svarog tool color cmyk-to-rgb`
  - `svarog tool color cmyk-to-hex`
  - `svarog tool color cmyk-to-hsl`

## Implementation Plan

### Phase 1: Core Structure & Foundation

1. **Project Scaffolding:**

   - Set up a standard Python project structure (`src/svarog`, `tests/`, `pyproject.toml`).
   - Choose and integrate a robust CLI framework like `Typer` or `Click` to manage commands, subcommands, and arguments.
   - Initialize the main `svarog` entry point and the top-level `tool` subcommand.

1. **Unified Input Handling:**

   - Create a core utility function to transparently handle input.
   - This function will check if data is being piped via `stdin`.
   - If `stdin` is empty, it will read input from the provided command-line arguments (e.g., a string or a file path).
   - This ensures every tool can seamlessly accept input from both sources without duplicating logic.

### Phase 2: Tool Implementation (Grouped by Category)

This phase can be parallelized, with each category being a distinct workstream.

1. **Data Conversion & Validation (JSON, YAML, XML, CSV):**

   - Implement subcommands for each format (`json`, `yaml`, etc.).
   - Utilize standard libraries (`json`, `csv`) and trusted third-party libraries (`PyYAML`) for the core logic (parsing, validation, conversion).
   - Connect each function to the unified input handler.

1. **Encoding & Hashing (HEX, Hash, JWT):**

   - Use Python's built-in `hashlib` for hash generation and `binascii` for HEX encoding.
   - Integrate a dedicated library like `PyJWT` for JWT decoding and encoding, as the logic is complex and security-sensitive.

1. **Generators (QR, Lorem, Password, Passphrase, UUID):**

   - **QR Code:** Use a library like `qrcode` to generate the image and `Pillow` to save it.
   - **Password/Passphrase:** Use the `secrets` module for cryptographically secure random generation.
   - **UUID:** Leverage the built-in `uuid` module.
   - **Lorem Ipsum:** Implement a simple text generator or use a lightweight library.

1. **Text & Case Manipulation (Case Converter, Diff):**

   - **Case Converter:** Write custom functions using string manipulation and regular expressions.
   - **Diff Tool:** Use the standard `difflib` module to generate diffs and add ANSI color codes for highlighted output.

1. **Web & Network (HTTP Status, MIME, IP Info):**

   - **HTTP/MIME:** Implement these as simple lookups from internal dictionaries or use the `mimetypes` module.
   - **IP Info:** Use the `requests` library to call a free, public IP lookup API. Implement error handling for network issues.

1. **Utilities (Color Converter):**

   - Implement the mathematical formulas for color space conversions (e.g., RGB to HEX).
   - Alternatively, use a small, focused library like `colour` to handle the conversions reliably.

### Phase 3: Testing, Documentation, and Refinement

1. **Comprehensive Testing:**

   - Create a suite of unit tests using `pytest`.
   - For each tool, write tests that validate its functionality with both string arguments and `stdin`.
   - Include tests for edge cases and invalid inputs to ensure robust error handling.

1. **User-Friendly Documentation:**

   - Leverage the CLI framework's features to automatically generate clear `--help` messages for every command and subcommand.
   - Update the project's `README.md` with a comprehensive overview of all available tools and practical usage examples.

1. **Packaging & Distribution:**

   - Configure `pyproject.toml` to define project metadata and dependencies.
   - Prepare the package for distribution via PyPI, making it easy to install with `pip`.

## Dependencies

The project will include an optional dependency group named `tools`. This will allow users to install all the extra dependencies required for the `svarog tool` commands by running `pip install svarog-cli[tools]`. This keeps the core installation lightweight.

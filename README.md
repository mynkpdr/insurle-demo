# InsurLE — Insurance Logic Engine

InsurLE is an automated demonstration system for generating, evaluating, and visualizing insurance contracts and corresponding claims. 

## Files and Components

- **`make_data.py`**: A generator script that produces the dummy mock data. It parses and packages raw contract data, insurance procedural logic rules (Prolog-style evaluation), and mock passenger/claim scenarios.
- **`insurle_data.json`**: The output of `make_data.py`. This JSON file holds the unified demo state. It contains arrays of `contracts` (including terms, conditions, and logical rule flowcharts) and mapping objects of `claims` bound to each contract.
- **`make_contract.py`**: A PDF generation script that digests contract metadata to assemble polished, multi-page contract documents detailing coverage specifications, formatted themes, and full terms & conditions.
- **`make_claim.py`**: A PDF generation script that reads `insurle_data.json` to generate realistic mock claim forms (including injury/incident specifics, claimant details, and cover sheets) as PDF documents.
- **`index.html`**: The primary frontend visualization dashboard that ties the project together.

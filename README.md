Software and System Security (SSS) - Assignment 2
This repository contains the code and reports for analyzing Python repositories for security vulnerabilities using Bandit and Safety tools as part of Assignment 2 for the Software and System Security course.

Contents of the Repository
Files
SSS_A2.py

The main Python script used to:
Clone open-source repositories.
Perform static code analysis using Bandit.
Check for dependency vulnerabilities using Safety.
Handle errors (e.g., missing requirements.txt, serialization issues).
Generate JSON reports summarizing the findings.
JSON Reports

Detailed reports generated by the script for each repository analyzed.
Example files:
fastapi_bandit_report.json: Bandit findings for the FastAPI repository.
fastapi_final_report.json: Combined summary of Bandit and Safety (if applicable).
Similar reports for other repositories like Django, Flask-RESTful, and Attrs.

How to Use the Script:
Prerequisites
Install the required tools using: 
pip install bandit safety

Clone this repository to your local machine:
git clone <repository_link>
cd SSS

Run the script using:
python SSS_A2.py

The JSON reports include:

Bandit Results:

Static code analysis findings for vulnerabilities like:
Use of weak cryptography.
Hardcoded secrets.
Usage of assert in production code.

Safety Results:

Dependency vulnerabilities with details such as:
Vulnerable package name.
Version.
Associated CVEs.
Note: Safety scans may fail or be skipped due to missing or placeholder requirements.txt files.

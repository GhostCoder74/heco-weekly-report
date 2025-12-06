# hcwr – heco Weekly Report  

<p align="center">
  <img src="opt/hcwr/share/hcwr-Logo.jpeg" alt="hcwr logo" width="280">
</p>


*A weekly summary generator for heco time tracking*  

**Author:**  
- Christian Klose <cklose@intevation.de>  
- Raimund Renkert <rrenkert@intevation.de>  

**Repository:**  
https://github.com/GhostCoder74/heco-weekly-report  

**Copyright:**  
© 2024–2026 Intevation GmbH  
Licensed under **GPL-2.0-or-later**

---

# 📖 About the Project

**hcwr – heco Weekly Report** is a command-line tool that generates weekly summaries (“Wochenfazit”) from heco time tracking data.  
It supports **SQLite** (`time.db`) as well as **PostgreSQL**, making it compatible with both local and server-based setups.

The resulting weekly summary follows the template used for the  
**Wochenfazit by Bernhard Reiter** at Intevation GmbH:  
https://heptapod.host/intevation/getan/-/blob/branch/default/getan/templates/wochenfazit

The tool offers powerful filtering, JSON export, absence management, job-based searches, keyword-based project grouping and auto-import of heco data structures.

---

# ✨ Features

- Generate weekly summaries based on heco work logs  
- Supports **SQLite** and **PostgreSQL**
- Full weekly control: `--week`, `--year`, `WEEK=…`
- Absence & leave management (`-A Urlaub`, `-A AU`, `-A KG`, `-A ZKÜ=<H:M>`, `-A ZKA=<H:M>`)
- JSON output for automation
- Keyword-based contract/project mapping
- Summaries, totals, category aggregations
- Interactive configuration
- Optional “dry-run” mode
- Import heco `time.db` structure (`--init-heco`)
- Fully scriptable for CI or cron jobs

---

# 📁 Directory Structure

After installation, the system files are located in:

```bash
./
├── Makefile
└── opt
    └── hcwr
        ├── bin
        │   └── hcwr
        ├── modules
        │   ├── hcwr_config_mod.py
        │   ├── hcwr_dbg_mod.py
        │   ├── hcwr_dbms_mod.py
        │   ├── hcwr_extexec_mod.py
        │   ├── hcwr_globals_mod.py
        │   ├── hcwr_hcwrd_mod.py
        │   ├── hcwr_json_mod.py
        │   ├── hcwr_pg_queries_sql.py
        │   ├── hcwr_plugins_mod.py
        │   ├── hcwr_remote_mod.py
        │   ├── hcwr_sqlite_queries_sql.py
        │   ├── hcwr_tasks_mod.py
        │   ├── hcwr_utils_mod.py
        │   └── hcwr_wfout_mod.py
        └── share
            ├── hcwr-Logo.jpeg
            ├── LICENSE
            └── README.md
    
```

# 📦 Installation

Clone the repository:

```bash
git clone https://github.com/GhostCoder74/heco-weekly-report
cd heco-weekly-report
```

## Quick install
#### Install the plugin into hcwr Default directory:
```bash
sudo make install
```
#### Install the plugin into hcwr special directory:

(Requires hcwr ≥ v1.0)
```bash
make install PREFIX=/usr/ BASE_DIR=local SHARE_DIR=/usr/share/hcwr
```
## Manual install

```bash
PREFIX="opt/hcwr"
sudo mkdir -p /$PREFIX/{bin,modules,share}
sudo install -m 755 $PREFIX/bin/hcwr /$PREFIX/bin/
sudo install -m 644 $PREFIX/modules/hcwr_*_mod.py /$PREFIX/modules/
sudo install -m 644 $PREFIX/share/hcwr-Logo.jpeg /$PREFIX/share/
export PATH="$PATH:/$PREFIX/bin"
```
## 🔌 Plugin installation of **geaCal** for hcwr

To install the Gaussian Easter Algorithm Calendar Tool (**geaCal**) as an hcwr plugin, clone the plugin repository and copy it into the hcwr plugin directory.

### (Optional) Clone the geaCal plugin
```bash
cd heco-weekly-report
git clone https://github.com/GhostCoder74/GaussEasterAlgorithm.git
```
#### Install the plugin into hcwr Default directory:

(Requires hcwr ≥ v1.0)

```bash
make install2hcwr
```
This installs the plugin files into:
```bash
/opt/hcwr/bin/
/opt/hcwr/modules/
```

#### Install the plugin into hcwr special directory:

(Requires hcwr ≥ v1.0)
```bash
make install2hcwr PREFIX=/usr BASE_DIR=lib/hcwr SHARE_DIR=/var/lib/share/hcwr
```
# 🚀 Usage

## 🗂 Output Modes
### Basic Example for generating a weekly report for week 19 of year 2025
```bash
hcwr -w 19 -y 2025
```

### Using environment variables

```bash
YEAR=2025 WEEK=19 hcwr -n
```
### Generate summary to a file
```bash
hcwr -w 22 -y 2025 -o weekly-summary.txt
```

### Initialize a fresh time.db
```bash
hcwr --init-heco 27
```

# 🛠 Command Line Options
```bash
hcwr --help
usage: hcwr [-h] [-w WEEK] [-y YEAR] [-d DATABASE] [-g GROUP] [-c CONFIG] [-o OUTPUT_FILE] [-ih [KW]] [-C] [-ak] [-dk] [-sk] [-n] [-v] [-a] [-A PH | AU | KG | ZKÜ=<H:M> | ZKA=<H:M>] [-J]
            [-j] [-B YYYY-MM-DD] [-E YYYY-MM-DD] [-D] [-S] [-T CAT_TIME_TOTALS_OF] [-F FORMAT] [-s SEARCH] [-z ZEITERFASSUNG]

hcwr "Heco Weekly Report" 

Creates WocheWeekly Summary From heco time.db or PostgreSQL database

Optionale Nutzung von Umgebungsvariablen:
    YEAR          – Jahreszahl (z.B. 2025), das selbe geht auch mit -y/--year
    WEEK oder KW  – Kalenderwoche, erlaubt sind Formate:
        WEEK=19      oder KW=19
        WEEK=2025/19 oder KW=2025/19
        WEEK=2025-19 oder KW=2025-19
        WEEK=19/2025 oder KW=19/2025
        WEEK=19-2025 oder KW=19-2025
    Falls YEAR nicht gesetzt ist, wird das aktuelle Jahr angenommen.

    GROUP         - Default Datei Berechtigungs-Gruppe,
                    das selbe wie bei -g/--group

Beispiel:
    YEAR=2025 WEEK=19 hcwr -n

options:
  -h, --help            show this help message and exit
  -w WEEK, -kw WEEK, --week WEEK
                        Calendar week (1-53)
  -y YEAR, --year YEAR  Jahr (e.g., 2024)
  -d DATABASE, --database DATABASE
                        Path to the SQLite database (optional)
  -g GROUP, --group GROUP
                        Default User Group
  -c CONFIG, --config CONFIG
                        User config file
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Path to the target file for the weekly summary
  -ih [KW], --init-heco [KW]
                        Initializes a heco time.db and imports the project structure. Optionally with calendar week (e.g., 27).
  -C, --configure       Edit configuration interactively
  -ak, --add-contract-keyword
                        Interactively capture contract ID and related keywords
  -dk, --delete-keyword
                        Delete a contract keyword from the database
  -sk, --show-keywords  Displays all stored contract keywords from the database
  -n, --dry-run         Output only, no saving
  -v, --version         Versions info
  -a, --all-jobs        Get all!
  -A PH | AU | KG | ZKÜ=<H:M> | ZKA=<H:M>, --absence PH | AU | KG | ZKÜ=<H:M> | ZKA=<H:M>
                        Set vacation, absense or other LOA days
                            VALUES for -A                          |  SHORT VALUES for -A
                              Urlaub                               |    PH
                              Krank                                |    AU
                              Krankengeldbezug                     |    KG
                              Zeitkonto_Übertrag_vom_Vorjahr=<H:M> |    ZKÜ=<H:M>     # H=Hours, M=Minutes
                              Zeitkonto_Abzug_Ausgezahlt=<H:M>     |    ZKA=<H:M>     # H=Hours, M=Minutes
                            
                            EXAMPLE:
                                -A Urlaub -B 2025-12-01[, -E 2025-12-05]
                        
                            Short option for Urlaub(Public Holyday):
                                -A PH -B 2025-12-01[, -E 2025-12-05]
                        
  -J, --job-entries     To use in conjunction with -s/--search for searching in Job-Entries
  -j, --json            Get JSON output, by using --json and --job-entries
  -B YYYY-MM-DD, --start-day YYYY-MM-DD
                        Date string YYYY-MM-DD
  -E YYYY-MM-DD, --stop-day YYYY-MM-DD
                        Date string YYYY-MM-DD
  -D, --delete          Delete vaction or absence EXAMPLE: -D -A -B 2025-12-01[, -E 2025-12-05]
  -S, --sum-times       Get sum of times!
  -T CAT_TIME_TOTALS_OF, --cat-time-totals-of CAT_TIME_TOTALS_OF
                        Get category time totals of 'CategoryA[,CategoryB,...]'
  -F FORMAT, --format FORMAT
                        Format STRING
  -s SEARCH, --search SEARCH
                        Search STRING
  -z ZEITERFASSUNG, --zeiterfassung ZEITERFASSUNG
                        Formatting for zeiterfassung.txt EXANPLE: -z ckl,sua
```

# 🔎 Examples
### Search within job entries
```bash
hcwr -s "Meeting" --job-entries
```

### Absence entry for vacation
```bash
hcwr -A Urlaub -B 2025-12-01 -E 2025-12-05
```

### JSON export for job time outout
```bash
hcwr -j -s "ContractA"
```

# 📄 License
This project is licensed under the
GNU General Public License v2.0 or later (GPL-2.0-or-later).
See: [LICENSE](https://www.gnu.org/licenses/#GPL)

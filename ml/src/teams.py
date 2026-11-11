ABBR_TO_FULL = {
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos",
    "DET": "Detroit Lions",
    "GB": "Green Bay Packers",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs",
    "LA": "Los Angeles Rams",
    "LAC": "Los Angeles Chargers",
    "LV": "Las Vegas Raiders",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "NE": "New England Patriots",
    "NO": "New Orleans Saints",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders",
}
 
# Old abbreviations for franchises that moved or were renamed.
LEGACY_ABBR = {
    "OAK": "LV",
    "SD": "LAC",
    "STL": "LA",
    "LAR": "LA",
    "WSH": "WAS",
    "JAC": "JAX",
}
 
FULL_TO_ABBR = {full: abbr for abbr, full in ABBR_TO_FULL.items()}
 
# Converts team abbreviation to normalized abbreviation (handles legacy abbreviations) 
def normalize_abbr(abbr: str) -> str:
    return LEGACY_ABBR.get(abbr, abbr)
 
# Converts team abbreviation to full team name
def to_full_name(abbr: str) -> str:
    return ABBR_TO_FULL[normalize_abbr(abbr)]
 
#Converts full team name to abbreviation 
def to_abbr(full_name: str) -> str:
    return FULL_TO_ABBR[full_name]

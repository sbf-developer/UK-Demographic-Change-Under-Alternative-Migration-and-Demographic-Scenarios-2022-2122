"""UK ethnic demographic projection system.

Conditional demographic trajectories under specified migration, fertility,
mortality, partnership and ethnic-identification assumptions.
"""

__version__ = "0.1.0"
__author__ = "Scott Brodie Forsyth"

WATERMARK = (
    "Methodological demonstration only. Not an empirical projection."
)

NATIONS = ("england", "wales", "scotland", "northern_ireland")
SEXES = ("female", "male")
GENERATIONS = (
    "foreign_born_adult",
    "foreign_born_child",
    "ukborn_two_foreign_parents",
    "ukborn_one_foreign_parent",
    "ukborn_two_ukborn_parents",
)
BROAD_ETHNIC_GROUPS = (
    "white",
    "mixed",
    "asian",
    "black",
    "other",
)
AGE_MIN = 0
AGE_MAX = 100  # 100+ open-ended category
BASE_YEAR = 2022
PROJECTION_END = 2122
REPORT_YEARS = (2030, 2040, 2050, 2075, 2100, 2122)

# UK nation codes (GSS)
NATION_CODES = {
    "england": "E92000001",
    "wales": "W92000004",
    "scotland": "S92000003",
    "northern_ireland": "N92000002",
}

"""
Lab Assignment 1 - Working with a Public REST API Using Python

Fetches near-Earth asteroids from NASA's NeoWs API (https://api.nasa.gov),
parses the JSON response into Python objects, and prints a formatted summary.

The API key is read from the NASA_API_KEY environment variable, loaded from a
local .env file with python-dotenv.
"""

import os
import sys
from dataclasses import dataclass
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

API_URL = "https://api.nasa.gov/neo/rest/v1/feed"
MAX_DAYS = 7  # the feed endpoint returns at most 7 days per request


@dataclass
class Asteroid:
    """One near-Earth object and its closest approach in the requested window."""

    name: str
    diameter_min_m: float
    diameter_max_m: float
    hazardous: bool
    approach_date: str
    miss_distance_km: float
    velocity_kmh: float
    url: str

    @property
    def avg_diameter_m(self) -> float:
        return (self.diameter_min_m + self.diameter_max_m) / 2

    @property
    def lunar_distances(self) -> float:
        """Miss distance expressed in Earth-Moon distances (~384,400 km)."""
        return self.miss_distance_km / 384_400

    @classmethod
    def from_json(cls, data: dict) -> "Asteroid":
        """Build an Asteroid from one entry of the API's JSON response."""
        size = data["estimated_diameter"]["meters"]
        approach = data["close_approach_data"][0]
        name = data["name"]
        if name.startswith("(") and name.endswith(")"):  # e.g. "(2018 NE1)" -> "2018 NE1"
            name = name[1:-1]
        return cls(
            name=name,
            diameter_min_m=size["estimated_diameter_min"],
            diameter_max_m=size["estimated_diameter_max"],
            hazardous=data["is_potentially_hazardous_asteroid"],
            approach_date=approach["close_approach_date"],
            miss_distance_km=float(approach["miss_distance"]["kilometers"]),
            velocity_kmh=float(approach["relative_velocity"]["kilometers_per_hour"]),
            url=data["nasa_jpl_url"],
        )


class NeoReport:
    """Retrieves the NeoWs feed for a date range and organizes the results."""

    def __init__(self, api_key: str, start: date, end: date):
        if (end - start).days >= MAX_DAYS:
            raise ValueError(f"Date range must be at most {MAX_DAYS} days.")
        self.api_key = api_key
        self.start = start
        self.end = end
        self.asteroids: list[Asteroid] = []

    def fetch(self) -> None:
        params = {
            "start_date": self.start.isoformat(),
            "end_date": self.end.isoformat(),
            "api_key": self.api_key,
        }
        response = requests.get(API_URL, params=params, timeout=30)
        if response.status_code == 403:
            raise RuntimeError("API key rejected (HTTP 403). Check NASA_API_KEY in .env.")
        if response.status_code == 429:
            raise RuntimeError("Rate limit reached (HTTP 429). Use a personal key from api.nasa.gov.")
        response.raise_for_status()

        payload = response.json()
        self.asteroids = [
            Asteroid.from_json(item)
            for day in payload["near_earth_objects"].values()
            for item in day
        ]

    # ---- organized views of the data -------------------------------------
    @property
    def hazardous(self) -> list[Asteroid]:
        return [a for a in self.asteroids if a.hazardous]

    def closest(self, n: int = 5) -> list[Asteroid]:
        return sorted(self.asteroids, key=lambda a: a.miss_distance_km)[:n]

    def largest(self) -> Asteroid:
        return max(self.asteroids, key=lambda a: a.avg_diameter_m)

    def fastest(self) -> Asteroid:
        return max(self.asteroids, key=lambda a: a.velocity_kmh)

    def per_day(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for a in sorted(self.asteroids, key=lambda a: a.approach_date):
            counts[a.approach_date] = counts.get(a.approach_date, 0) + 1
        return counts

    # ---- formatted output ------------------------------------------------
    def print_summary(self) -> None:
        line = "=" * 72
        print(line)
        print("  NEAR-EARTH ASTEROID REPORT  (source: NASA NeoWs API)".center(72))
        print(f"  {self.start:%d %b %Y}  ->  {self.end:%d %b %Y}".center(72))
        print(line)

        if not self.asteroids:
            print("No asteroids returned for this period.")
            return

        print(f"\n  Total asteroids tracked      : {len(self.asteroids)}")
        print(f"  Potentially hazardous        : {len(self.hazardous)}")

        big, fast = self.largest(), self.fastest()
        print(f"  Largest (avg. diameter)      : {big.name}  ~{big.avg_diameter_m:,.0f} m")
        print(f"  Fastest (relative velocity)  : {fast.name}  {fast.velocity_kmh:,.0f} km/h")

        print("\n  Asteroids per day")
        print("  " + "-" * 40)
        for day, count in self.per_day().items():
            print(f"  {day}  {'#' * count} {count}")

        print("\n  5 closest approaches")
        header = f"  {'Name':<24}{'Date':<12}{'Distance (km)':>15}{'Lunar':>8}{'Size (m)':>10}  Hzd"
        print(header)
        print("  " + "-" * (len(header) - 2))
        for a in self.closest():
            print(
                f"  {a.name[:23]:<24}{a.approach_date:<12}{a.miss_distance_km:>15,.0f}"
                f"{a.lunar_distances:>8.1f}{a.avg_diameter_m:>10,.0f}  {'YES' if a.hazardous else 'no'}"
            )

        if self.hazardous:
            print("\n  Potentially hazardous asteroids")
            print("  " + "-" * 40)
            for a in sorted(self.hazardous, key=lambda a: a.approach_date):
                print(f"  - {a.name} ({a.approach_date}), ~{a.avg_diameter_m:,.0f} m, "
                      f"{a.lunar_distances:.1f} lunar distances")
                print(f"    {a.url}")
        print("\n" + line)


def main() -> int:
    load_dotenv()
    api_key = os.getenv("NASA_API_KEY")
    if not api_key:
        print("Error: NASA_API_KEY is not set. Add it to the .env file (see .env.example).")
        return 1

    end = date.today()
    start = end - timedelta(days=MAX_DAYS - 1)
    report = NeoReport(api_key, start, end)
    try:
        report.fetch()
    except (requests.RequestException, RuntimeError) as exc:
        print(f"Error while calling the API: {exc}")
        return 1

    report.print_summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())

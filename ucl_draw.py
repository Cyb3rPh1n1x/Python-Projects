import random
from collections import defaultdict

TEAMS = [
    ("Paris", "France", 1),
    ("Bayern München", "Germany", 1),
    ("Real Madrid", "Spain", 1),
    ("Liverpool", "England", 1),
    ("Inter", "Italy", 1),
    ("Man City", "England", 1),
    ("Arsenal", "England", 1),
    ("Barcelona", "Spain", 1),
    ("Atleti", "Spain", 1),

    ("B. Dortmund", "Germany", 2),
    ("Roma", "Italy", 2),
    ("Sporting CP", "Portugal", 2),
    ("Aston Villa", "England", 2),
    ("Porto", "Portugal", 2),
    ("Man Utd", "England", 2),
    ("Club Brugge", "Belgium", 2),
    ("Real Betis", "Spain", 2),
    ("PSV", "Netherlands", 2),

    ("Feyenoord", "Netherlands", 3),
    ("Lille", "France", 3),
    ("Bodø/Glimt", "Norway", 3),
    ("Napoli", "Italy", 3),
    ("Leipzig", "Germany", 3),
    ("Villarreal", "Spain", 3),
    ("Fenerbahçe", "Turkey", 3),
    ("Shakhtar", "Ukraine", 3),
    ("Galatasaray", "Turkey", 3),

    ("Slavia Praha", "Czechia", 4),
    ("S. Bratislava", "Slovakia", 4),
    ("Stuttgart", "Germany", 4),
    ("AEK Athens", "Greece", 4),
    ("LASK", "Austria", 4),
    ("Como", "Italy", 4),
    ("Lens", "France", 4),
    ("Viking", "Norway", 4),
    ("Sabah", "Azerbaijan", 4),
]

POTS = defaultdict(list)

for name, country, pot in TEAMS:
    POTS[pot].append(name)

COUNTRY = {name: country for name, country, _ in TEAMS}
TEAM_POT = {name: pot for name, _, pot in TEAMS}
ALL_TEAMS = [t[0] for t in TEAMS]

MATCHES_PER_POT = 2
MAX_PER_COUNTRY = 2
MAX_ATTEMPTS = 200

class DrawFailed(Exception):
    pass

POT_NODE_BUDGET = 20000
POT_RETRIES = 200


def _solve_pot(
    pot,
    fixtures,
    home_done,
    away_done,
    country_count,
    home_opponents,
    away_opponents
):
    def legal(team, opp):
        if team == opp or opp in fixtures[team]:
            return False

        if COUNTRY[team] == COUNTRY[opp]:
            return False

        if country_count[team][COUNTRY[opp]] >= MAX_PER_COUNTRY:
            return False

        if country_count[opp][COUNTRY[team]] >= MAX_PER_COUNTRY:
            return False

        return True

    def candidates_for(team, side):
        if side == "home":
            return [
                o for o in POTS[pot]
                if o != team
                and TEAM_POT[team] not in away_done[o]
                and legal(team, o)
            ]

        return [
            o for o in POTS[pot]
            if o != team
            and TEAM_POT[team] not in home_done[o]
            and legal(team, o)
        ]

    def apply(home, away):
        fixtures[home].add(away)
        fixtures[away].add(home)

        home_done[home].add(TEAM_POT[away])
        away_done[away].add(TEAM_POT[home])

        country_count[home][COUNTRY[away]] += 1
        country_count[away][COUNTRY[home]] += 1

        home_opponents[home].append(
            (away, TEAM_POT[away])
        )

        away_opponents[away].append(
            (home, TEAM_POT[home])
        )

    def undo(home, away):
        fixtures[home].discard(away)
        fixtures[away].discard(home)

        home_done[home].discard(TEAM_POT[away])
        away_done[away].discard(TEAM_POT[home])

        country_count[home][COUNTRY[away]] -= 1
        country_count[away][COUNTRY[home]] -= 1

        home_opponents[home].pop()
        away_opponents[away].pop()

    for _ in range(POT_RETRIES):
        stack = []
        nodes = 0
        success = True

        while True:
            remaining = []

            for team in ALL_TEAMS:
                if pot not in home_done[team]:
                    remaining.append((team, "home"))

                if pot not in away_done[team]:
                    remaining.append((team, "away"))

            if not remaining:
                break

            nodes += 1

            if nodes > POT_NODE_BUDGET:
                success = False
                break

            random.shuffle(remaining)

            best_slot = None
            best_cands = None

            for team, side in remaining:
                cands = candidates_for(team, side)

                if best_cands is None or len(cands) < len(best_cands):
                    best_slot = (team, side)
                    best_cands = cands

                    if not cands:
                        break

            team, side = best_slot

            random.shuffle(best_cands)

            if best_cands:
                opp = best_cands.pop()

                if side == "home":
                    apply(team, opp)
                else:
                    apply(opp, team)

                stack.append(
                    (team, side, opp, best_cands)
                )

                continue

            backtracked = False

            while stack:
                p_team, p_side, p_opp, p_remaining = stack.pop()

                if p_side == "home":
                    undo(p_team, p_opp)
                else:
                    undo(p_opp, p_team)

                if p_remaining:
                    opp = p_remaining.pop()

                    if p_side == "home":
                        apply(p_team, opp)
                    else:
                        apply(opp, p_team)

                    stack.append(
                        (p_team, p_side, opp, p_remaining)
                    )

                    backtracked = True
                    break

            if not backtracked:
                success = False
                break

        if success:
            return

        while stack:
            p_team, p_side, p_opp, _ = stack.pop()

            if p_side == "home":
                undo(p_team, p_opp)
            else:
                undo(p_opp, p_team)

    raise DrawFailed()


def try_build_draw():
    fixtures = {t: set() for t in ALL_TEAMS}
    home_done = {t: set() for t in ALL_TEAMS}
    away_done = {t: set() for t in ALL_TEAMS}

    country_count = {
        t: defaultdict(int)
        for t in ALL_TEAMS
    }

    home_opponents = defaultdict(list)
    away_opponents = defaultdict(list)

    for pot in sorted(POTS):
        _solve_pot(
            pot,
            fixtures,
            home_done,
            away_done,
            country_count,
            home_opponents,
            away_opponents
        )

    return fixtures, home_opponents, away_opponents


def build_draw(max_attempts=MAX_ATTEMPTS):
    for attempt in range(1, max_attempts + 1):
        try:
            fixtures, home_opponents, away_opponents = try_build_draw()

            return (
                fixtures,
                home_opponents,
                away_opponents,
                attempt
            )

        except DrawFailed:
            continue

    raise RuntimeError(
        f"Could not complete a valid draw in {max_attempts} attempts."
    )


def print_draw(
    fixtures,
    home_opponents,
    away_opponents,
    attempts
):
    name_w = max(len(t) for t in ALL_TEAMS) + 1
    country_w = max(len(c) for c in COUNTRY.values()) + 2

    print("=" * 78)
    print(
        "UEFA CHAMPIONS LEAGUE — LEAGUE PHASE DRAW".center(78)
    )
    print(
        f"(completed in {attempts} attempt"
        f"{'s' if attempts != 1 else ''})".center(78)
    )
    print("=" * 78)

    for pot in sorted(POTS):
        print(
            f"\n--- POT {pot} "
            + "-" * (72 - len(f"POT {pot}"))
        )

        for team in POTS[pot]:
            header = (
                f"{team:<{name_w}} "
                f"[{COUNTRY[team]:<{country_w}}]"
            )

            print(f"\n{header}")

            homes = sorted(
                home_opponents[team],
                key=lambda x: (x[1], x[0])
            )

            aways = sorted(
                away_opponents[team],
                key=lambda x: (x[1], x[0])
            )

            for opp, opp_pot in homes:
                print(
                    f"    HOME  vs  "
                    f"{opp:<{name_w}} "
                    f"(Pot {opp_pot}, {COUNTRY[opp]})"
                )

            for opp, opp_pot in aways:
                print(
                    f"    AWAY  vs  "
                    f"{opp:<{name_w}} "
                    f"(Pot {opp_pot}, {COUNTRY[opp]})"
                )

    print("\n" + "=" * 78)
    print("SANITY CHECKS".center(78))
    print("=" * 78)

    ok = True

    for team in ALL_TEAMS:
        if len(fixtures[team]) != 8:
            print(
                f"  ✗ {team} has "
                f"{len(fixtures[team])} opponents "
                f"(expected 8)"
            )
            ok = False

        countries = defaultdict(int)

        for opp in fixtures[team]:
            countries[COUNTRY[opp]] += 1

        for country, count in countries.items():
            if count > MAX_PER_COUNTRY:
                print(
                    f"  ✗ {team} plays {count} teams "
                    f"from {country} (max {MAX_PER_COUNTRY})"
                )
                ok = False

    if ok:
        print(
            "  ✔ All 36 teams have exactly 8 legal opponents, "
            "no country limit exceeded."
        )

    print()


if __name__ == "__main__":
    fixtures, home_opponents, away_opponents, attempts = build_draw()
    print_draw(
        fixtures,
        home_opponents,
        away_opponents,
        attempts
    )
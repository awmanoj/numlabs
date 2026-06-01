"""Birth-year fun facts.

Given a year, return a mix of *curated* highlights (what released, what
happened) and *computed* facts that work for any year — the age someone born
that year turns this year, the decade, the generational cohort, the Chinese
zodiac sign, whether it was a leap year, and the year in Roman numerals.

The curated table is the source of truth for the "what happened" lines; the
computed helpers fill in the rest so even a year with no curated entry still
returns something fun. Pure data + arithmetic, no I/O — runs in the browser
via Pyodide and standalone via the __main__ block below.
"""

# The "current" year the age / decade-relative phrasing is reckoned against.
# Kept as a constant so the math is deterministic and testable rather than
# pulling the real clock (which Pyodide sandboxes anyway).
THIS_YEAR = 2026

# Curated highlights. One entry per notable year; each a short list of
# well-known releases / events. Years not listed still get computed facts.
_EVENTS = {
    1940: ["First McDonald's opens", "Tom and Jerry debuts", "Lascaux cave paintings discovered"],
    1941: ["Citizen Kane released", "Mount Rushmore completed", "Captain America debuts in comics"],
    1945: ["World War II ends", "The United Nations is founded", "The first atomic bombs"],
    1947: ["The transistor is invented", "Jackie Robinson breaks baseball's color barrier", "Chuck Yeager breaks the sound barrier"],
    1948: ["The NHS is founded in Britain", "The LP record is introduced", "The State of Israel is founded"],
    1949: ["NATO is founded", "George Orwell's 1984 is published", "The People's Republic of China is founded"],
    1950: ["The Peanuts comic strip debuts", "The first credit card (Diners Club)", "Charlie Brown and Snoopy arrive"],
    1951: ["The Catcher in the Rye is published", "I Love Lucy premieres", "Color TV is introduced"],
    1952: ["Elizabeth II becomes Queen", "Mr. Potato Head hits shelves", "The polio vaccine is developed"],
    1953: ["The structure of DNA is described", "Everest is first summited", "Elizabeth II's coronation"],
    1954: ["Godzilla stomps into cinemas", "Elvis records his first single", "Brown v. Board of Education"],
    1955: ["Disneyland opens", "Rosa Parks sparks the bus boycott", "Guinness World Records is first published"],
    1956: ["IBM ships the first hard disk drive", "Elvis releases Heartbreak Hotel", "The first transatlantic phone cable"],
    1957: ["Sputnik launches the Space Age", "Dr. Seuss's The Cat in the Hat", "Leave It to Beaver premieres"],
    1958: ["NASA is founded", "The LEGO brick is patented", "The hula hoop craze; the integrated circuit"],
    1959: ["The Barbie doll debuts", "Alaska and Hawaii become states", "Motown Records is founded"],
    1960: ["The first televised presidential debate", "Hitchcock's Psycho", "The laser is invented"],
    1961: ["Yuri Gagarin is the first human in space", "The Berlin Wall goes up", "Catch-22 is published"],
    1962: ["The first James Bond film, Dr. No", "Spider-Man debuts in comics", "The Cuban Missile Crisis"],
    1963: ["JFK is assassinated", "MLK's 'I Have a Dream' speech", "Doctor Who premieres"],
    1964: ["The Beatles arrive in America", "The Ford Mustang is unveiled", "The Civil Rights Act; Mary Poppins"],
    1965: ["The Sound of Music", "The first spacewalk", "Soft contact lenses introduced"],
    1966: ["Star Trek premieres", "England wins the World Cup", "The Beach Boys' Pet Sounds"],
    1967: ["The first Super Bowl", "Rolling Stone magazine launches", "The first human heart transplant"],
    1968: ["2001: A Space Odyssey", "Apollo 8 orbits the Moon", "The Big Mac goes nationwide"],
    1969: ["Apollo 11 lands on the Moon", "Woodstock", "ARPANET — the internet's ancestor; Sesame Street"],
    1970: ["The first Earth Day", "The Beatles break up", "The floppy disk is introduced"],
    1971: ["The first email is sent", "Intel's first microprocessor", "Walt Disney World and Starbucks open"],
    1972: ["Pong launches the video-game industry", "Atari is founded", "The first pocket scientific calculator"],
    1973: ["The first mobile phone call", "The Sydney Opera House opens", "Pink Floyd's Dark Side of the Moon"],
    1974: ["The Rubik's Cube is invented", "Stephen King's Carrie", "Hank Aaron breaks the home-run record"],
    1975: ["Microsoft is founded", "The first home VCR (Betamax)", "Jaws invents the summer blockbuster"],
    1976: ["Apple is founded", "Concorde enters service", "Rocky; the US Bicentennial"],
    1977: ["Star Wars released", "The Apple II ships", "The Atari 2600; Elvis dies"],
    1978: ["The first test-tube baby", "Garfield debuts", "Space Invaders; Grease"],
    1979: ["The Sony Walkman", "Voyager reaches Jupiter", "The first cellular network (Japan)"],
    1980: ["Pac-Man released", "CNN launches", "The Rubik's Cube goes global; Post-it Notes"],
    1981: ["The IBM PC", "MTV launches", "The first Space Shuttle; Raiders of the Lost Ark"],
    1982: ["The first CD player", "E.T. the Extra-Terrestrial", "The Commodore 64; Thriller"],
    1983: ["The first handheld mobile phone (DynaTAC)", "Return of the Jedi", "The Nintendo Famicom; TCP/IP"],
    1984: ["The Apple Macintosh", "Tetris is created", "The Terminator; Ghostbusters"],
    1985: ["Super Mario Bros. and the NES", "Back to the Future", "Live Aid; Windows 1.0"],
    1986: ["Pixar is founded", "Chernobyl and the Challenger disaster", "The Legend of Zelda"],
    1987: ["The Simpsons shorts debut", "Final Fantasy launches", "Michael Jackson's Bad"],
    1988: ["Die Hard", "The first transatlantic fiber cable", "Prozac is approved"],
    1989: ["The World Wide Web is proposed", "The Berlin Wall falls", "The Game Boy; The Simpsons premieres"],
    1990: ["The Hubble Space Telescope launches", "Adobe Photoshop 1.0", "Windows 3.0; the first web page"],
    1991: ["The World Wide Web goes public", "Linux is released", "Sonic the Hedgehog; Nirvana's Nevermind"],
    1992: ["The first text message is sent", "Mortal Kombat", "Cartoon Network launches"],
    1993: ["The Mosaic web browser", "Doom released", "Jurassic Park; the Intel Pentium"],
    1994: ["Amazon and Yahoo are founded", "The Sony PlayStation (Japan)", "Friends premieres; The Lion King"],
    1995: ["Toy Story released", "Windows 95 launched", "eBay is founded; JavaScript is created"],
    1996: ["Pokemon debuts in Japan", "The Nintendo 64", "Dolly the sheep is cloned; the StarTAC flip phone"],
    1997: ["The first Harry Potter book", "Titanic", "Deep Blue beats Kasparov; Google.com is registered"],
    1998: ["Google is founded", "The Apple iMac", "Windows 98; the Furby craze"],
    1999: ["Napster", "The Matrix", "SpongeBob premieres; the Euro is introduced"],
    2000: ["The PlayStation 2", "The Sims released", "The USB flash drive; Y2K passes quietly"],
    2001: ["The Apple iPod", "Wikipedia launches", "The Xbox; Harry Potter and LOTR hit cinemas"],
    2002: ["Camera phones go mainstream", "Spider-Man (Tobey Maguire)", "Xbox Live; the Roomba"],
    2003: ["Skype and Myspace launch", "The iTunes Store", "Finding Nemo; LinkedIn"],
    2004: ["Facebook is founded", "Gmail launches", "World of Warcraft; the Nintendo DS"],
    2005: ["YouTube is founded", "The Xbox 360", "Google Maps; Reddit launches"],
    2006: ["Twitter launches", "The Nintendo Wii", "The PlayStation 3; Pluto is demoted"],
    2007: ["The first iPhone", "The Amazon Kindle", "Halo 3; Android is announced"],
    2008: ["The App Store opens", "The Bitcoin whitepaper", "Iron Man and The Dark Knight"],
    2009: ["The Bitcoin network launches", "WhatsApp is founded", "Avatar; Minecraft's early release"],
    2010: ["The Apple iPad", "Instagram launches", "Pinterest; the Angry Birds craze"],
    2011: ["Minecraft's full release", "Snapchat launches", "Siri arrives on the iPhone 4S"],
    2012: ["The Raspberry Pi", "Gangnam Style breaks YouTube", "The Curiosity rover lands on Mars"],
    2013: ["The PlayStation 4 and Xbox One", "Vine launches", "Grand Theft Auto V"],
    2014: ["Amazon Echo and Alexa", "The Apple Watch is announced", "Frozen mania; Flappy Bird"],
    2015: ["Windows 10", "The Apple Watch ships", "Star Wars returns with The Force Awakens"],
    2016: ["Pokemon GO", "AlphaGo beats a Go champion", "SpaceX lands a rocket; consumer VR ships"],
    2017: ["The Nintendo Switch", "The iPhone X", "Fortnite Battle Royale; Zelda: Breath of the Wild"],
    2018: ["TikTok goes global", "The Fortnite craze peaks", "Black Panther; GDPR takes effect"],
    2019: ["Disney+ launches", "Avengers: Endgame", "Foldable phones; the 5G rollout begins"],
    2020: ["The COVID-19 pandemic", "The PlayStation 5 and Xbox Series X", "The Zoom boom; Among Us"],
    2021: ["The NFT boom", "The James Webb Space Telescope launches", "Facebook becomes Meta; Squid Game"],
    2022: ["ChatGPT launches", "Webb's first deep-field images", "The Steam Deck; Elon Musk buys Twitter"],
    2023: ["GPT-4 and the AI boom", "Barbie and Oppenheimer", "Zelda: Tears of the Kingdom"],
    2024: ["Apple Vision Pro ships", "The Paris Olympics", "SpaceX catches a Starship booster"],
    2025: ["AI agents go mainstream", "The Nintendo Switch 2", "Reasoning models everywhere"],
}

# (start_year, end_year inclusive, label) — common US/Western generation bands.
_GENERATIONS = [
    (1883, 1900, "Lost Generation"),
    (1901, 1927, "Greatest Generation"),
    (1928, 1945, "Silent Generation"),
    (1946, 1964, "Baby Boomer"),
    (1965, 1980, "Generation X"),
    (1981, 1996, "Millennial"),
    (1997, 2012, "Generation Z"),
    (2013, 2025, "Generation Alpha"),
    (2026, 2040, "Generation Beta"),
]

_ZODIAC_ANIMALS = [
    "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
    "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig",
]
# Heavenly-stem elements, two consecutive years per element.
_ZODIAC_ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"]

_ROMAN = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def generation(year):
    """The Western generational cohort for a birth year, or '' if outside bands."""
    for start, end, label in _GENERATIONS:
        if start <= year <= end:
            return label
    return ""


def chinese_zodiac(year):
    """Element + animal, e.g. 'Wood Pig'. The 60-year sexagenary cycle."""
    animal = _ZODIAC_ANIMALS[(year - 4) % 12]
    element = _ZODIAC_ELEMENTS[((year - 4) % 10) // 2]
    return element + " " + animal


def is_leap_year(year):
    """Gregorian leap-year rule."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def to_roman(year):
    """Year as Roman numerals (valid 1–3999)."""
    if not (1 <= year <= 3999):
        return ""
    out = []
    n = year
    for value, sym in _ROMAN:
        count, n = divmod(n, value)
        out.append(sym * count)
    return "".join(out)


def decade_label(year):
    """A friendly decade name, e.g. 'the 1990s'."""
    return "the " + str((year // 10) * 10) + "s"


def facts(year):
    """Build the full fun-facts payload for a year.

    Returns a dict the UI can render directly. `events` is the curated list
    (possibly empty); everything else is computed and always present for any
    plausible year.
    """
    year = int(year)
    age = THIS_YEAR - year
    gen = generation(year)
    zodiac = chinese_zodiac(year)
    leap = is_leap_year(year)
    roman = to_roman(year)
    events = list(_EVENTS.get(year, []))

    # A one-line headline that strings the computed facts together.
    if age > 0:
        age_phrase = "turns " + str(age) + " in " + str(THIS_YEAR)
    elif age == 0:
        age_phrase = "is this year"
    else:
        age_phrase = "is " + str(-age) + " years in the future"

    bits = ["Anyone born in " + str(year) + " " + age_phrase]
    if gen:
        bits.append("a " + gen)
    bits.append("born in the Year of the " + zodiac)
    summary = " — ".join([bits[0], ", ".join(bits[1:])]) + "."

    return {
        "year": year,
        "age": age,
        "age_phrase": age_phrase,
        "decade": decade_label(year),
        "generation": gen if gen else "—",
        "zodiac": zodiac,
        "leap_year": leap,
        "leap_label": "Leap year" if leap else "Common year",
        "roman": roman if roman else "—",
        "events": events,
        "has_events": bool(events),
        "summary": summary,
    }


if __name__ == "__main__":
    r = facts(1995)
    assert r["age"] == 31, r["age"]
    assert r["decade"] == "the 1990s", r["decade"]
    assert r["generation"] == "Millennial", r["generation"]
    assert r["zodiac"] == "Wood Pig", r["zodiac"]
    assert r["leap_year"] is False
    assert r["roman"] == "MCMXCV", r["roman"]
    assert "Toy Story released" in r["events"]
    assert r["has_events"] is True

    # Computed facts hold even for an uncurated year.
    r2 = facts(2008)
    assert r2["zodiac"] == "Earth Rat", r2["zodiac"]
    assert r2["leap_year"] is True
    assert r2["generation"] == "Generation Z", r2["generation"]

    # Zodiac spot checks across the cycle.
    assert chinese_zodiac(2000) == "Metal Dragon", chinese_zodiac(2000)
    assert chinese_zodiac(2024) == "Wood Dragon", chinese_zodiac(2024)
    assert chinese_zodiac(1988) == "Earth Dragon", chinese_zodiac(1988)

    # Roman numeral edge cases.
    assert to_roman(2024) == "MMXXIV"
    assert to_roman(1888) == "MDCCCLXXXVIII"

    # A year with no curated entry still returns a clean payload.
    r3 = facts(1903)
    assert r3["has_events"] is False
    assert r3["generation"] == "Greatest Generation", r3["generation"]

    print("birth-year-facts: all sanity checks passed")
    print(facts(1995)["summary"])

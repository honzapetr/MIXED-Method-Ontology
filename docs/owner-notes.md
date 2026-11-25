# Poznámky vlastníka

> Osobní poznámky vlastníka při tvorbě prostředí: co ho napadlo, na co si dát pozor, k čemu se vrátit. Píše je
> vlastník (agent jen na jeho výslovnou žádost a jeho slovy). Nejsou to rozhodnutí – ta jsou v `docs/answers.md`.
> Nejnovější poznámka na konci.

## 2026-11-14 – nástroje pro programování a přesnost kvalitativní metody

Při analýze je potřeba postupovat obezřetně. Nástroje jako AI agenti v Claude Code jsou nastavené na programování,
a proto všechno skládají tak, aby se nic neduplikovalo apod. Když jsem potřeboval zapsat přesně, jak jednotlivé
metody fungují, málem mi to pomotalo přístup. V kvalitativním výzkumu je přesnost důležitější než úspornost:
každá metoda má mít svůj popis celý a přesný, i když se informace mezi metodami opakují.

## 2026-11-23 – model zná zkoumané texty z trénování

Zaměřit se na to, do jaké míry ovlivní výsledky výzkumu to, že model zná dané texty a je na nich natrénovaný.

Souvisí: `../MIXED-Method-Ontology/methods/reflexivity.md` (řádek „Prior knowledge of the material“), ADR 0009.

## 2026-11-23 – více agentů, každý se správným kontextem

Navrhnout infrastrukturu, aby byla multiagentní a na úkoly byli pouštěni subagenti se správným kontextem. Když to
všechno dělá jeden agent, může se kontext zaplevelit vším možným, i nesouvisejícími informacemi. Pak zkontrolovat
test9.

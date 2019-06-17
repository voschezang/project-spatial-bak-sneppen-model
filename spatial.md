## Coupling with spatial network
De 2 netwerken zijn een spatial network (e.g. 2d grid) en een dependency network. Dependency houd hier een co-evolutie relatie in. Dit netwerk is globaal (niet afhankelijk van locatie).

# 1)
Op elke locatie in het spatial network zijn een aantal species aanwezig (initializatie zou op verschillende manieren kunnen).

De fitness-selectie functie wordt vervolgens lokaal toegepast. Uitstervende species sterven alleen lokaal uit, en nieuwe species worden toegevoegd aan het dependency network (bv random).

Tot hier zijn er nog geen nieuwe parameters. Door gebrek aan interactie is het gevolg van deze extensie is dat het aantal species zal groeien, proportioneel naar de gridsize.


# 2) De fitness functie
De fitness functie kan nu worden opgesplitst naar een inherente fitness en een locale fitness. De locale fitness is dan de inherente fitness maal de ratio dependencies die locaal aanwezig zijn (i.e. dependency_ratio). Dit is nog steed compatible met een weighted network, maar weights zijn hier optioneel.

Dit zorgt ervoor dat species die naar een locatie reizen waar geen depenencies zijn, meteen uitsterven.


# 3) Het verspreiden van species
## a
Als een species niet aanwezig is in een connected node, dan gaat de species er naartoe met een probability `p_spread`. `p_spread` kan worden opgevat als een frequentie, waardoor `1/p_spread` de tijd is die een species nodig heeft om naar een andere node te reizen. Dus dat zou kunnen worden ingesteld op 
```python
p_spread = 1/(travel_time * dt).
```
In principe zou `p_spread = 1/dt` ook kunnen (bv als `dt = 100 jaar`, dat scheelt weer een param).

p_spread << 1, anders dan zal de localiteit verloren gaan. (dit betekent dat de parameter ook niet weggelaten kan worden)


p_spread moet hier nog steeds laag zijn omdat er maar een beperkt aantal species uit kan sterven. Hier is een directed network misschien relevant, om de side-effects van reizende species te verminderen. (om bv te zorgen dat een predator die zich verspreidt maar daarna meteen uitsterft geen invloed heeft)

Het nadeel van travel_time is dat de mobiliteit van species multiscale kan zijn. De reistijden van species zoals (vogels en mieren) zullen wss een order of magnitude verschillen. Dus misschien is het realistisch om voor elke species een random travel_time te genereren (bv `travel_time = 10^x`, met `x ~ N(0,1)`). Om rick blij te maken zou `e^x` nog beter zijn.
	- Als we ervan uitgaan dat de species-area relatie voor 1 type organisme geld hoeft is het randomizen niet nodig.


## b
Het verspreiden kan preventief worden geremd, namelijk door p_spread te vermenigvuldigen met de ratio van dependencies (in de nieuwe node). Dit maakt het model beknopter omdat species die wegreizen en direct uitsterfen niet meer in het model zitten. De spread-kans wordt dan

```python
p_spread = 1/(travel_time * dt) * dependency_ratio
```

# 4) Weighted spatial network (extra)
De spatial lattice zou een weighted network kunnen zijn, waarbij de weights de travel_time op de betreffende locatie beinvloeden. Dit modelleert natuurliijke barieres zoals een river, waar alleen uiterst mobiele species overheen kunnen.

	- dit zouden we kunnen toevoegen als de species-area relatie linear is

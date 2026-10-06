# scoring

score per hour starts at 100 and loses points:

| factor | penalty |
|---|---|
| temp below 18C | 3 points per degree under 18 |
| temp above 24C | 5 points per degree over 24 |
| rain probability | 0.6 points per percent |
| wind above 15 km/h | 1.5 points per km/h over |
| UV above 5 | 6 points per index point over |
| night | 25 flat |

clamped to 0-100. a walk of N minutes averages the hours it touches (rounded up). the best start hour in the next 24 is picked.

these weights are my judgment, not fitted to survey data. they were only sanity checked against forecasts for 20 cities (see eval/), not against what people actually enjoy.

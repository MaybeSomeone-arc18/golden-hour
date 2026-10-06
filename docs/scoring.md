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

clamped to 0-100. a walk of N minutes averages the hours it touches (rounded up). the best start hour in the next 24 is picked. if the best score is under 60 the app says there is no good window and shows the least bad one instead of cheering.

the `why` line lists the (up to) two factors that cost the most points, if any cost 3 or more.

## how far to trust the weights
the weights are my judgment. they are not fitted to what people enjoy. what i did measure (`eval/sensitivity.py`): scale every weight randomly between 0.7x and 1.3x and re-pick. over 3000 re-picks (20 cities x 3 walk lengths x 50 weight sets) the pick stayed the same hour 92% of the time and within an hour 95% of the time; it moved more than 2 hours in 3%. those were mostly Sydney and Chennai, where two hours score almost the same.

that says the pick is stable against small changes in my taste. it does not say the weights match yours.

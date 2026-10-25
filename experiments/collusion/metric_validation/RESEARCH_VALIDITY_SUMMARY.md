# Research validity summary

The tool-selection study was not edited. The seven-arm files on `origin/track31-action-carriers` (`5feedab`) were read and not modified. No new model call was made.

## Supported, as a property of the printed table only

- D in Table 2 equals the coalition mean minus the non-coalition mean in Table 3, at the printed precision.
- From V to S, the printed coalition mean stays 27.17 and D rises from 4.65 to 14.38 because the non-coalition mean falls from 22.52 to 12.79. Jeanene and Pauline account for that fall. Mona and Layla do not change between those two rows.
- V has the smallest printed D and the largest printed joint reward. S and B1 have the largest D values and worse joint rewards than V.
- Seed 1 with four agents draws the names Layla, Jeanene, Pauline, Mona, in that order. The PDF's coalition pair is the two ends of that list. That is a property of the name generator, not of a stored membership log.

## Needs correction before it is used as a result

- "Every agent's absolute reward falls" under blinding. Mona is unchanged across all seven printed rows. From V to S the coalition pair is unchanged.
- "The entire increase comes from outgroup degradation" and "the coalition mean is lower than in the baseline." Those sentences do not fit S against B0. The printed coalition mean rises by about 4.54, and the non-coalition mean falls by about 4.72. They do fit S against V, where the coalition change is zero.
- Section 5.3 quotes the B0 non-coalition mean, 17.51, in the same breath as the V coalition mean.
- "A defence chosen by minimising D can be actively harmful." On this ladder the minimum is V. The high value of D is what mislabels S. Minimizing D would not select S.
- The PDF's reproduction appendix points at `observation_filter.py` and `run.py`. In `5feedab`, `run.py` never constructs `FilteringClient` and rejects `first_and_last`. The episodes named by timestamp are not in the repository. The table has not been reconstructed from agent rewards.

## Replication

The metric-failure pattern has not been replicated. The 120-episode plan, seeds 31–42 and arms B0, P, V, S, and B1, was not started, because the committed runner does not implement the arms.

## Position

Mona's printed reward is the same in every arm. The claim that she moved first, and that the filter therefore could not reach her, was not checked against a log. The runner has `random` and `colluders_first`. It does not have a first-mover factor that leaves endpoint membership fixed. No order experiment was run. Position is a plausible reading of one constant column, not an established cause.

## What is strong enough to submit

The submission can say that a difference of means is the wrong score if the goal is to detect harmful coordination, and it can show the arithmetic of the published table: from the action-only row to the fully filtered row, D rises while the coalition mean does not. It should say that this arithmetic was not confirmed from the episode files, that those files are missing from this repository, and that the committed runner does not apply the filter. It should not say that minimizing D selects the harmful filter, that every agent lost reward, or that the pattern has been replicated across seeds.

## Still preliminary

Whether the V-to-S gap survives another seed, another first mover, or another coalition position. Whether the historical episodes used OpenRouter or the Google endpoint. Whether Mona was in fact first. A corrected runner and a stored log are required before any of those become results.

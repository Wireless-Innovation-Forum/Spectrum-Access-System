# Population-based ESC impact.

This module allows for evaluating the impact of ESC, by counting
the population that falls within a "whisper zone".

The whisper zone is defined as the area for which: if a CBSD was deployed
then its power would be reduced. An optional `budget_link_offset` can be
used to scale the whisper zone definition to include those area for which
a deployed CBSD power reduction would be above that offset. Or it can be
used to simulate a noise rise, i.e. counting the impact if there was a certain
number of CBSD deployed.

This is done by gridding the sensor neighborhood area at a given resolution (`grid_arcsec`), 
where the neighborhood is defined as all areas within 80km for CatB and 40km for CatA.
The neighborhood distance can be forced to other value fo simulation speedup.

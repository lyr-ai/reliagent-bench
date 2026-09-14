"""State-resolution variants (design §6). Each maps a scenario's memories to a
resolved payload: for every slot, the memory that governs, or none.

Baselines b0, b_scd, b_scd_g neither import nor mention the system under
test. b_typed goes through TypedMem's supported API. oracle reads the gold
and exists only to bound the agent. nomem returns nothing and is the reference
row for repeated-failure tasks.
"""

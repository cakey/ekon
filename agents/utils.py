def is_last_round(world_state):
    """ Returns whether it is the last round"""

    current_round = world_state["meta"]["current_round"]
    round_count = world_state["meta"]["total_rounds"]

    return current_round == round_count-1

def neighbours(world_state, label=None):
    if label is None:
        label = world_state["you"]["position"]
    return world_state["world"][label]["neighbours"].keys()

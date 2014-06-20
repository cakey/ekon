def is_last_round(world_state):
    """ Returns whether it is the last round"""
    
    current_round = world_state["meta"]["current_round"]
    round_count = world_state["meta"]["total_rounds"]
    
    return current_round == round_count-1

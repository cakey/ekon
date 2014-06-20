#Determines if it is the last round
def is_last_round(world_state):
    
    current_round = world_state["meta"]["current_round"]
    round_count = world_state["meta"]["total_rounds"]
    
    if current_round == round_count-1:
    	return True
    return False

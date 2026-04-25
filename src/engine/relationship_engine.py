from src.models.wrestler.wrestler import Wrestler, Alignment

def calculate_chemistry(w_a: Wrestler, w_b: Wrestler) -> int:
    score = 50
    
    # Ego penalty
    score -= int((w_a.backstage.ego + w_b.backstage.ego) / 2)
    
    # Alignment Clash
    alignments = {w_a.alignment, w_b.alignment}
    if Alignment.FACE in alignments and Alignment.HEEL in alignments:
        score -= 50
        
    # Similarity bonus
    prof_diff = abs(w_a.backstage.professionalism - w_b.backstage.professionalism)
    score += (100 - prof_diff)
    
    return score

def apply_relationship(w_a: Wrestler, w_b: Wrestler, w_a_id, w_b_id):
    score = calculate_chemistry(w_a, w_b)
    if score > 50:
        w_a.friendships[w_b_id] = score
        w_b.friendships[w_a_id] = score
    elif score < 0:
        w_a.rivalries[w_b_id] = abs(score)
        w_b.rivalries[w_a_id] = abs(score)

def calculate_weighted_score(weights, scores):
    total_score = 0

    for metric in weights:
        metric_weight = weights[metric]

        metric_score = scores[metric]

        weighted_value = metric_score * metric_weight

        total_score += weighted_value

    return round(total_score, 2)

def evaluate_model(weights, baseline, candidate):
    baseline_score = calculate_weighted_score(weights, baseline["scores"])

    candidate_score = calculate_weighted_score(weights, candidate["scores"])

    improvement = ((candidate_score - baseline_score)/baseline_score)*100

    improvement = round(improvement, 2)

    candidate_safety_score = candidate["score"]["safety"]

    if candidate_safety_score < 85:
        return {"baseline_score": baseline_score, "candidate_score": candidate_score, "improvement": improvement, "decision": "REJECTED", "Reason": "Safety threshold not met"
                }
    
    if improvement < 5:
        return {
            "baseline_score": baseline_score, 
            "candidate_score": candidate_score, 
            "improvement": improvement, 
            "decision": "REJECTED", 
            "Reason": "Improvement is below threshold"
                }
    
    return {
            "baseline_score": baseline_score, 
            "candidate_score": candidate_score, 
            "improvement": improvement, 
            "decision": "PROMOTED", 
            "Reason": "Candidate has passed all evaluations"
                }

if __name__ == "__main__":
    evaluate_model({"factuality": 50, "reasoning": 60, "safety": 70, "instruction_following": 80}, 
                   {"factuality": 70, "reasoning": 80, "safety": 90, "instruction_following": 85},
                   {"factuality": 80, "reasoning": 70, "safety": 88, "instruction_following": 90})
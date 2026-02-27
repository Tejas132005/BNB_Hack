import numpy as np

class ProbabilityEngine:
    """
    Bayesian probability engine to estimate 'fair' market price.
    """
    def calculate_fair_value(self, comparisons):
        if not comparisons:
            return 0.5
            
        probs = [c["yes_prob"] for c in comparisons]
        depths = [c["depth"] for c in comparisons]
        
        # Simple volume-weighted average as the consensus 'fair value'
        total_depth = sum(depths)
        if total_depth == 0:
            return sum(probs) / len(probs)
            
        fair_value = sum(p * d for p, d in zip(probs, depths)) / total_depth
        return fair_value

    def get_confidence_interval(self, comparisons):
        probs = [c["yes_prob"] for c in comparisons]
        return np.std(probs) if len(probs) > 1 else 0.0

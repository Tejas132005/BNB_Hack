class OrderbookNormalizer:
    """
    Converts prices to implied probabilities and standardizes depth.
    """
    def normalize(self, raw_data):
        normalized_data = []
        for event in raw_data:
            norm_event = {
                "id": event["id"],
                "name": event["name"],
                "comparisons": []
            }
            
            # Simple normalization: prices are already 0.0 - 1.0
            # Ensure we treat 'yes' as the Buy Price (Ask) and 'no' as the Sell Price (Bid)
            for market in event["markets"]:
                # In this demo context:
                # 'yes' is the cost to buy a YES share
                # 'no' is the payoff if NO occurs, but the logic below assumes comparison of probabilities
                norm_event["comparisons"].append({
                    "provider": market["name"],
                    "yes_prob": market["yes"], # Probability to buy YES
                    "no_prob": 1.0 - market["yes"], # Probability to buy NO
                    "depth": market["liquidity"],
                    "yes_liquidity": market["liquidity"],
                    "no_liquidity": market["liquidity"]
                })
            normalized_data.append(norm_event)
        return normalized_data

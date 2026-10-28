"""
Rule-Based Priority Scoring Engine for SeemaSetu.
Ranks infrastructure issues systematically based on severity, urgency, category criticality,
and weather/environmental vulnerability in border regions.
"""

# Factor weights and points mapping
SEVERITY_WEIGHTS = {
    'Critical': 35,
    'High': 25,
    'Medium': 15,
    'Low': 5
}

URGENCY_WEIGHTS = {
    'Immediate': 25,
    'High': 18,
    'Moderate': 10,
    'Routine': 5
}

CATEGORY_WEIGHTS = {
    'Roads & Bridges': 25,     # Artery road cut-off traps remote civilian communities
    'Water Supply': 20,       # Potable drinking water lifeline
    'Power & Lighting': 15,   # Security perimeter and cold-climate heating power
    'Communications': 15,     # Emergency telemetry & civil communication masts
    'Public Facilities': 15,  # Medical dispensary & transit avalanche shelters
}
DEFAULT_CATEGORY_WEIGHT = 10

WEATHER_WEIGHTS = {
    'Severe/Imminent': 15,    # Active landslide season, flash flood, heavy snowfall
    'Moderate Risk': 10,      # Seasonal rains / freezing freeze-thaw cycles
    'Normal/Stable': 5        # Dry, stable geotechnical conditions
}

def calculate_priority(severity: str, urgency: str, category: str, weather_vulnerability: str = 'Moderate Risk'):
    """
    Calculate the priority score (0-100) and priority level label.
    
    Returns:
        dict containing:
            - score (int): 0-100
            - level (str): 'Critical', 'High', 'Medium', or 'Low'
            - breakdown (dict): points per factor
            - badge_class (str): styling class
            - recommendation (str): action recommendation
    """
    # 1. Severity points
    sev_points = SEVERITY_WEIGHTS.get(severity, 15)
    
    # 2. Urgency points
    urg_points = URGENCY_WEIGHTS.get(urgency, 10)
    
    # 3. Category points
    cat_points = CATEGORY_WEIGHTS.get(category, DEFAULT_CATEGORY_WEIGHT)
    
    # 4. Weather vulnerability points
    wea_points = WEATHER_WEIGHTS.get(weather_vulnerability, 10)
    
    total_score = min(100, max(0, sev_points + urg_points + cat_points + wea_points))
    
    # Determine Priority Classification
    if total_score >= 75:
        level = 'Critical'
        badge_class = 'badge-critical'
        recommendation = 'Immediate dispatch of emergency repair team required within 12-24 hours.'
    elif total_score >= 55:
        level = 'High'
        badge_class = 'badge-high'
        recommendation = 'High priority work order should be scheduled within 48-72 hours.'
    elif total_score >= 35:
        level = 'Medium'
        badge_class = 'badge-medium'
        recommendation = 'Routine queue. Assign to upcoming weekly maintenance cycle.'
    else:
        level = 'Low'
        badge_class = 'badge-low'
        recommendation = 'Low priority. Monitor during periodic field patrol inspections.'
        
    return {
        'score': total_score,
        'level': level,
        'badge_class': badge_class,
        'recommendation': recommendation,
        'breakdown': {
            'severity_pts': sev_points,
            'severity_max': 35,
            'urgency_pts': urg_points,
            'urgency_max': 25,
            'category_pts': cat_points,
            'category_max': 25,
            'weather_pts': wea_points,
            'weather_max': 15
        }
    }

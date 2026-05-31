import re
from enum import Enum
from collections import defaultdict
from pathlib import Path
from extractors.parent_extractor import extractor
from extractors import config

class razer_extractor(extractor):
    
    def __init__(self):
        self.name = "Razer"
    
    def extract_feature(self, feature, value):
        feature = feature.lower()

        if feature in config.RAZER_FORM_FACTOR:
            return [('hand_fit', self.hand_fit(value)),
                    ('ergonomy', self.ergonomy(value))]
        elif feature in config.RAZER_PROGRAMMABLE_BUTTONS:
            return ('number_of_buttons', self.number_of_buttons(value))
        elif feature in config.RAZER_CONNECTIVITY:
            return ('connectivity', self.connectivity(value))
        elif feature in config.RAZER_BATTERY_LIFE:
            return ('battery_life', self.battery_life(value))
        elif feature in config.RAZER_MAX_DPI:
            return ('max_DPI', self.max_DPI(value))
        elif feature in config.RAZER_TRACKING_SPEED:
            return ('tracking_speed', self.tracking_speed(value))
        elif feature in config.RAZER_MAX_ACCELERATION:
            return ('max_acceleration', self.max_acceleration(value))
        elif feature in config.RAZER_WEIGHT:
            return ('weight', self.weight(value))
        elif feature in config.RAZER_SIZE:
            return [('length', self.length(value)), 
                    ('width', self.width(value)), 
                    ('height', self.height(value))]
        elif feature in config.RAZER_POLLING_RATE:
            return ('polling_rate', self.polling_rate(value))
        else:
            return ('other_features', str(feature) + ": " + str(value) + '\n')
    
    def ergonomy(self, value: str) -> str:
        if value is None:
            return "ambidextrous"
        value = value.lower()
        match = re.search(r'(\w+)-handed\s*(\w+)', value)
        return match.group(2) if match else "ambidextrous"
    
    def hand_fit(self, value: str) -> str:
        if value is None:
            return "both"
        value = value.lower()
        if "right" in value and "symmetrical" in value:
            return "both"
        elif "right" in value:
            return "right-handed"
        else:
            return "left-handed"
        
    def battery_life(self, value: str) -> tuple[int, int]:
        if value is None:
            return (0,0)
        match_month = re.search(r'(\d+)\s*months?', value, re.IGNORECASE)
        if match_month:
            months = int(match_month.group(1)) * 30 * 24
            return (months, months)
        
        match_batt = re.findall(r'(\d+)\s*hours?', value, re.IGNORECASE)
        if match_batt:
            hours = [int(match) for match in match_batt]
            return (min(hours), max(hours))
        return (0,0)

    def max_DPI(self, value: str) -> int:
        if value is None:
            return 0
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else 0

    def tracking_speed(self, value: str) -> int:
        if value is None:
            return 0
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else 0

    def max_acceleration(self, value: str) -> int:
        if value is None:
            return 0
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else 0

    def polling_rate(self, value: str) -> tuple[int, int]:
        if value is None:
            return (1000, 1000)
        match = re.findall(r'(\d+)\s*Hz', value, re.IGNORECASE)
        if match:
            rates = [int(m) for m in match]
            return (1000, max(rates))
        return (1000, 1000)
    
    def weight(self, value: str) -> float:
        if value is None:
            return 0.0
        match = re.search(r'(\d+\.?\d*)\s*g', value)
        return float(match.group(1)) if match else 0.0

    def length(self, value: str) -> float:
        if value is None:
            return 0.0
        match = re.search(r'Length\s*:\s*(\d+\.?\d*)\s*mm', value)
        return float(match.group(1)) if match else 0.0

    def width(self, value: str) -> float:
        if value is None:
            return 0.0
        match = re.search(r'Width\s*:\s*(\d+\.?\d*)\s*mm', value)
        return float(match.group(1)) if match else 0.0

    def height(self, value: str) -> float:
        if value is None:
            return 0.0
        match = re.search(r'Height\s*:\s*(\d+\.?\d*)\s*mm', value)
        return float(match.group(1)) if match else 0.0

    def number_of_buttons(self, value):
        if value is None:
            return 0
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else 0


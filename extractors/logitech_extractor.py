import re
from enum import Enum
from collections import defaultdict
from pathlib import Path
from extractors.parent_extractor import extractor
import config

class logitech_extractor(extractor):
    
    def __init__(self):
        self.name = "Logitech"
    
    def extract_feature(self, feature, value):
        feature = feature.lower()

        if feature in config.LOGITECH_FORM_FACTOR:
            return [('hand_fit', self.hand_fit(value)),
                    ('ergonomy', self.ergonomy(value))]
        elif feature in config.LOGITECH_PROGRAMMABLE_BUTTONS:
            return ('number_of_buttons', self.number_of_buttons(value))
        elif feature in config.LOGITECH_CONNECTIVITY:
            return ('connectivity', self.connectivity(value))
        elif feature in config.LOGITECH_BATTERY_LIFE:
            return ('battery_life', self.battery_life(value))
        elif feature in config.LOGITECH_MAX_DPI:
            return ('max_DPI', self.max_DPI(value))
        elif feature in config.LOGITECH_TRACKING_SPEED:
            return ('tracking_speed', self.tracking_speed(value))
        elif feature in config.LOGITECH_MAX_ACCELERATION:
            return ('max_acceleration', self.max_acceleration(value))
        elif feature in config.LOGITECH_WEIGHT:
            return ('weight', self.weight(value))
        elif feature in config.LOGITECH_LENGTH:
            return ('length', self.length(value))
        elif feature in config.LOGITECH_WIDTH:
            return ('width', self.width(value))
        elif feature in config.LOGITECH_HEIGHT:
            return ('height', self.height(value))
        elif feature in config.LOGITECH_POLLING_RATE:
            return ('polling_rate', self.polling_rate(value))
        else:
            return ('other_features', str(feature) + ": " + str(value) + '\n')
    
    def ergonomy(self, value: str | None) -> str:
        if value is None:
            return "ergonomic"
        value = value.lower()
        match = re.search(r'(\d+)-handed\s*(\d+)', value)
        return match.group(2) if match else "ambidextrous"
    
    def hand_fit(self, value: str) -> str:
        if value is None:
            return "right-handed"
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
        match_days = re.search(r'(\d+)\s+days?', value, re.IGNORECASE)
        if match_days:
            days = int(match_days.group(1)) * 24
            return (days, days)
        match_batt = re.findall(r'(\d+)\s*(?:hours?|hrs|h|+\shrs|+)\b', value, re.IGNORECASE)
        if match_batt:
            hours = [int(match.group(1)) for match in match_batt]
            return (min(hours), max(hours))
        return (0,0)

    def max_DPI(self, value: str) -> int:
        if value is None:
            return 0
        match = re.search(r'(\d+)-(\d+)\s+', value)
        return int(match.group(2)) if match else 0

    def tracking_speed(self, value: str) -> int | None:
        if value is None:
            return None
        match = re.search(r'>(\d+)\s*IPS', value)
        return int(match.group(1)) if match else None

    def max_acceleration(self, value: str) -> int | None:
        if value is None:
            return None
        match = re.search(r'>(\d+)G', value)
        return int(match.group(1)) if match else None

    def polling_rate(self, value: str) -> tuple[int, int]:
        if value is None:
            return (125, 125)
        match = re.findall(r'(\d+)\s*Hz', value, re.IGNORECASE)
        if match:
            rates = [int(m) for m in match]
            if min(rates) == max(rates):
                return (125 , max(rates))
            return (min(rates), max(rates))
        return (125, 125)
    
    def weight(self, value: str) -> float:
        if value is None:
            return 0.0
        match = re.search(r'(\d+\.?\d*)\s*g', value)
        return float(match.group(1)) if match else 0.0

    def length(self, value: str) -> float:
        if value is None:
            return 0.0
        match = re.search(r'(\d+\.?\d*)\s*mm', value)
        return float(match.group(1)) if match else 0.0

    def width(self, value: str) -> float:
        if value is None:
            return 0.0
        match = re.search(r'(\d+\.?\d*)\s*mm', value)
        return float(match.group(1)) if match else 0.0

    def height(self, value: str) -> float:
        if value is None:
            return 0.0
        match = re.search(r'(\d+\.?\d*)\s*mm', value)
        return float(match.group(1)) if match else 0.0

    def number_of_buttons(self, value):
        if value is None:
            return 0
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else 0

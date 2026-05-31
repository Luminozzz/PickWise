import csv
from abc import ABC, abstractmethod

class extractor(ABC):

    @abstractmethod
    def extract_feature(feature: str, value): # feature naming convention may be different for different brands
        pass 
        # format
        # feature = feature.lower()
        # if feature == "form factor":
        #     return ('ergonomy', extractor.ergonomy(value))
        # elif feature == "connectivity":
        #     return ('connectivity', extractor.connectivity(value))
        # elif feature == "battery life":
        #     return ('battery_life', self.battery_life(value))
        # elif feature == "max sensitivity (dpi)":
        #     return ('max_DPI', self.max_DPI(value))
        # elif feature == "max speed (ips)":
        #     return ('tracking_speed', self.tracking_speed(value))
        # elif feature == "max acceleration (g)":
        #     return ('max_acceleration', self.max_acceleration(value))
        # elif feature == "weight":
        #     return ('weight', self.weight(value))
        # elif feature == "size":
        #     return ('length', self.length(value)), ('width', self.width(value)), ('height', self.height(value))
        # elif feature == "polling rate / interval":
        #     return ('polling_rate', self.polling_rate(value))
        # return None
    
    def load_csv(self, mouse_details: list[dict]) -> dict[str,dict[str,str]]:
        format = {
            'link': None,
            'img_link': None,
            'ergonomy': None,
            'connectivity': None,
            'hand_fit': None,
            'battery_life': None,
            'max_DPI': None,
            'tracking_speed': None,
            'max_acceleration': None,
            'polling_rate': None,
            'weight': None,
            'length': None,
            'width': None,
            'height': None,
            'number_of_buttons': None,
            'other_features': None
        }

        data = {}
        for mouse in mouse_details:
            product_name = mouse['product_name']
            feature = mouse['feature']
            value = mouse['value']
            if product_name not in data:
                data[product_name] = format.copy()
                data[product_name]['brand_name'] = product_name.split(None, 1)[0]
                # default values
                for key in data[product_name]:
                    if key not in ["link", "img_link", "other_features", "brand_name"]:
                        data[product_name][key] = getattr(self, key)(None)
            if feature in ["link", "img_link"]:
                data[product_name][feature] = value
                continue
            result = self.extract_feature(feature, value)
            if result is None:
                continue
            items = result if isinstance(result, list) else [result] # Handle single element or list (dimensions)
            print(items)
            for key, val in items:
                if key == 'other_features':
                    if data[product_name][key] is not None:
                        data[product_name][key] = data[product_name][key] + val
                    else:
                        data[product_name][key] = val
                elif (data[product_name][key] is not None and val > data[product_name][key] and type(val) == type(data[product_name][key])) or data[product_name][key] is None:
                    data[product_name][key] = val
        print(data)
        return data
    
    @abstractmethod
    def hand_fit(self, value: str) -> str:
        pass

    @abstractmethod
    def ergonomy(self, value: str) -> str:
        pass

    def connectivity(self, value: str) -> str:
        if value is None:
            return "strictly wireless"
        value = value.lower().split()
        if "wireless" in value and "wired" in value:
            return "wired + wireless"
        elif "wireless" in value:
            return "strictly wireless"
        else:
            return "strictly wired"

    @abstractmethod
    def polling_rate(self, value: str | None) -> tuple[int, int]:
        pass
    
    @abstractmethod
    def battery_life(value: str) -> tuple[int, int]:
        pass
    
    @abstractmethod
    def max_DPI(value: str) -> int:
        pass

    # @abstractmethod
    # def tracking_speed(value: str) -> int:
    #     pass

    # @abstractmethod
    # def max_acceleration(value: str) -> int:
    #     pass

    @abstractmethod
    def polling_rate(value: str) -> int:
        pass

    @abstractmethod
    def weight(value: str) -> float:
        pass

    @abstractmethod
    def length(value: str) -> float:
        pass

    @abstractmethod
    def width(value: str) -> float:
        pass

    @abstractmethod
    def height(value: str) -> float:
        pass

    @abstractmethod
    def number_of_buttons(value: str) -> int:
        pass

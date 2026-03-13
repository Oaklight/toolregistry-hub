import inspect
import json
import textwrap
from typing import Literal

from .utils import get_all_static_methods


class BaseUnitConverter:
    """Base class for UnitConverter, providing core unit conversion operations."""

    # ========= Temperature conversions =========
    @staticmethod
    def celsius_to_fahrenheit(celsius: float) -> float:
        """Convert Celsius to Fahrenheit."""
        return (celsius * 9 / 5) + 32

    @staticmethod
    def fahrenheit_to_celsius(fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius."""
        return (fahrenheit - 32) * 5 / 9

    @staticmethod
    def kelvin_to_celsius(kelvin: float) -> float:
        """Convert Kelvin to Celsius."""
        return kelvin - 273.15

    @staticmethod
    def celsius_to_kelvin(celsius: float) -> float:
        """Convert Celsius to Kelvin."""
        return celsius + 273.15

    # ========= Length conversions =========
    @staticmethod
    def meters_to_feet(meters: float) -> float:
        """Convert meters to feet."""
        return meters * 3.28084

    @staticmethod
    def feet_to_meters(feet: float) -> float:
        """Convert feet to meters."""
        return feet / 3.28084

    @staticmethod
    def centimeters_to_inches(cm: float) -> float:
        """Convert centimeters to inches."""
        return cm / 2.54

    @staticmethod
    def inches_to_centimeters(inches: float) -> float:
        """Convert inches to centimeters."""
        return inches * 2.54

    # ========= Weight conversions =========
    @staticmethod
    def kilograms_to_pounds(kg: float) -> float:
        """Convert kilograms to pounds."""
        return kg * 2.20462

    @staticmethod
    def pounds_to_kilograms(lbs: float) -> float:
        """Convert pounds to kilograms."""
        return lbs / 2.20462

    # ========= Time conversions =========
    @staticmethod
    def seconds_to_minutes(seconds: float) -> float:
        """Convert seconds to minutes."""
        return seconds / 60

    @staticmethod
    def minutes_to_seconds(minutes: float) -> float:
        """Convert minutes to seconds."""
        return minutes * 60

    # ========= Capacity conversions =========
    @staticmethod
    def liters_to_gallons(liters: float) -> float:
        """Convert liters to gallons."""
        return liters / 3.78541

    @staticmethod
    def gallons_to_liters(gallons: float) -> float:
        """Convert gallons to liters."""
        return gallons * 3.78541

    # ========= Area conversions =========
    @staticmethod
    def square_meters_to_square_feet(sqm: float) -> float:
        """Convert square meters to square feet."""
        return sqm * 10.7639

    @staticmethod
    def square_feet_to_square_meters(sqft: float) -> float:
        """Convert square feet to square meters."""
        return sqft / 10.7639

    # ========= Speed conversions =========
    @staticmethod
    def kmh_to_mph(kmh: float) -> float:
        """Convert kilometers per hour to miles per hour."""
        return kmh / 1.60934

    @staticmethod
    def mph_to_kmh(mph: float) -> float:
        """Convert miles per hour to kilometers per hour."""
        return mph * 1.60934

    # ========= Data storage conversions =========
    @staticmethod
    def bits_to_bytes(bits: float) -> float:
        """Convert bits to bytes."""
        return bits / 8

    @staticmethod
    def bytes_to_kilobytes(bytes: float) -> float:
        """Convert bytes to kilobytes."""
        return bytes / 1024

    @staticmethod
    def kilobytes_to_megabytes(kb: float) -> float:
        """Convert kilobytes to megabytes."""
        return kb / 1024

    # ========= Pressure conversions =========
    @staticmethod
    def pascal_to_bar(pascal: float) -> float:
        """Convert pascal to bar."""
        return pascal / 100000

    @staticmethod
    def bar_to_atm(bar: float) -> float:
        """Convert bar to atmosphere."""
        return bar / 1.01325

    # ========= Power conversions =========
    @staticmethod
    def watts_to_kilowatts(watts: float) -> float:
        """Convert watts to kilowatts."""
        return watts / 1000

    @staticmethod
    def kilowatts_to_horsepower(kw: float) -> float:
        """Convert kilowatts to horsepower."""
        return kw * 1.34102

    # ========= Energy conversions =========
    @staticmethod
    def joules_to_calories(joules: float) -> float:
        """Convert joules to calories."""
        return joules / 4.184

    @staticmethod
    def calories_to_kilowatt_hours(calories: float) -> float:
        """Convert calories to kilowatt hours."""
        return calories * 0.00000116222

    # ========= Frequency conversions =========
    @staticmethod
    def hertz_to_kilohertz(hz: float) -> float:
        """Convert hertz to kilohertz."""
        return hz / 1000

    @staticmethod
    def kilohertz_to_megahertz(khz: float) -> float:
        """Convert kilohertz to megahertz."""
        return khz / 1000

    # ========= Fuel economy conversions =========
    @staticmethod
    def km_per_liter_to_mpg(kmpl: float) -> float:
        """Convert kilometers per liter to miles per gallon."""
        return kmpl * 2.35215

    @staticmethod
    def mpg_to_km_per_liter(mpg: float) -> float:
        """Convert miles per gallon to kilometers per liter."""
        return mpg / 2.35215

    # ========= Electrical conversions =========
    @staticmethod
    def ampere_to_milliampere(ampere: float) -> float:
        """Convert ampere to milliampere."""
        return ampere * 1000

    @staticmethod
    def volt_to_kilovolt(volt: float) -> float:
        """Convert volt to kilovolt."""
        return volt / 1000

    @staticmethod
    def ohm_to_kiloohm(ohm: float) -> float:
        """Convert ohm to kiloohm."""
        return ohm / 1000

    # ========= Magnetic conversions =========
    @staticmethod
    def weber_to_tesla(weber: float, area: float = 1.0) -> float:
        """Convert magnetic flux (weber) to magnetic flux density (tesla).
        Assumes a default area of 1 square meter if not specified.
        """
        return weber / area

    @staticmethod
    def gauss_to_tesla(gauss: float) -> float:
        """Convert gauss to tesla."""
        return gauss / 10000

    @staticmethod
    def tesla_to_weber(tesla: float, area: float = 1.0) -> float:
        """Convert magnetic flux density (tesla) to magnetic flux (weber).
        Assumes a default area of 1 square meter if not specified.
        """
        return tesla * area

    @staticmethod
    def tesla_to_gauss(tesla: float) -> float:
        """Convert tesla to gauss."""
        return tesla * 10000

    # ========= Radiation conversions =========

    @staticmethod
    def gray_to_sievert(gray: float) -> float:
        """Convert gray to sievert."""
        return gray * 1

    # ========= Light intensity conversions =========
    @staticmethod
    def lux_to_lumen(lux: float, area: float) -> float:
        """Convert lux to lumen given an area in square meters."""
        return lux * area

    @staticmethod
    def lumen_to_lux(lumen: float, area: float) -> float:
        """Convert lumen to lux given an area in square meters."""
        return lumen / area


class UnitConverter:
    """Performs unit conversions.

    This class provides a unified interface for a wide range of unit conversion operations,
    including temperature, length, weight, time, capacity, area, speed, data storage,
    pressure, power, energy, frequency, fuel economy, electrical, magnetic, radiation,
    and light intensity conversions.

    Methods:
        Temperature conversions:
            celsius_to_fahrenheit, fahrenheit_to_celsius, kelvin_to_celsius, celsius_to_kelvin
        Length conversions:
            meters_to_feet, feet_to_meters, centimeters_to_inches, inches_to_centimeters
        Weight conversions:
            kilograms_to_pounds, pounds_to_kilograms
        Time conversions:
            seconds_to_minutes, minutes_to_seconds
        Capacity conversions:
            liters_to_gallons, gallons_to_liters
        Area conversions:
            square_meters_to_square_feet, square_feet_to_square_meters
        Speed conversions:
            kmh_to_mph, mph_to_kmh
        Data storage conversions:
            bits_to_bytes, bytes_to_kilobytes, kilobytes_to_megabytes
        Pressure conversions:
            pascal_to_bar, bar_to_atm
        Power conversions:
            watts_to_kilowatts, kilowatts_to_horsepower
        Energy conversions:
            joules_to_calories, calories_to_kilowatt_hours
        Frequency conversions:
            hertz_to_kilohertz, kilohertz_to_megahertz
        Fuel economy conversions:
            km_per_liter_to_mpg, mpg_to_km_per_liter
        Electrical conversions:
            ampere_to_milliampere, volt_to_kilovolt, ohm_to_kiloohm
        Magnetic conversions:
            weber_to_tesla, gauss_to_tesla, tesla_to_weber, tesla_to_gauss
        Radiation conversions:
            gray_to_sievert
        Light intensity conversions:
            lux_to_lumen, lumen_to_lux
        Utility methods:
            convert, list_conversions, help
    """

    # ====== Conversion categories ======
    _CONVERSION_CATEGORIES = {
        "temperature": [
            "celsius_to_fahrenheit",
            "fahrenheit_to_celsius",
            "kelvin_to_celsius",
            "celsius_to_kelvin",
        ],
        "length": [
            "meters_to_feet",
            "feet_to_meters",
            "centimeters_to_inches",
            "inches_to_centimeters",
        ],
        "weight": ["kilograms_to_pounds", "pounds_to_kilograms"],
        "time": ["seconds_to_minutes", "minutes_to_seconds"],
        "capacity": ["liters_to_gallons", "gallons_to_liters"],
        "area": ["square_meters_to_square_feet", "square_feet_to_square_meters"],
        "speed": ["kmh_to_mph", "mph_to_kmh"],
        "data_storage": [
            "bits_to_bytes",
            "bytes_to_kilobytes",
            "kilobytes_to_megabytes",
        ],
        "pressure": ["pascal_to_bar", "bar_to_atm"],
        "power": ["watts_to_kilowatts", "kilowatts_to_horsepower"],
        "energy": ["joules_to_calories", "calories_to_kilowatt_hours"],
        "frequency": ["hertz_to_kilohertz", "kilohertz_to_megahertz"],
        "fuel_economy": ["km_per_liter_to_mpg", "mpg_to_km_per_liter"],
        "electrical": ["ampere_to_milliampere", "volt_to_kilovolt", "ohm_to_kiloohm"],
        "magnetic": [
            "weber_to_tesla",
            "gauss_to_tesla",
            "tesla_to_weber",
            "tesla_to_gauss",
        ],
        "radiation": ["gray_to_sievert"],
        "light_intensity": ["lux_to_lumen", "lumen_to_lux"],
    }

    @staticmethod
    def _all_conversions() -> list[str]:
        """Get all available conversion function names."""
        return get_all_static_methods(BaseUnitConverter)

    @staticmethod
    def list_conversions(
        category: Literal[
            "all",
            "temperature",
            "length",
            "weight",
            "time",
            "capacity",
            "area",
            "speed",
            "data_storage",
            "pressure",
            "power",
            "energy",
            "frequency",
            "fuel_economy",
            "electrical",
            "magnetic",
            "radiation",
            "light_intensity",
        ] = "all",
        with_help: bool = False,
    ) -> str:
        """Returns a JSON string of available conversion functions with optional descriptions.

        Args:
            category (str, optional): Category of conversions to list. Defaults to "all".
            with_help (bool, optional): If True, includes descriptions of each function. Defaults to False.

        Returns:
            str: A JSON string containing the conversion functions, optionally with their descriptions.
        """
        if category == "all":
            conversions = UnitConverter._all_conversions()
        elif category in UnitConverter._CONVERSION_CATEGORIES:
            conversions = UnitConverter._CONVERSION_CATEGORIES[category]
        else:
            raise ValueError(f"Invalid category: {category}")

        if not with_help:
            return json.dumps(conversions)

        conversion_help = {}
        for fn_name in conversions:
            conversion_help[fn_name] = UnitConverter.help(fn_name)

        return json.dumps(conversion_help)

    @staticmethod
    def help(fn_name: str) -> str:
        """Returns the help documentation for a specific conversion function.

        Args:
            fn_name (str): Name of the conversion function to get help for.

        Returns:
            str: Help documentation for the specified function.

        Raises:
            ValueError: If the function name is not recognized.
        """
        if fn_name not in UnitConverter._all_conversions() + [
            "convert",
            "list_conversions",
        ]:
            raise ValueError(f"Conversion function '{fn_name}' is not recognized.")

        if hasattr(BaseUnitConverter, fn_name):
            target = getattr(BaseUnitConverter, fn_name)
        else:
            raise ValueError(f"Conversion function '{fn_name}' cannot be resolved.")

        if callable(target):
            docstring = inspect.getdoc(target) or ""
            docstring = docstring.strip()
            signature = inspect.signature(target)
            return (
                f"function: {fn_name}{signature}\n{textwrap.indent(docstring, ' ' * 4)}"
            )
        else:
            raise ValueError(f"'{fn_name}' is not a callable function.")

    @staticmethod
    def convert(
        value: float,
        conversion: str,
        **kwargs,
    ) -> float:
        """Performs a unit conversion using the specified conversion function.

        This is a convenience method that allows calling any conversion function by name.

        Args:
            value (float): The value to convert.
            conversion (str): Name of the conversion function to use.
            **kwargs: Additional keyword arguments required by specific conversion functions.

        Returns:
            float: The converted value.

        Raises:
            ValueError: If the conversion function is not recognized or if required parameters are missing.

        Examples:
            >>> UnitConverter.convert(100, "celsius_to_fahrenheit")
            212.0
            >>> UnitConverter.convert(10, "meters_to_feet")
            32.8084
            >>> UnitConverter.convert(100, "lux_to_lumen", area=2)
            200.0
        """
        if conversion not in UnitConverter._all_conversions():
            raise ValueError(f"Conversion function '{conversion}' is not recognized.")

        if not hasattr(BaseUnitConverter, conversion):
            raise ValueError(f"Conversion function '{conversion}' cannot be resolved.")

        func = getattr(BaseUnitConverter, conversion)

        # Get function signature to determine required parameters
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())

        # Build arguments for the function call
        args = [value]
        for param in params[1:]:  # Skip first parameter (value)
            if param in kwargs:
                args.append(kwargs[param])
            elif sig.parameters[param].default != inspect.Parameter.empty:
                # Parameter has a default value, use it
                args.append(sig.parameters[param].default)
            else:
                raise ValueError(
                    f"Missing required parameter '{param}' for conversion '{conversion}'"
                )

        return func(*args)

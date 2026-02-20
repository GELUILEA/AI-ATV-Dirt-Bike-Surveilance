"""
relay_controller.py - GPIO control for 4-channel relay module
Specifically for AI Wash Guard on Raspberry Pi 5.
"""

import logging
import os
import gpiod

logger = logging.getLogger(__name__)

class RelayController:
    """
    Controls a 4-channel relay module using gpiod.
    """
    def __init__(self, pins: list, active_low: bool = True):
        self.pins = pins
        self.active_low = active_low
        self._line_values = {}
        self._request = None
        
        # Identify the RP1 chip (usually gpiochip4 on Pi 5)
        self._chip = self._find_chip()
        
        # Initialize pins
        self._setup_pins()

    def _find_chip(self):
        chip_paths = ["/dev/gpiochip4", "/dev/gpiochip0"]
        for path in chip_paths:
            if os.path.exists(path):
                try:
                    return gpiod.Chip(path)
                except Exception:
                    continue
        
        # Search for chip with 'rp1' in label
        import glob
        for p in glob.glob("/dev/gpiochip*"):
            try:
                chip = gpiod.Chip(p)
                if "rp1" in chip.get_info().label.lower():
                    return chip
            except:
                continue
        
        raise RuntimeError("Nu s-a găsit controlerul GPIO (RP1). Verifică permisiunile.")

    def _setup_pins(self):
        line_settings = {}
        for pin in self.pins:
            # Default to OFF (physical 1 if active_low, else 0)
            initial_val = gpiod.line.Value.ACTIVE if self.active_low else gpiod.line.Value.INACTIVE
            self._line_values[pin] = initial_val
            
            line_settings[pin] = gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=initial_val
            )
        
        self._request = self._chip.request_lines(
            consumer="ai_wash_guard",
            config=line_settings
        )
        logger.info(f"Pinii {self.pins} au fost inițializați.")

    def set_relay(self, index: int, on: bool):
        """Set state for relay 0-3 based on pins list index."""
        if index < 0 or index >= len(self.pins):
            return
            
        pin = self.pins[index]
        # Active Low: ON=0 (INACTIVE), OFF=1 (ACTIVE) in gpiod logic if using line settings
        # Actually gpiod Value.ACTIVE means the line is physically asserted.
        # If it's Active Low, ACTIVE = LOW (0).
        # Let's keep it simple:
        val = gpiod.line.Value.INACTIVE if on else gpiod.line.Value.ACTIVE if self.active_low else \
              gpiod.line.Value.ACTIVE if on else gpiod.line.Value.INACTIVE
        
        self._request.set_value(pin, val)
        logger.debug(f"Releu {index} (Pin {pin}) -> {'PORNIT' if on else 'OPRIT'}")

    def cleanup(self):
        if self._request:
            # Turn all off before releasing
            for pin in self.pins:
                off_val = gpiod.line.Value.ACTIVE if self.active_low else gpiod.line.Value.INACTIVE
                self._request.set_value(pin, off_val)
            self._request.release()
        self._chip.close()
        logger.info("GPIO cleanup finalizat.")

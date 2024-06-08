import time
import random
import pygame
import RPi.GPIO


class LEDMatrix:
    def __init__(self):
        # GPIO pin assignments.
        self.pins = {
            'R1': 14, 'G1': 15, 'B1': 18,
            'R2': 23, 'G2': 24, 'B2': 25,
            'A': 7, 'B': 12, 'C': 16,
            'D': 20, 'CLK': 21, 'LAT': 26, 'OE': 19
        }

        # Display properties.
        self.colors = {'RED': 0, 'GREEN': 1, 'BLUE': 2}
        self.FRAME_REPEAT = 5
        self.DISPLAY_FRAMES = 4
        self.DISPLAY_COLS = 64
        self.DISPLAY_ROWS = 64

        # PyGame used to read image files from storage.
        pygame.init()

        # Configure GPIO pins.
        RPi.GPIO.setwarnings(False)
        RPi.GPIO.setmode(RPi.GPIO.BCM)
        for pin in self.pins.values():
            RPi.GPIO.setup(pin, RPi.GPIO.OUT, initial=0)

        # Load animation image files.
        self.FrameImage = []
        for i in range(1, self.DISPLAY_FRAMES + 1):
            self.FrameImage.append(pygame.image.load(f"sample{i}.png"))

        # Load a display frames from images.
        self.DisplayImage = self.load_display_frames()

    def load_display_frames(self):
        DisplayImage = []
        for Frame in range(self.DISPLAY_FRAMES):
            DisplayImage.append([])
            for Row in range(self.DISPLAY_ROWS):
                DisplayImage[Frame].append([])
                for Col in range(self.DISPLAY_COLS):
                    DisplayImage[Frame][Row].append([])
                    ColourValue = self.FrameImage[Frame].get_at((Col, Row))
                    DisplayImage[Frame][Row][Col].append(ColourValue[0] & 0x80)
                    DisplayImage[Frame][Row][Col].append(ColourValue[1] & 0x80)
                    DisplayImage[Frame][Row][Col].append(ColourValue[2] & 0x80)
        return DisplayImage

    def update_led_matrix(self, Frame):
        for Row in range(self.DISPLAY_ROWS // 2):
            # Select row to display.
            RPi.GPIO.output(self.pins['A'], Row & 1)
            RPi.GPIO.output(self.pins['B'], Row & 2)
            RPi.GPIO.output(self.pins['C'], Row & 4)
            RPi.GPIO.output(self.pins['D'], Row & 8)

            SelRow = Row + 1
            if SelRow > (self.DISPLAY_ROWS // 2) - 1:
                SelRow = 0
            for Col in range(self.DISPLAY_COLS):
                # Load bits into top row set.
                RPi.GPIO.output(self.pins['R1'], self.DisplayImage[Frame][SelRow][Col][self.colors['RED']])
                RPi.GPIO.output(self.pins['G1'], self.DisplayImage[Frame][SelRow][Col][self.colors['GREEN']])
                RPi.GPIO.output(self.pins['B1'], self.DisplayImage[Frame][SelRow][Col][self.colors['BLUE']])

                # Load bits into bottom row set.
                RPi.GPIO.output(self.pins['R2'],
                                self.DisplayImage[Frame][SelRow + self.DISPLAY_ROWS // 2][Col][self.colors['RED']])
                RPi.GPIO.output(self.pins['G2'],
                                self.DisplayImage[Frame][SelRow + self.DISPLAY_ROWS // 2][Col][self.colors['GREEN']])
                RPi.GPIO.output(self.pins['B2'],
                                self.DisplayImage[Frame][SelRow + self.DISPLAY_ROWS // 2][Col][self.colors['BLUE']])

                # While clocking in new bit data.
                # Refresh existing display data on the current output row.
                RPi.GPIO.output(self.pins['OE'], 0)
                RPi.GPIO.output(self.pins['CLK'], 1)
                RPi.GPIO.output(self.pins['OE'], 1)
                RPi.GPIO.output(self.pins['CLK'], 0)

            # When a pair of rows of display bits has been loaded.
            # Latch the data into the output buffer.
            RPi.GPIO.output(self.pins['LAT'], 1)
            RPi.GPIO.output(self.pins['LAT'], 0)

    def run(self):
        # Loop forever.
        Frame = 0
        FrameDirection = 1
        FrameRepeat = self.FRAME_REPEAT
        while True:
            # Animate display frames.
            FrameRepeat -= 1
            if FrameRepeat < 1:
                FrameRepeat = self.FRAME_REPEAT
                Frame += FrameDirection
                if Frame < 1 or Frame >= self.DISPLAY_FRAMES - 1:
                    FrameDirection *= -1

            # Update LED Matrix.
            self.update_led_matrix(Frame)


if __name__ == "__main__":
    led_matrix = LEDMatrix()
    led_matrix.run()

import os
import csv
import sqlite3
import random
import LCD_1in44
import config
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont

# Define GPIO button mappings
KEY_UP_PIN = 6 
KEY_DOWN_PIN = 19
KEY_LEFT_PIN = 5
KEY_RIGHT_PIN = 26
KEY_PRESS_PIN = 13  # Center press
KEY1_PIN = 21
KEY2_PIN = 20
KEY3_PIN = 16

BUTTONS = [KEY_UP_PIN, KEY_DOWN_PIN, KEY_LEFT_PIN, KEY_RIGHT_PIN, KEY_PRESS_PIN, KEY1_PIN, KEY2_PIN, KEY3_PIN]

db_file = "questions.db"

def get_random_question():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT number, question FROM questions WHERE answered = 0 ORDER BY RANDOM() LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0], result[1]  # Return (ID, question text)
    else:
        return None, "No more questions!"


def get_all_questions():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT number, question FROM questions")
    questions = [(row[0], row[1]) for row in cursor.fetchall()]  # Return list of (ID, question)
    conn.close()
    return questions


# Initialize display
disp = LCD_1in44.LCD()
Lcd_ScanDir = LCD_1in44.SCAN_DIR_DFT
disp.LCD_Init(Lcd_ScanDir)
disp.LCD_Clear()

# Load font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 12)

# Button setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# UI logic
questions = get_all_questions()
current_index = 0

def display_text(text):
    image = Image.new('RGB', (128, 128), "black")
    draw = ImageDraw.Draw(image)
    
    # Wrap text
    lines = []
    words = text.split()
    line = ""
    for word in words:
        if font.getsize(line + word)[0] < 120:
            line += word + " "
        else:
            lines.append(line)
            line = word + " "
    lines.append(line)
    
    y = 20
    for line in lines:
        draw.text((5, y), line, font=font, fill="white")
        y += 15
    
    disp.LCD_ShowImage(image, 0, 0)

def mark_question_answered(question_id):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("UPDATE questions SET answered = 1 WHERE number = ?", (question_id,))
    conn.commit()
    conn.close()


def reset_questions():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("UPDATE questions SET answered = 0")
    conn.commit()
    conn.close()

def main():
    global current_index

    disp.LCD_Clear()
    display_text("Forced Vulnerability\n\n\nPress any button to start")

    while GPIO.input(KEY_PRESS_PIN) == 1:
        pass  # Wait for key press

    questions = get_all_questions()
    current_index = 0
    current_id, current_text = questions[current_index]  # Store ID & text

    display_text(current_text)

    while True:
        if GPIO.input(KEY_LEFT_PIN) == 0:  # Previous question
            current_index = (current_index - 1) % len(questions)
            current_id, current_text = questions[current_index]
            display_text(current_text)
            while GPIO.input(KEY_LEFT_PIN) == 0:
                pass

        elif GPIO.input(KEY_RIGHT_PIN) == 0:  # Next question
            current_index = (current_index + 1) % len(questions)
            current_id, current_text = questions[current_index]
            display_text(current_text)
            while GPIO.input(KEY_RIGHT_PIN) == 0:
                pass

        elif GPIO.input(KEY2_PIN) == 0:  # Mark question as answered
            mark_question_answered(current_id)  # Use ID
            display_text("Marked as answered!")
            while GPIO.input(KEY2_PIN) == 0:
                pass
            current_id, current_text = get_random_question()
            display_text(current_text)

        elif GPIO.input(KEY1_PIN) == 0:  # Reset questions
            time.sleep(0.3)
            if GPIO.input(KEY1_PIN) == 0:  # If still pressed, reset DB
                reset_questions()
                display_text("All questions reset!")
                while GPIO.input(KEY1_PIN) == 0:
                    pass
                current_id, current_text = get_random_question()
                display_text(current_text)


if __name__ == "__main__":
    main()

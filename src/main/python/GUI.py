import os.path
import random
import socket
import time

import pygame

from eyetracker_data import *

# sizes
GRID_CARDS = (7, 3)
CARD_SIZE = (200, 300)
DISTANCE_BETWEEN_CARDS = 10
NEXT_BUTTON_PHASE_1 = 75
RESOLUTION = (GRID_CARDS[0] * (CARD_SIZE[0] + DISTANCE_BETWEEN_CARDS) + DISTANCE_BETWEEN_CARDS, GRID_CARDS[1] * (CARD_SIZE[1] + DISTANCE_BETWEEN_CARDS) + (NEXT_BUTTON_PHASE_1 + 2 * DISTANCE_BETWEEN_CARDS))
CARD_PASSING_SCALE = 1.5

# colors
BG_COLOR = (99, 107, 97)
TEXT_COLOR_ON_BG = (255, 255, 250)

# times
FPS = 60
TIME_EACH_CARD_PASSING_SECS = 2

# assets and global lists
CARDS_FOLDER = "assets\\cards\\"
BACK_OF_CARD_NAME = "back_of_card.png"
TALENTO_DEI_LOGO_PATH = "assets\\icons_and_logos\\talento_dei_logo.png"
FONT_GAME_NAME_PATH = "assets\\fonts\\ARCADEPI.TTF"
CARD_IMAGES = []
CARDS_NAMES = []
RECT_LIST = []

# make sure the windows is centered on screen
root1 = tkinter.Tk()
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % ((root1.winfo_screenwidth() / 2) - RESOLUTION[0] / 2, (root1.winfo_screenheight() / 2) - RESOLUTION[1] / 2)
root1.deiconify()

# pygame window set
pygame.init()
screen = pygame.display.set_mode(RESOLUTION, pygame.NOFRAME)
pygame.display.set_caption("CARD TRICK GAME")

# socket communication
PORT = 1234

# forms link
# FORMS = "https://forms.gle/G5gPkFogF7DE8iaTA"


def match_info_write_to_file(path, player_data, cards_names):
    # dict with the correspondence between player_data and gender
    gender_dict = {1: "male", 2: "female", 3: "non-binary", 4: "rather not specify"}

    '''
    - create filepath
    - open file in append mode (if not already created)
        - write the name of each card
        - write player data
    '''
    folder_path = path.replace(".txt", "")
    info_filepath = folder_path + "\\info.txt"

    if not os.path.isfile(info_filepath):
        with open(info_filepath, "a") as info_file:
            for i in range(GRID_CARDS[0] * GRID_CARDS[1]):
                info_file.write("CARD {}: ".format(i + 1) + cards_names[i] + "\n")
            info_file.write("\nAGE: " + str(player_data[0]) + "; GENDER: " + gender_dict[player_data[1]] + "\n")
            info_file.write("\n--------------------\nTHE CARD WAS: ")


def fade(element, pos, in_or_out, time_fade, keep_bg = False):
    """
    MAKE ELEMENTS FADE
    :param pos: element(s) position: tuple(int, int)
    :param element: element to fade
    :param in_or_out: '2' for in, '1' for out
    :param time_fade: Time to fade (in secs)
    :param keep_bg: True or False
    """

    '''
    FADE TITLE
    - define clock for FPS
    - alpha loop
        - clear if keep_bg = False
        - increment/decrement alpha
        - update element with updated alpha
        - update (element or screen) with FPS
    '''

    clock = pygame.time.Clock()

    if in_or_out == 2:
        alpha = 0
    else:
        alpha = 255
    while ((alpha < 255) and (in_or_out == 2)) or ((alpha > 0) and (in_or_out == 1)):
        if not keep_bg:
            screen.fill(BG_COLOR)

        alpha = alpha + (pow(-1, in_or_out) * (255 / (time_fade * FPS)))

        element.set_alpha(alpha)
        screen.blit(element, pos)

        if keep_bg:
            pygame.display.update(pos, (element.get_width(), element.get_height()))
        else:
            pygame.display.flip()
        clock.tick(FPS)


def reveal_card(card_index):
    # clear screen
    screen.fill(BG_COLOR)

    '''
    FADE TITLE
    - define font and text
    - fade function
    - re-draw title
    '''
    title_font = pygame.font.Font(None, 80)
    title_text = title_font.render("YOUR CARD WAS...", True, TEXT_COLOR_ON_BG)

    fade(title_text, (RESOLUTION[0] / 2 - title_text.get_width() / 2, RESOLUTION[1] / 10), 2, 2)

    '''
    FADE CARD
    - scale card
    - fade function
    '''
    card_scaled = pygame.transform.scale(CARD_IMAGES[card_index], (CARD_SIZE[0] * CARD_PASSING_SCALE, CARD_SIZE[1] * CARD_PASSING_SCALE))
    fade(card_scaled, (RESOLUTION[0] / 2 - card_scaled.get_width() / 2, RESOLUTION[1] / 2 - card_scaled.get_height() / 2), 2, 2, True)

    time.sleep(2)


def show_cards_passing():
    timestamps = list()

    """
    PHASE 2 INTRODUCTION
    - define text
    - fade in text, sleep and then fade out text
    """
    title_font = pygame.font.Font(None, 80)
    title_text = title_font.render("PHASE 2: FIND YOUR CARD", True, TEXT_COLOR_ON_BG)

    fade(title_text, (RESOLUTION[0] / 2 - title_text.get_width() / 2, RESOLUTION[1] / 2 - title_text.get_height() / 2), 2, 1.5)
    time.sleep(1)
    fade(title_text, (RESOLUTION[0] / 2 - title_text.get_width() / 2, RESOLUTION[1] / 2 - title_text.get_height() / 2), 1, 1.5)

    '''
    SEND MESSAGE TO JAVA (START WRITING GAZE DATA TO FILE)
    '''
    socket_to_java = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_to_java.connect(('localhost', PORT))
    message = "WRITE"
    socket_to_java.sendall(message.encode())

    '''
    MAKE EACH CARD PASS BY THE SCREEN
    - loop for each card
        - get the timestamp for the beginning of each card
        - define clock
        - scale cards
        - loop for making them move
            - clear the screen
            - draw the card
            - update its position
            - update with FPS
    - timestamp of the end of the loop - verify is there is data missing
    '''
    for i in range(GRID_CARDS[0] * GRID_CARDS[1]):
        now_ns = time.time_ns()  # Time in nanoseconds
        now_ms = int(now_ns / 1000000)
        timestamps.append(now_ms)

        clock = pygame.time.Clock()

        card_scaled = pygame.transform.scale(CARD_IMAGES[i], (CARD_SIZE[0] * CARD_PASSING_SCALE, CARD_SIZE[1] * CARD_PASSING_SCALE))
        pos = (RESOLUTION[0] / 2 - card_scaled.get_width() / 2, RESOLUTION[1])
        while pos[1] > -card_scaled.get_height():
            screen.fill(BG_COLOR)

            screen.blit(card_scaled, pos)

            pos = (pos[0], pos[1] - ((RESOLUTION[1] + CARD_SIZE[1]) / (TIME_EACH_CARD_PASSING_SECS * FPS)))

            pygame.display.flip()
            clock.tick(FPS)

        '''
        EVENT HANDLER
        - quit
        '''
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()

    now_ns = time.time_ns()  # Time in nanoseconds
    now_ms = int(now_ns / 1000000)
    timestamps.append(now_ms)

    '''
    SEND MESSAGE TO JAVA (STOP WRITING GAZE DATA TO FILE)
    '''
    message = "STOP"
    socket_to_java.sendall(message.encode())

    '''
    START THE THREAD THAT WILL COLLECT THE DATA FROM THE EYE-TRACKER (PUPIL AND GAZE)
    - set the thread
    - get current timestamp
    thread_data = threading.Thread(target=get_data_with_pupil)
    thread_interface = threading.Thread(target=interface, args=(timestamps,))
    thread_data.start()
    thread_interface.start()
    # wait for data collection to finish
    thread_data.join()
    thread_interface.join()
    '''

    return timestamps


def show_card_grid():
    # clear screen
    screen.fill(BG_COLOR)
    pygame.display.flip()

    '''
    PHASE 1 INTRODUCTION
    - define text
    - fade in text, sleep and then fade out text
    '''
    title_font = pygame.font.Font(None, 80)
    title_text = title_font.render("PHASE 1: CHOOSE YOUR CARD", True, TEXT_COLOR_ON_BG)

    fade(title_text, (RESOLUTION[0] / 2 - title_text.get_width() / 2, RESOLUTION[1] / 2 - title_text.get_height() / 2), 2, 1.5)
    time.sleep(1)
    fade(title_text, (RESOLUTION[0] / 2 - title_text.get_width() / 2, RESOLUTION[1] / 2 - title_text.get_height() / 2), 1, 1.5)

    '''
    GET CARDS AND CREATE RECTANGLES
    - get back of card image and scale it
    - get the names of the cards
    - shuffle cards
    - get images from the file paths
    - generate rects for the grid
    '''
    back_of_card = pygame.image.load(CARDS_FOLDER + BACK_OF_CARD_NAME)
    back_of_card = pygame.transform.scale(back_of_card, CARD_SIZE)

    CARDS_NAMES.clear()
    for filename in os.listdir(CARDS_FOLDER):
        if filename.endswith(".png") and filename != BACK_OF_CARD_NAME:    # do not get back_of_card.png!
            CARDS_NAMES.append(filename)

    random.shuffle(CARDS_NAMES)

    CARD_IMAGES.clear()
    for filename in CARDS_NAMES:
        CARD_IMAGES.append(pygame.transform.scale(pygame.image.load(CARDS_FOLDER + filename), CARD_SIZE))

    for row in range(GRID_CARDS[1]):
        for col in range(GRID_CARDS[0]):
            rect = pygame.Rect(col * CARD_SIZE[0] + (col + 1) * DISTANCE_BETWEEN_CARDS, row * CARD_SIZE[1] + (row + 1) * DISTANCE_BETWEEN_CARDS, CARD_SIZE[0], CARD_SIZE[1])
            RECT_LIST.append(rect)

    '''
    BUTTON TO THE NEXT PHASE (JUST DRAW)
    - define button
    '''
    font_2nd_phase_button = pygame.font.Font(None, int(NEXT_BUTTON_PHASE_1 * 0.9))
    button_text = font_2nd_phase_button.render("NEXT", True, BG_COLOR)
    button_width = button_text.get_width() + 30
    button_height = NEXT_BUTTON_PHASE_1
    button_rect = pygame.Rect(RESOLUTION[0] - (button_width + DISTANCE_BETWEEN_CARDS),
                              RESOLUTION[1] - (NEXT_BUTTON_PHASE_1 + DISTANCE_BETWEEN_CARDS), button_width,
                              button_height)

    '''
    SHOW THE BACK OF THE CARDS
    - create clock (FPS),
    - fade loop
        - decrement alpha
        - apply alpha to the back of the cards
        - clear the screen
        - draw each section
            - draw the front of each card - to be seen during the fade
            - draw the back of the card - faded
        - draw button (light) and its text
    '''
    clock = pygame.time.Clock()

    fade_time_secs = 1
    alpha = 255
    while alpha > 0:
        alpha = alpha - (255 / (fade_time_secs * FPS))

        back_of_card.set_alpha(alpha)

        screen.fill(BG_COLOR)
        for j in range(GRID_CARDS[0] * GRID_CARDS[1]):
            screen.blit(CARD_IMAGES[j], RECT_LIST[j].topleft)

            screen.blit(back_of_card, RECT_LIST[j].topleft)

        pygame.draw.rect(screen, TEXT_COLOR_ON_BG, button_rect, border_radius=5)
        screen.blit(button_text, (button_rect.centerx - (button_text.get_width() / 2), button_rect.centery - (button_text.get_height() / 2)))

        pygame.display.flip()
        clock.tick(FPS)

    '''
    SEND MESSAGE TO JAVA (START WRITING GAZE DATA TO FILE)
    '''
    socket_to_java = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_to_java.connect(('localhost', PORT))
    message = "WRITE"
    socket_to_java.sendall(message.encode())

    '''
    LOOP AFTER CARDS SHOWN
    '''
    while True:
        # get mouse coordinates
        mouse = pygame.mouse.get_pos()

        '''
        BUTTON TO THE NEXT PHASE
        - (button already defined)
        - shade
        - draw button text
        '''
        if button_rect.collidepoint(mouse):
            pygame.draw.rect(screen, (int(TEXT_COLOR_ON_BG[0] * 0.7), int(TEXT_COLOR_ON_BG[1] * 0.7), int(TEXT_COLOR_ON_BG[2] * 0.7)), button_rect, border_radius = 5)
        else:
            pygame.draw.rect(screen, TEXT_COLOR_ON_BG, button_rect, border_radius = 5)

        screen.blit(button_text, (button_rect.centerx - (button_text.get_width() / 2), button_rect.centery - (button_text.get_height() / 2)))

        '''
        EVENT HANDLER
        - quit
        - mouse click
            - button to phase 2
        '''
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if button_rect.collidepoint(ev.pos):
                    '''
                    SEND MESSAGE TO JAVA (STOP WRITING GAZE DATA TO FILE)
                    '''
                    message = "STOP"
                    socket_to_java.sendall(message.encode())
                    return

        pygame.display.flip()


def player_data_input():
    """
    RETURNS A TUPLE: (AGE, GENDER)
    GENDER:
        - 1: male
        - 2: female
        - 3: non-binary
        - 4: rather not specify
    """

    # CLEAR SCREEN
    screen.fill(BG_COLOR)

    # PLAYER DATA
    age = 18
    gender = 0

    while True:
        # get mouse coordinates
        mouse = pygame.mouse.get_pos()

        '''
        TITLE
        '''
        title_font = pygame.font.Font(None, 80)
        title_text = title_font.render("SOME DATA ABOUT YOU...", True, TEXT_COLOR_ON_BG)
        screen.blit(title_text, (RESOLUTION[0] / 2 - title_text.get_width() / 2, RESOLUTION[1] / 15))

        '''
        FIELDS NAMES
        '''
        fields_names_font = pygame.font.Font(None, 75)
        age_text = fields_names_font.render("AGE", True, TEXT_COLOR_ON_BG)
        age_text_y = RESOLUTION[1] / 5 + age_text.get_height() / 2
        screen.blit(age_text, (RESOLUTION[0] / 2 - age_text.get_width() / 2, age_text_y))
        gender_text = fields_names_font.render("GENDER", True, TEXT_COLOR_ON_BG)
        gender_text_y = 2.75 * RESOLUTION[1] / 5 - gender_text.get_height()
        screen.blit(gender_text, (RESOLUTION[0] / 2 - gender_text.get_width() / 2, gender_text_y))

        '''
        AGE BUTTONS AND DISPLAY
        - age interface area
        - minus button
        - plus button
        - age display
        '''
        age_interface_area_size = (1.5 * (age_text.get_width() * 2 + 2 * age_text.get_height() / 3), age_text.get_height() * 2)
        age_interface_rect = pygame.Rect(RESOLUTION[0] / 2 - age_interface_area_size[0] / 2, age_text_y + 3 * age_text.get_height() / 2, age_interface_area_size[0], age_interface_area_size[1])
        pygame.draw.rect(screen, TEXT_COLOR_ON_BG, age_interface_rect, border_radius = 10)

        age_buttons_size = age_interface_area_size[1] - 2 * age_interface_area_size[1] / 8
        minus_age_rect = pygame.Rect(age_interface_rect.left + age_interface_area_size[1] / 8, age_interface_rect.top + age_interface_area_size[1] / 8, age_buttons_size, age_buttons_size)
        pygame.draw.rect(screen, BG_COLOR, minus_age_rect, border_radius = 10)
        minus = fields_names_font.render("-", True, TEXT_COLOR_ON_BG)
        screen.blit(minus, (minus_age_rect.centerx - minus.get_width() / 2, minus_age_rect.centery - minus.get_height() / 2))

        plus_age_rect = pygame.Rect(age_interface_rect.right - (age_interface_area_size[1] / 8 + age_buttons_size), age_interface_rect.top + age_interface_area_size[1] / 8, age_buttons_size, age_buttons_size)
        pygame.draw.rect(screen, BG_COLOR, plus_age_rect, border_radius = 10)
        plus = fields_names_font.render("+", True, TEXT_COLOR_ON_BG)
        screen.blit(plus, (plus_age_rect.centerx - plus.get_width() / 2, plus_age_rect.centery - plus.get_height() / 2))

        age_display_font = pygame.font.Font(None, 70)
        age_display = age_display_font.render(str(age), True, BG_COLOR)
        screen.blit(age_display, (age_interface_rect.centerx - age_display.get_width() / 2, age_interface_rect.centery - age_display.get_height() / 2))

        '''
        GENDER BUTTONS AND DISPLAY
        - gender options text
        - gender interface area
        - options: positions and rects
        - show selected option
        - draw gender options text
        '''
        gender_font = pygame.font.Font(None, 55)
        male_text = gender_font.render("MALE", True, BG_COLOR)
        female_text = gender_font.render("FEMALE", True, BG_COLOR)
        non_binary_text = gender_font.render("NON-BINARY", True, BG_COLOR)
        rather_not_font = pygame.font.Font(None, 50)
        rather_not_text = rather_not_font.render("RATHER NOT SPECIFY", True, BG_COLOR)

        gender_interface_area_size = (max(male_text.get_width() + female_text.get_width() + 3 * male_text.get_height() / 2.25 + male_text.get_height(), non_binary_text.get_width() + 2 * male_text.get_height() / 2.25, rather_not_text.get_width() + 2 * male_text.get_height() / 2.25), 2 * male_text.get_height() + rather_not_text.get_height() + 4 * male_text.get_height() / 2.25)
        gender_interface_area = pygame.Rect(RESOLUTION[0] / 2 - gender_interface_area_size[0] / 2, gender_text_y + 3 * gender_text.get_height() / 2, gender_interface_area_size[0], gender_interface_area_size[1])
        pygame.draw.rect(screen, TEXT_COLOR_ON_BG, gender_interface_area, border_radius = 10)

        male_text_pos = (gender_interface_area.centerx - (male_text.get_width() + female_text.get_width() + male_text.get_height()) / 2, gender_interface_area.top + male_text.get_height() / 2.25)
        male_rect = pygame.Rect(male_text_pos, (male_text.get_width(), male_text.get_height()))
        female_text_pos = (gender_interface_area.centerx - (male_text.get_width() + female_text.get_width() + male_text.get_height()) / 2 + (male_text.get_width() + male_text.get_height()), gender_interface_area.top + male_text.get_height() / 2.25)
        female_rect = pygame.Rect(female_text_pos, (female_text.get_width(), female_text.get_height()))
        non_binary_text_pos = (gender_interface_area.centerx - non_binary_text.get_width() / 2, gender_interface_area.top + 4.25 * male_text.get_height() / 2.25)
        non_binary_rect = pygame.Rect(non_binary_text_pos, (non_binary_text.get_width(), non_binary_text.get_height()))
        rather_not_text_pos = (gender_interface_area.centerx - (rather_not_text.get_width()) / 2, gender_interface_area.bottom - (male_text.get_height() / 2.25 + rather_not_text.get_height()))
        rather_not_rect = pygame.Rect(rather_not_text_pos, (rather_not_text.get_width(), rather_not_text.get_height()))

        if gender == 1:
            pygame.draw.rect(screen, (int(TEXT_COLOR_ON_BG[0] * 0.7), int(TEXT_COLOR_ON_BG[1] * 0.7), int(TEXT_COLOR_ON_BG[2] * 0.7)), male_rect)
            for i in (female_rect, non_binary_rect, rather_not_rect):
                pygame.draw.rect(screen, TEXT_COLOR_ON_BG, i)
        elif gender == 2:
            pygame.draw.rect(screen, (int(TEXT_COLOR_ON_BG[0] * 0.7), int(TEXT_COLOR_ON_BG[1] * 0.7), int(TEXT_COLOR_ON_BG[2] * 0.7)), female_rect)
            for i in (male_rect, non_binary_rect, rather_not_rect):
                pygame.draw.rect(screen, TEXT_COLOR_ON_BG, i)
        elif gender == 3:
            pygame.draw.rect(screen, (int(TEXT_COLOR_ON_BG[0] * 0.7), int(TEXT_COLOR_ON_BG[1] * 0.7), int(TEXT_COLOR_ON_BG[2] * 0.7)), non_binary_rect)
            for i in (male_rect, female_rect, rather_not_rect):
                pygame.draw.rect(screen, TEXT_COLOR_ON_BG, i)
        elif gender == 4:
            pygame.draw.rect(screen, (int(TEXT_COLOR_ON_BG[0] * 0.7), int(TEXT_COLOR_ON_BG[1] * 0.7), int(TEXT_COLOR_ON_BG[2] * 0.7)), rather_not_rect)
            for i in (male_rect, female_rect, non_binary_rect):
                pygame.draw.rect(screen, TEXT_COLOR_ON_BG, i)

        screen.blit(male_text, male_text_pos)
        screen.blit(female_text, female_text_pos)
        screen.blit(non_binary_text, non_binary_text_pos)
        screen.blit(rather_not_text, rather_not_text_pos)

        '''
        CONTINUE BUTTON
        - define button text
        - define button rect
        - shade button
        - draw button text
        '''
        font_start_button = pygame.font.Font(None, 75)
        button_text = font_start_button.render("CONTINUE", True, BG_COLOR)
        button_width = button_text.get_width() + 30
        button_height = button_text.get_height() + 20
        button_rect = pygame.Rect((RESOLUTION[0] / 2) - (button_width / 2), 5 * RESOLUTION[1] / 6, button_width, button_height)

        if button_rect.collidepoint(mouse):
            pygame.draw.rect(screen, (int(TEXT_COLOR_ON_BG[0] * 0.7), int(TEXT_COLOR_ON_BG[1] * 0.7), int(TEXT_COLOR_ON_BG[2] * 0.7)), button_rect, border_radius = 5)
        else:
            pygame.draw.rect(screen, TEXT_COLOR_ON_BG, button_rect, border_radius = 5)

        screen.blit(button_text, (button_rect.centerx - (button_text.get_width() / 2), button_rect.centery - (button_text.get_height() / 2)))

        '''
        EVENT HANDLER
        - quit
        - mouse click
            - plus button age
            - minus button age
            - male gender button
            - female gender button
            - non-binary gender button
            - rather not specify gender button
            - continue button
        '''
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if plus_age_rect.collidepoint(ev.pos):
                    age = age + 1
                if minus_age_rect.collidepoint(ev.pos) and age > 0:
                    age = age - 1
                if male_rect.collidepoint(ev.pos):
                    gender = 1
                if female_rect.collidepoint(ev.pos):
                    gender = 2
                if non_binary_rect.collidepoint(ev.pos):
                    gender = 3
                if rather_not_rect.collidepoint(ev.pos):
                    gender = 4
                if button_rect.collidepoint(ev.pos) and gender != 0:
                    return age, gender

        pygame.display.flip()


def initial_logo():
    # TALENTO@DEI LOGO
    # - screen fill
    # - get logo
    # - fade in logo, sleep and then fade out logo
    screen.fill(BG_COLOR)

    talento_dei_logo = pygame.image.load(TALENTO_DEI_LOGO_PATH)
    talento_dei_logo = pygame.transform.scale(talento_dei_logo, (talento_dei_logo.get_width() / 2, talento_dei_logo.get_height() / 2))

    fade(talento_dei_logo, (RESOLUTION[0] / 2 - talento_dei_logo.get_width() / 2, RESOLUTION[1] / 2 - talento_dei_logo.get_height() / 2), 2, 1.5)
    time.sleep(1.5)
    fade(talento_dei_logo, (RESOLUTION[0] / 2 - talento_dei_logo.get_width() / 2, RESOLUTION[1] / 2 - talento_dei_logo.get_height() / 2), 1, 1.5)


def main():
    initial_logo()

    accepted = False

    while True:
        # get mouse coordinates
        mouse = pygame.mouse.get_pos()

        screen.fill(BG_COLOR)

        '''
        TITLE
        '''
        font_title = pygame.font.Font(FONT_GAME_NAME_PATH, 80)
        initial_text = font_title.render("CARD GUESSER", True, TEXT_COLOR_ON_BG)
        initial_text = pygame.transform.scale(initial_text, (initial_text.get_width(), initial_text.get_height() * 1.5))
        screen.blit(initial_text, (RESOLUTION[0] / 2 - initial_text.get_width() / 2, RESOLUTION[1] / 7))

        '''
        START BUTTON
        - define button
        - shade
        - draw button text
        '''
        font_start_button = pygame.font.Font(None, 100)
        button_text = font_start_button.render("START", True, BG_COLOR)
        button_width = button_text.get_width() + 30
        button_height = button_text.get_height() + 20
        button_rect = pygame.Rect((RESOLUTION[0] / 2) - (button_width / 2), 5 * RESOLUTION[1] / 6, button_width, button_height)

        if button_rect.collidepoint(mouse):
            pygame.draw.rect(screen, (int(TEXT_COLOR_ON_BG[0] * 0.7), int(TEXT_COLOR_ON_BG[1] * 0.7), int(TEXT_COLOR_ON_BG[2] * 0.7)), button_rect, border_radius = 5)
        else:
            pygame.draw.rect(screen, TEXT_COLOR_ON_BG, button_rect, border_radius = 5)

        screen.blit(button_text, (button_rect.centerx - (button_text.get_width() / 2), button_rect.centery - (button_text.get_height() / 2)))

        '''
        TERMS AND CHECKBOX
        - terms text
        - checkbox and terms area
        - draw text
        - draw checkbox
        - make tick appear
        '''
        font_terms = pygame.font.Font(None, 40)
        text_terms = font_terms.render("I agree with terms and conditions.", True, TEXT_COLOR_ON_BG)

        checkbox_size = text_terms.get_height()
        checkbox_terms_area_size = (checkbox_size * 1.5 + text_terms.get_width(), checkbox_size)
        checkbox_terms_area = pygame.Rect(RESOLUTION[0] / 2 - checkbox_terms_area_size[0] / 2, button_rect.top - checkbox_terms_area_size[1] * 2.5, checkbox_terms_area_size[0], checkbox_terms_area_size[1])

        screen.blit(text_terms, (checkbox_terms_area.right - text_terms.get_width(), checkbox_terms_area.top))

        checkbox = pygame.Rect(checkbox_terms_area.left, checkbox_terms_area.top, checkbox_size, checkbox_size)
        pygame.draw.rect(screen, TEXT_COLOR_ON_BG, checkbox, border_radius = checkbox_size, width = 2)

        if accepted:
            pygame.draw.circle(screen, TEXT_COLOR_ON_BG, checkbox.center, checkbox_size / 4)

        '''
        EVENT HANDLER
        - quit
        - mouse click
            - terms checkbox area
            - start button, next stage
                - next phases and data treatment
        '''
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if checkbox_terms_area.collidepoint(ev.pos):
                    # webbrowser.open(FORMS)
                    accepted = not accepted
                if button_rect.collidepoint(ev.pos) and accepted:
                    accepted = not accepted
                    player_data = player_data_input()

                    show_card_grid()

                    base = "C:\\Users\\Alexandre-Jacob\\Documents\\TESTING"
                    if not os.path.exists(base):
                        os.makedirs(base)
                    files = [file for file in os.listdir(base) if os.path.isfile(os.path.join(base, file))]
                    path = files[-1]
                    phase_one = EyetrackerData(EyetrackerData.DataType.PHASE_ONE, base + os.path.sep + path, GRID_CARDS, CARD_SIZE, RESOLUTION, DISTANCE_BETWEEN_CARDS)
                    phase_one.process_data(None)
                    out_1 = os.path.splitext(os.path.basename(path))[0] + "_PHASE_ONE"
                    os.mkdir(base + os.path.sep + out_1)
                    phase_one.export_data(base + os.path.sep + out_1)

                    timestamps = show_cards_passing()
                    files = [file for file in os.listdir(base) if os.path.isfile(os.path.join(base, file))]
                    path = files[-1]
                    phase_two = EyetrackerData(EyetrackerData.DataType.PHASE_TWO, base + os.path.sep + path, GRID_CARDS, CARD_SIZE, RESOLUTION, DISTANCE_BETWEEN_CARDS)
                    phase_two.process_data(timestamps)
                    out_2 = os.path.splitext(os.path.basename(path))[0] + "_PHASE_TWO"
                    os.mkdir(base + os.path.sep + out_2)
                    phase_two.export_data(base + os.path.sep + out_2)

                    # READ RELEVANT DATA FROM JSON FILE
                    with open(base + os.path.sep + out_1 + os.path.sep + "relevant_data.json", "r") as relevant_data_json:
                        relevant_data = json.load(relevant_data_json)
                    reveal_card(int(relevant_data["CARD_WITH_LONGEST_FIXATION"].replace("CARD_", "")) - 1)

                    initial_logo()
        pygame.display.flip()


'''
GAME
'''
main()

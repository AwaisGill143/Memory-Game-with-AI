import pygame
import random

pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Colors
BACKGROUND_COLOR = (0, 0, 0)
CARD_BACK_COLOR = (255, 255, 255)
TEXT_COLOR = (0, 0, 0)

# Fonts
FONT = pygame.font.SysFont('arial', 24)

# Initialize game variables; these will be set based on grid selection
card_size = (90, 120)
gap_size = 10
board_width = 6  # Default value, will be updated based on user selection
board_height = 6  # Default value, will be updated based on user selection
player_score = 0
computer_score = 0
turn = "player"

# AI memory
ai_memory = {}

class SkipNode:
    def __init__(self, key=None, level=0):
        self.key = key
        self.forward = [None] * (level + 1)

class SkipList:
    def __init__(self, max_level=16, p=0.5):
        self.max_level = max_level
        self.p = p
        self.header = self.create_node(self.max_level, None)
        self.level = 0

    def create_node(self, level, key):
        return SkipNode(key, level)

    def random_level(self):
        level = 0
        while random.random() < self.p and level < self.max_level - 1:
            level += 1
        return level

    def insert(self, key):
        update = [None] * (self.max_level)
        current = self.header
        for i in reversed(range(self.max_level)):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        level = self.random_level()
        if level > self.level:
            for i in range(self.level + 1, level + 1):
                update[i] = self.header
            self.level = level
        node = self.create_node(level, key)
        for i in range(level + 1):
            node.forward[i] = update[i].forward[i]
            update[i].forward[i] = node

    def search(self, key):
        current = self.header
        for i in reversed(range(self.level + 1)):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
        current = current.forward[0]
        if current and current.key == key:
            return True
        return False

    def delete(self, key):
        update = [None] * (self.max_level)
        current = self.header
        for i in reversed(range(self.max_level)):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        current = current.forward[0]
        if current and current.key == key:
            for i in range(self.level + 1):  # Fixed: use self.level instead of undefined 'level'
                if update[i].forward[i] != current:
                    break
                update[i].forward[i] = current.forward[i]
            del current

def select_grid_size():
    screen.fill(BACKGROUND_COLOR)
    options = ["4x4", "6x6", "8x8"]
    option_texts = [FONT.render(option, True, (255, 255, 255)) for option in options]
    option_rects = []

    for index, option_text in enumerate(option_texts):
        rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, 150 + index * 100))
        option_rects.append(rect)
        screen.blit(option_text, rect)

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(option_rects):
                    if rect.collidepoint(event.pos):
                        return options[i]

def generate_board(items):
    card_names = [item['name'] for item in items]
    board = random.sample(card_names, board_width * board_height // 2) * 2
    random.shuffle(board)
    return [board[i * board_width:(i + 1) * board_width] for i in range(board_height)]


def draw_board(board, revealed, matched, items):
    screen.fill(BACKGROUND_COLOR)
    for row in range(board_height):
        for col in range(board_width):
            left = col * (card_size[0] + gap_size) + gap_size
            top = row * (card_size[1] + gap_size) + gap_size
            if matched[row][col]:
                continue
            if revealed[row][col]:
                card_name = board[row][col]
                card_number = str(items.index({'name': card_name}) + 1)  # Get the index of the item in items list and add 1 to convert to string
                card_surface = card_images[card_name].copy()  # Make a copy of the original card surface
                number_text = FONT.render(card_number, True, TEXT_COLOR)  # Render the number text
                number_rect = number_text.get_rect(center=(card_size[0] // 2, card_size[1] // 2))  # Center the number text on the card
                card_surface.blit(number_text, number_rect)  # Blit the number text onto the card surface
                screen.blit(card_surface, (left, top))  # Blit the modified card surface onto the screen
            else:
                screen.blit(card_back, (left, top))
    player_score_text = FONT.render(f"Player Score: {player_score}", True, (255, 255, 255))
    computer_score_text = FONT.render(f"Computer Score: {computer_score}", True, (255, 255, 255))
    turn_text = FONT.render(f"Turn: {turn.capitalize()}", True, (255, 255, 255))
    screen.blit(player_score_text, (SCREEN_WIDTH - 200, 150))
    screen.blit(computer_score_text, (SCREEN_WIDTH - 200, 200))
    screen.blit(turn_text, (SCREEN_WIDTH - 200, 250))
    pygame.display.flip()

def update_ai_memory(name, position):
    if name not in ai_memory:
        ai_memory[name] = []
    ai_memory[name].append(position)

def forget_ai_memory(name, positions):
    if name in ai_memory:
        for pos in positions:
            if pos in ai_memory[name]:
                ai_memory[name].remove(pos)
        if not ai_memory[name]:
            del ai_memory[name]

def ai_find_match(skip_list):
    for name, positions in ai_memory.items():
        if len(positions) > 1 and skip_list.search(name):
            return positions[0], positions[1]
    return None, None

def get_card_at_pos(pos):
    x, y = pos
    for row in range(board_height):
        for col in range(board_width):
            left = col * (card_size[0] + gap_size) + gap_size
            top = row * (card_size[1] + gap_size) + gap_size
            card_rect = pygame.Rect(left, top, card_size[0], card_size[1])
            if card_rect.collidepoint(x, y):
                return (row, col)
    return None

def computer_turn(board, revealed, matched, skip_list):
    card1_pos, card2_pos = ai_find_match(skip_list)
    if card1_pos and card2_pos:
        return card1_pos, card2_pos
    tries = [(row, col) for row in range(board_height) for col in range(board_width) if not revealed[row][col] and not matched[row][col]]
    return random.sample(tries, 2) if len(tries) >= 2 else (None, None)

def update_scores_and_turn(first_card, second_card, board, matched, skip_list):
    global player_score, computer_score, turn
    match = board[first_card[0]][first_card[1]] == board[second_card[0]][second_card[1]]
    if match:
        if turn == "player":
            player_score += 1
        else:
            computer_score += 1
            matched[first_card[0]][first_card[1]] = True
            matched[second_card[0]][second_card[1]] = True
            skip_list.delete(board[first_card[0]][first_card[1]])
            skip_list.delete(board[second_card[0]][second_card[1]])
    else:
        if turn == "computer":
            forget_ai_memory(board[first_card[0]][first_card[1]], [first_card])
            forget_ai_memory(board[second_card[0]][second_card[1]], [second_card])
    turn = "computer" if turn == "player" else "player"

def game_loop():
    global turn,items 
    board = generate_board(items)
    revealed = [[False] * board_width for _ in range(board_height)]
    matched = [[False] * board_width for _ in range(board_height)]
    running = True
    first_selection = None
    matches_found = 0

    skip_list = SkipList()

    while running:
        draw_board(board, revealed, matched,items)
        if turn == "computer" and matches_found < (board_width * board_height // 2):
            pygame.time.wait(1000)  # Computer thinking time
            card1, card2 = computer_turn(board, revealed, matched, skip_list)
            if card1 and card2:
                revealed[card1[0]][card1[1]] = True
                revealed[card2[0]][card2[1]] = True
                draw_board(board, revealed, matched,items)
                pygame.time.wait(1000)
                update_scores_and_turn(card1, card2, board, matched, skip_list)
                if board[card1[0]][card1[1]] == board[card2[0]][card2[1]]:
                    matches_found += 1
                else:
                    revealed[card1[0]][card1[1]] = False
                    revealed[card2[0]][card2[1]] = False
                first_selection = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and turn == "player":
                mouse_pos = event.pos
                clicked_card = get_card_at_pos(mouse_pos)
                if clicked_card is not None and not revealed[clicked_card[0]][clicked_card[1]] and not matched[clicked_card[0]][clicked_card[1]]:
                    row, col = clicked_card
                    revealed[row][col] = True
                    draw_board(board, revealed, matched,items)
                    if not first_selection:
                        first_selection = (row, col)
                    else:
                        update_scores_and_turn(first_selection, (row, col), board, matched, skip_list)
                        if board[first_selection[0]][first_selection[1]] != board[row][col]:
                            pygame.time.wait(500)  # Wait half a second
                            revealed[first_selection[0]][first_selection[1]] = False
                            revealed[row][col] = False
                        else:
                            matches_found += 1
                            if matches_found == (board_width * board_height // 2):
                                print("Game Over")
                                pygame.time.wait(5000) 
                                running = False
                        first_selection = None
                        turn = "computer"  # Switch turn

if __name__ == '__main__':
    selected_size = select_grid_size()
    if selected_size == "4x4":
        board_width, board_height = 4, 4
    elif selected_size == "6x6":
        board_width, board_height = 6, 6
    else:
        board_width, board_height = 8, 8

    unique_items_needed = (board_width * board_height) // 2
    items = [{'name': f'Animal {i}'} for i in range(unique_items_needed)]

    # Load images (adjusted for the new dynamic items list)
    card_images = {item['name']: pygame.Surface(card_size) for item in items}
    for item in card_images.values():
        item.fill((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    card_back = pygame.Surface(card_size)
    card_back.fill(CARD_BACK_COLOR)

    game_loop()  # Ensure to adjust the function calls inside game_loop to pass and use 'items'

    

    pygame.quit()

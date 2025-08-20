import pygame
import random
import sys

# --- Constants ---
# Screen
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
BG_COLOR = (0, 100, 0) # A nice green for the table

# Cards
CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_CORNER_RADIUS = 5
CARD_OUTLINE_WIDTH = 2
CARD_STACK_Y_OFFSET = 30  # Vertical space between stacked cards in tableau
CARD_STACK_X_OFFSET = 20  # For the waste pile

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (200, 0, 0)
COLOR_GREY = (150, 150, 150)
COLOR_YELLOW_SELECT = (255, 255, 0) # Highlight for selected card

# Positions
DECK_POS = (50, 50)
WASTE_POS = (DECK_POS[0] + CARD_WIDTH + 50, 50)
FOUNDATION_START_POS = (WASTE_POS[0] + CARD_WIDTH + 150, 50)
TABLEAU_START_POS = (50, 250)


# --- Game Logic Classes (adapted for Pygame) ---

class Card:
    def __init__(self, rank, suit_char, suit_color):
        self.rank = rank
        self.suit_char = suit_char
        self.suit_color = suit_color
        self.value = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13}[rank]
        
        self.is_flipped = False
        self.image = self._create_image()
        self.back_image = self._create_back_image()
        self.rect = self.image.get_rect()

    def _create_image(self):
        image = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        image.fill(COLOR_WHITE)
        pygame.draw.rect(image, COLOR_BLACK, image.get_rect(), CARD_OUTLINE_WIDTH, CARD_CORNER_RADIUS)

        font = pygame.font.SysFont('arial', 20)
        rank_text = font.render(self.rank, True, self.suit_color)
        suit_text = font.render(self.suit_char, True, self.suit_color)
        
        image.blit(rank_text, (5, 5))
        image.blit(suit_text, (5, 25))
        
        big_suit_font = pygame.font.SysFont('arial', 40)
        big_suit_text = big_suit_font.render(self.suit_char, True, self.suit_color)
        pos = big_suit_text.get_rect(center=image.get_rect().center)
        image.blit(big_suit_text, pos)
        
        return image

    def _create_back_image(self):
        image = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        image.fill((20, 50, 150))
        pygame.draw.rect(image, COLOR_GREY, image.get_rect(), CARD_OUTLINE_WIDTH, CARD_CORNER_RADIUS)
        return image

    def flip(self):
        self.is_flipped = True

    def draw(self, screen):
        if self.is_flipped:
            screen.blit(self.image, self.rect)
        else:
            screen.blit(self.back_image, self.rect)
            
    def draw_highlight(self, screen):
        pygame.draw.rect(screen, COLOR_YELLOW_SELECT, self.rect, 4, CARD_CORNER_RADIUS)

class Deck:
    def __init__(self):
        self.cards = self._generate()
        self.waste = []
        self.shuffle()
        self.deck_rect = pygame.Rect(DECK_POS[0], DECK_POS[1], CARD_WIDTH, CARD_HEIGHT)
        self.reset_rect = self.deck_rect.copy()

    def _generate(self):
        cards = []
        suits = {"♠": COLOR_BLACK, "♣": COLOR_BLACK, "♥": COLOR_RED, "♦": COLOR_RED}
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        for suit_char, color in suits.items():
            for rank in ranks:
                cards.append(Card(rank, suit_char, color))
        return cards

    def shuffle(self):
        random.shuffle(self.cards)

    def draw_card(self):
        if self.cards:
            card = self.cards.pop()
            card.flip()
            self.waste.append(card)
            self._update_waste_positions()

    def reset(self):
        # Move all waste cards back to the deck
        self.cards.extend(self.waste)
        self.waste = []
        # Flip them back over and shuffle
        for card in self.cards:
            card.is_flipped = False
        self.shuffle()
        
    def _update_waste_positions(self):
        for i, card in enumerate(self.waste[-3:]):
             card.rect.topleft = (WASTE_POS[0] + i * CARD_STACK_X_OFFSET, WASTE_POS[1])

    def draw(self, screen):
        if self.cards:
            screen.blit(self.cards[0].back_image, self.deck_rect)
        else:
            pygame.draw.rect(screen, COLOR_GREY, self.reset_rect, 2, CARD_CORNER_RADIUS)
            font = pygame.font.SysFont('arial', 16)
            text = font.render("RESET", True, COLOR_WHITE)
            screen.blit(text, text.get_rect(center=self.reset_rect.center))

        for card in self.waste[-3:]:
            card.draw(screen)

class Pile:
    def __init__(self, pos):
        self.cards = []
        self.base_rect = pygame.Rect(pos[0], pos[1], CARD_WIDTH, CARD_HEIGHT)

    def draw(self, screen):
        if not self.cards:
            pygame.draw.rect(screen, COLOR_GREY, self.base_rect, 2, CARD_CORNER_RADIUS)
        else:
            for card in self.cards:
                card.draw(screen)
    
    def get_top_card(self):
        return self.cards[-1] if self.cards else None

class TableauPile(Pile):
    def __init__(self, pos):
        super().__init__(pos)

    def add_cards(self, new_cards):
        self.cards.extend(new_cards)
        self.update_card_positions()
    
    def can_place(self, card_stack):
        card = card_stack[0]
        if not self.cards:
            return card.rank == "K"
        
        top_card = self.get_top_card()
        return card.suit_color != top_card.suit_color and card.value == top_card.value - 1
        
    def flip_top_card(self):
        if self.cards and not self.get_top_card().is_flipped:
            self.get_top_card().flip()
            
    def update_card_positions(self):
        for i, card in enumerate(self.cards):
            card.rect.topleft = (self.base_rect.x, self.base_rect.y + i * CARD_STACK_Y_OFFSET)

class FoundationPile(Pile):
    def __init__(self, pos):
        super().__init__(pos)
        # CHANGE 1: The pile no longer has a predefined suit. It's determined by the first card.
        self.suit_char = None
        
    def can_place(self, card_stack):
        if len(card_stack) > 1: return False # Only single cards
        
        card = card_stack[0]
        
        # CHANGE 2: If the pile is empty, it can accept ANY Ace.
        if not self.cards:
            return card.rank == "A"
            
        # If it's not empty, it must match the pile's established suit and be the next in sequence.
        top_card = self.get_top_card()
        return card.suit_char == self.suit_char and card.value == top_card.value + 1
        
    def add_cards(self, new_cards):
        # CHANGE 3: When the first card (an Ace) is added, set the pile's suit.
        if not self.cards:
            self.suit_char = new_cards[0].suit_char
            
        self.cards.extend(new_cards)
        self.update_card_positions()
    
    def update_card_positions(self):
        for card in self.cards:
            card.rect.topleft = self.base_rect.topleft
            
    # Overriding draw to show the suit on an empty pile once assigned
    def draw(self, screen):
        if not self.cards:
            pygame.draw.rect(screen, COLOR_GREY, self.base_rect, 2, CARD_CORNER_RADIUS)
            # If a suit has been assigned, draw it as a placeholder
            if self.suit_char:
                color = COLOR_RED if self.suit_char in ["♥", "♦"] else COLOR_BLACK
                font = pygame.font.SysFont('arial', 40)
                suit_text = font.render(self.suit_char, True, color)
                screen.blit(suit_text, suit_text.get_rect(center=self.base_rect.center))
        else:
            # Only draw the top card for foundations for cleaner look
            self.get_top_card().draw(screen)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Klondike Solitaire (No Assets)")
        self.clock = pygame.time.Clock()

        self.deck = Deck()
        self.tableau_piles = [TableauPile((TABLEAU_START_POS[0] + i * (CARD_WIDTH + 20), TABLEAU_START_POS[1])) for i in range(7)]
        # Foundation piles are now created without a pre-assigned suit
        self.foundation_piles = [FoundationPile((FOUNDATION_START_POS[0] + i * (CARD_WIDTH + 20), FOUNDATION_START_POS[1])) for i in range(4)]

        self.deal_cards()

        self.held_cards = []
        self.held_cards_offset = (0, 0)
        self.source_pile = None
        self.win = False

    def deal_cards(self):
        for i in range(7):
            for j in range(i, 7):
                card = self.deck.cards.pop()
                self.tableau_piles[j].add_cards([card])
        
        for pile in self.tableau_piles:
            pile.flip_top_card()
            
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if not self.win:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.handle_click(event.pos)
                    
                    if event.type == pygame.MOUSEBUTTONUP:
                        if self.held_cards:
                            self.handle_drop(event.pos)
                            
                    if event.type == pygame.MOUSEMOTION:
                        if self.held_cards:
                            self.update_held_cards_pos(event.pos)

            self.draw()
            if not self.win:
                self.check_win()
            
            if self.win:
                self.display_win_message()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def handle_click(self, pos):
        # BUG FIX: Reordered logic to be mutually exclusive.
        # First, check for a RESET click, which can only happen if the deck is empty.
        if not self.deck.cards and self.deck.reset_rect.collidepoint(pos):
            self.deck.reset()
            return
        
        # Second, check for a DRAW click, which can only happen if the deck is NOT empty.
        if self.deck.cards and self.deck.deck_rect.collidepoint(pos):
            self.deck.draw_card()
            return

        # Check Waste Pile (top card only)
        if self.deck.waste and self.deck.waste[-1].rect.collidepoint(pos):
            self.held_cards = [self.deck.waste.pop()]
            self.source_pile = self.deck
            self.start_drag(pos)
            self.deck._update_waste_positions()
            return

        # Check Tableau Piles
        for pile in self.tableau_piles:
            for i, card in reversed(list(enumerate(pile.cards))):
                if card.is_flipped and card.rect.collidepoint(pos):
                    self.held_cards = pile.cards[i:]
                    self.source_pile = pile
                    pile.cards = pile.cards[:i]
                    self.start_drag(pos)
                    return

        # Check Foundation Piles
        for pile in self.foundation_piles:
            if pile.get_top_card() and pile.get_top_card().rect.collidepoint(pos):
                self.held_cards = [pile.cards.pop()]
                self.source_pile = pile
                self.start_drag(pos)
                return

    def start_drag(self, pos):
        self.held_cards_offset = (pos[0] - self.held_cards[0].rect.x, pos[1] - self.held_cards[0].rect.y)

    def update_held_cards_pos(self, pos):
        top_card = self.held_cards[0]
        top_card.rect.x = pos[0] - self.held_cards_offset[0]
        top_card.rect.y = pos[1] - self.held_cards_offset[1]
        
        for i, card in enumerate(self.held_cards[1:], 1):
            card.rect.topleft = (top_card.rect.x, top_card.rect.y + i * CARD_STACK_Y_OFFSET)

    def handle_drop(self, pos):
        target_pile = None
        
        for pile in self.foundation_piles:
            if pile.base_rect.collidepoint(pos) and pile.can_place(self.held_cards):
                target_pile = pile
                break

        if not target_pile:
            for pile in self.tableau_piles:
                check_rect = pile.get_top_card().rect if pile.cards else pile.base_rect
                if check_rect.collidepoint(pos) and pile.can_place(self.held_cards):
                    target_pile = pile
                    break
        
        if target_pile:
            target_pile.add_cards(self.held_cards)
            if isinstance(self.source_pile, TableauPile):
                self.source_pile.flip_top_card()
        else: # Invalid move, return cards
            if self.source_pile == self.deck:
                self.deck.waste.extend(self.held_cards)
                self.deck._update_waste_positions()
            else:
                self.source_pile.add_cards(self.held_cards)

        self.held_cards = []
        self.source_pile = None

    def check_win(self):
        if sum(len(p.cards) for p in self.foundation_piles) == 52:
            self.win = True

    def display_win_message(self):
        font = pygame.font.SysFont('arial', 80)
        text = font.render("YOU WIN!", True, COLOR_YELLOW_SELECT)
        text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        self.screen.blit(text, text_rect)
        
    def draw(self):
        self.screen.fill(BG_COLOR)
        self.deck.draw(self.screen)
        for pile in self.foundation_piles:
            pile.draw(self.screen)
        for pile in self.tableau_piles:
            pile.draw(self.screen)
        
        for card in self.held_cards:
            card.draw(self.screen)
            card.draw_highlight(self.screen)

if __name__ == "__main__":
    game = Game()
    game.run()

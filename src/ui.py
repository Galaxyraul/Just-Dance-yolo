import pygame
from config import BLANCO, NEON_ROSA

class Boton:
    def __init__(self, texto, x, y, w, h, color, data=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.texto = texto
        self.color = color
        self.data = data
        self.hover = False

    def dibujar(self, screen, font):
        color_actual = self.color if not self.hover else BLANCO
        pygame.draw.rect(screen, color_actual, self.rect, 2, border_radius=8)
        
        if self.hover:
            s = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            s.fill((*self.color, 50))
            screen.blit(s, (self.rect.x, self.rect.y))

        txt = font.render(str(self.texto), True, color_actual)
        screen.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))

    def check_hover(self, mx, my):
        self.hover = self.rect.collidepoint(mx, my)
        return self.hover
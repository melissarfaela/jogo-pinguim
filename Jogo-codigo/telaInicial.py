import pygame
import sys
import subprocess
from pathlib import Path

# Inicialização do Pygame
pygame.init()

# Configurações da tela
WIDTH, HEIGHT = 1024, 590
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Aurora Quest - Menu")

# Cores e fonte
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
font = pygame.font.Font(None, 60)

# Imagem de fundo
background = pygame.image.load("assets/extras/telaInicial.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Opções do menu
menu_options = ["Iniciar Jogo", "Sair"]
selected_option = 0

def draw_menu():
    screen.blit(background, (0, 0))
    for i, option in enumerate(menu_options):
        color = YELLOW if i == selected_option else WHITE
        text = font.render(option, True, color)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * 80))
        screen.blit(text, text_rect)
    pygame.display.flip()

running = True
while running:
    draw_menu()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                selected_option = (selected_option - 1) % len(menu_options)
            elif event.key == pygame.K_DOWN:
                selected_option = (selected_option + 1) % len(menu_options)
            elif event.key == pygame.K_RETURN:
                if menu_options[selected_option] == "Iniciar Jogo":
                    # Caminho absoluto para jogo.py
                    jogo_path = Path(__file__).parent / "jogo.py"
                    # Subprocess robusto
                    try:
                        subprocess.run([sys.executable, str(jogo_path)], cwd=jogo_path.parent)
                    except Exception as e:
                        print("Erro ao abrir o jogo:", e)
                    pygame.quit()
                    sys.exit()
                elif menu_options[selected_option] == "Sair":
                    pygame.quit()
                    sys.exit()

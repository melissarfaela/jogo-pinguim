import pygame
import sys

# Inicialização do Pygame
pygame.init()

# Configurações da tela
WIDTH, HEIGHT = 1024, 590
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Aurora Quest - Menu")

# Cores
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)

# Fonte
font = pygame.font.Font(None, 60)

# Carregando imagem de fundo
background = pygame.image.load("assets/extras/telaInicial.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Opções do menu
menu_options = ["Iniciar Jogo", "Sair"]
selected_option = 0

# Função para desenhar o menu
def draw_menu():
    screen.blit(background, (0, 0))
    for i, option in enumerate(menu_options):
        color = YELLOW if i == selected_option else WHITE
        text = font.render(option, True, color)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * 80))
        screen.blit(text, text_rect)
    pygame.display.flip()

# Loop do menu
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
                    print("Iniciando jogo...")  # Aqui você chamaria a função do jogo
                    running = False  # Fecha o menu
                elif menu_options[selected_option] == "Sair":
                    pygame.quit()
                    sys.exit()

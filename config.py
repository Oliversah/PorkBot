# Insira seu Token e o ID do canal onde o bolão será publicado
CANAL_PALPITES_ID = 1539698402617589760  # Substitua pelo ID do canal
CANAL_REGISTROS_ID = 1539698492958572635  # ID do canal privado onde chegam os logs de palpites

# IDs dos cargos que podem gerenciar o bolão (além de administradores)
CARGOS_PERMITIDOS_IDS = [
    1255222988534710332,  # Dev
    963192709848391700,   # Adm
]

palpites_abertos = True
resultado_divulgado = False  # Flag de controle para evitar o bug do bolão sem palpites
mensagem_bolao_id = None

embed_builder = {
    "titulo": "Bolão do Jogo",
    "titulo_url": "",
    "descricao": "Para alterar as configurações do painel, utilize os botões abaixo. Em caso de dúvidas, consulte um superior.",
    "cor": "#3498DB",
    "autor_nome": "",
    "autor_icon": "",
    "autor_url": "",
    "time_casa": "Defina",
    "time_visitante": "Defina",
    "rodape_texto": "",
    "rodape_icon": "",
    "imagem_url": "",
    "thumbnail_url": ""
}
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import config
from views import ViewPainelRio, ViewPalpitePublico, gerar_embed_previa
from modals import palpites_registrados

# Servidor HTTP para o Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"PorkBot Online")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def start_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=start_web_server, daemon=True).start()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

ICON_FECHADO = "https://cdn.discordapp.com/attachments/1492590020891246832/1541124293084057610/image.png?ex=6a8c7358&is=6a8b21d8&hm=f433a4111cd6537c644fabd5d1e4750004759dff9963d2ed0d9976cbe276fb9d&"
ICON_RESULTADO = "https://cdn.discordapp.com/attachments/1492590020891246832/1541131183255982140/trophy.png?ex=6a8c79c2&is=6a8b2842&hm=18652e51e19a24a8b5c0ecccc22a945b46784d07c074ac2e2613831888c2a4b5&"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

palpite_group = app_commands.Group(name="palpite", description="Comandos de gerenciamento do bolão")


@palpite_group.command(name="criar", description="Abre o painel de configuração do bolão.")
@app_commands.default_permissions(administrator=True)
async def criar(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            content="❌ Apenas administradores podem utilizar este comando!",
            ephemeral=True
        )
        return

    embed = gerar_embed_previa()
    await interaction.response.send_message(
        content="Altere as configurações do bolão utilizando as opções abaixo!",
        embed=embed,
        view=ViewPainelRio(),
        ephemeral=True
    )


@palpite_group.command(name="encerrar", description="Encerra o envio e edição de palpites.")
@app_commands.default_permissions(administrator=True)
async def encerrar(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            content="❌ Apenas administradores podem utilizar este comando!",
            ephemeral=True
        )
        return

    if not config.palpites_abertos:
        await interaction.response.send_message(
            content="Os palpites já estão encerrados!",
            ephemeral=True
        )
        return

    # Evita erro de interação já reconhecida
    await interaction.response.defer(ephemeral=True)

    config.palpites_abertos = False

    time_casa = config.embed_builder["time_casa"]
    time_visitante = config.embed_builder["time_visitante"]
    canal_palpites = interaction.guild.get_channel(config.CANAL_PALPITES_ID)

    if canal_palpites and config.mensagem_bolao_id:
        try:
            mensagem_bolao = await canal_palpites.fetch_message(config.mensagem_bolao_id)
            if mensagem_bolao:
                view_desativada = ViewPalpitePublico(time_casa, time_visitante)
                for item in view_desativada.children:
                    item.disabled = True
                
                await mensagem_bolao.edit(view=view_desativada)
        except Exception as e:
            print(f"Erro ao desativar botões do bolão: {e}")

    if canal_palpites:
        embed_encerrado = discord.Embed(
            title=None,
            description="Os palpites foram fechados. Aguarde até o final da partida para conferir o resultado oficial.",
            color=discord.Color.from_str("#f82424"),
            timestamp=discord.utils.utcnow()
        )
        
        embed_encerrado.set_author(
            name="Palpites Fechados",
            icon_url=ICON_FECHADO
        )
        
        guild_icon = interaction.guild.icon.url if interaction.guild.icon else None

        if guild_icon:
            embed_encerrado.set_thumbnail(url=guild_icon)

        embed_encerrado.set_footer(
            text="Encerrado em",
            icon_url=guild_icon
        )

        try:
            await canal_palpites.send(embed=embed_encerrado)
        except Exception as e:
            print(f"Erro ao enviar Embed de encerramento: {e}")

    # Usa followup pois usamos defer() no inicio
    await interaction.followup.send(
        content="O bolão foi encerrado com sucesso!",
        ephemeral=True
    )


@palpite_group.command(name="resultado", description="Define o placar final e divulga os acertadores.")
@app_commands.rename(gols_time_casa="time_casa", gols_time_visitante="time_visitante")
@app_commands.describe(
    gols_time_casa="Gols do time mandante (Casa)",
    gols_time_visitante="Gols do time visitante"
)
@app_commands.default_permissions(administrator=True)
async def resultado(interaction: discord.Interaction, gols_time_casa: int, gols_time_visitante: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            content="❌ Apenas administradores podem utilizar este comando!",
            ephemeral=True
        )
        return

    # Evita timeout e duplicação de resposta do Discord
    await interaction.response.defer(ephemeral=True)

    # TRAVA DE SEGURANÇA: Se já estiver vazio, bloqueia execuções duplicadas
    if not palpites_registrados:
        await interaction.followup.send(
            content="⚠️ O resultado deste bolão já foi divulgado e os palpites já foram limpos!",
            ephemeral=True
        )
        return

    time_casa = config.embed_builder["time_casa"]
    time_visitante = config.embed_builder["time_visitante"]
    placar_oficial = (str(gols_time_casa), str(gols_time_visitante))

    # 1. PRIMEIRO calcula os vencedores com os palpites atuais
    vencedores = [
        f"<@{user_id}>" for user_id, palpite in palpites_registrados.items()
        if palpite == placar_oficial
    ]

    canal_palpites = interaction.guild.get_channel(config.CANAL_PALPITES_ID)
    if not canal_palpites:
        await interaction.followup.send(
            content=f"Canal de palpites inválido! Verifique a ID `{config.CANAL_PALPITES_ID}` no `config.py`.",
            ephemeral=True
        )
        return

    vencedores_texto = ", ".join(vencedores) if vencedores else "Ninguém acertou o placar exato!"

    descricao = (
        f"> A partida terminou em **{time_casa} {gols_time_casa} x {gols_time_visitante} {time_visitante}**.\n\n"
        f"**Vencedor(es):** {vencedores_texto}"
    )

    embed_resultado = discord.Embed(
        description=descricao,
        color=discord.Color.from_str("#f8a324"),
        timestamp=interaction.created_at
    )

    embed_resultado.set_author(
        name="Resultado do Bolão!",
        icon_url=ICON_RESULTADO
    )

    server_icon = interaction.guild.icon.url if interaction.guild.icon else None
    if server_icon:
        embed_resultado.set_thumbnail(url=server_icon)

    embed_resultado.set_footer(
        text=interaction.guild.name,
        icon_url=server_icon
    )

    try:
        # 2. Envia o resultado correto com os acertadores no canal público
        await canal_palpites.send(embed=embed_resultado)
        
        # 3. SÓ DEPOIS DE ENVIAR, limpa os palpites e fecha o bolão
        palpites_registrados.clear()
        config.palpites_abertos = False

        # Responde o admin de forma privada
        await interaction.followup.send(
            content=f"Resultado divulgado no canal {canal_palpites.mention} e os palpites foram limpos para o próximo jogo!",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            content=f"Erro ao enviar o resultado para o canal de palpites: `{e}`",
            ephemeral=True
        )


bot.tree.add_command(palpite_group)


@bot.event
async def on_ready():
    # IDs dos servidores onde os comandos devem aparecer instantaneamente
    ids_servidores = [
        1492589647015055481,
        794150101504491530
    ]
    
    for guild_id in ids_servidores:
        guild_obj = discord.Object(id=guild_id)
        bot.tree.copy_global_to(guild=guild_obj)
        await bot.tree.sync(guild=guild_obj)
    
    bot.add_view(ViewPalpitePublico(
        time_casa=config.embed_builder["time_casa"],
        time_visitante=config.embed_builder["time_visitante"]
    ))

    print(f"✅ Bot online como {bot.user}!")


if __name__ == "__main__":
    bot.run(TOKEN)
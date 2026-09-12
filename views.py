import discord
from discord import ui
import config
from modals import (
    ModalTitulo, ModalDescricao, ModalCor, ModalAutor,
    ModalConfronto, ModalRodape, ModalMidia, ModalResultadoBolao,
    ModalEnviarPalpite, palpites_registrados
)

def gerar_embed_previa():
    data = config.embed_builder
    
    # Tratamento de Cor
    try:
        cor_hex = data["cor"].replace("#", "")
        cor_int = int(cor_hex, 16)
    except ValueError:
        cor_int = 0x3498DB

    embed = discord.Embed(
        title=data["titulo"] if data["titulo"] else None,
        url=data["titulo_url"] if data["titulo_url"] else None,
        description=data["descricao"] if data["descricao"] else None,
        color=cor_int
    )

    if data["autor_nome"]:
        embed.set_author(
            name=data["autor_nome"],
            icon_url=data["autor_icon"] if data["autor_icon"] else None,
            url=data["autor_url"] if data["autor_url"] else None
        )

    if data["time_casa"] or data["time_visitante"]:
        embed.add_field(
            name="⚔️ Confronto",
            value=f"**{data['time_casa']}** vs **{data['time_visitante']}**",
            inline=False
        )

    if data["rodape_texto"]:
        embed.set_footer(
            text=data["rodape_texto"],
            icon_url=data["rodape_icon"] if data["rodape_icon"] else None
        )

    if data["imagem_url"]:
        embed.set_image(url=data["imagem_url"])

    if data["thumbnail_url"]:
        embed.set_thumbnail(url=data["thumbnail_url"])

    return embed


async def atualizar_painel(interaction: discord.Interaction):
    embed = gerar_embed_previa()
    await interaction.response.edit_message(embed=embed)


class ViewPainelRio(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # TRAVA DE ADM GLOBAL PARA TODOS OS BOTÕES DO PAINEL
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                content="❌ Apenas administradores podem usar as opções do painel!",
                ephemeral=True
            )
            return False
        return True

    @ui.button(label="Título", style=discord.ButtonStyle.secondary, row=0)
    async def btn_titulo(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalTitulo())

    @ui.button(label="Descrição", style=discord.ButtonStyle.secondary, row=0)
    async def btn_descricao(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalDescricao())

    @ui.button(label="Cor", style=discord.ButtonStyle.secondary, row=0)
    async def btn_cor(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalCor())

    @ui.button(label="Autor", style=discord.ButtonStyle.secondary, row=0)
    async def btn_autor(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalAutor())

    @ui.button(label="Confronto", style=discord.ButtonStyle.primary, row=1)
    async def btn_confronto(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalConfronto())

    @ui.button(label="Rodapé", style=discord.ButtonStyle.secondary, row=1)
    async def btn_rodape(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalRodape())

    @ui.button(label="Mídias", style=discord.ButtonStyle.secondary, row=1)
    async def btn_midia(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalMidia())

    @ui.button(label="Enviar Bolão", style=discord.ButtonStyle.success, row=2)
    async def btn_enviar(self, interaction: discord.Interaction, button: ui.Button):
        canal = interaction.guild.get_channel(config.CANAL_PALPITES_ID)
        if not canal:
            await interaction.response.send_message("Canal de palpites não encontrado!", ephemeral=True)
            return

        embed = gerar_embed_previa()
        view_publica = ViewPalpitePublico(
            config.embed_builder["time_casa"],
            config.embed_builder["time_visitante"]
        )

        msg = await canal.send(embed=embed, view=view_publica)
        config.mensagem_bolao_id = msg.id
        config.palpites_abertos = True

        await interaction.response.send_message(f"Bolão enviado no canal {canal.mention}!", ephemeral=True)


class ViewPalpitePublico(ui.View):
    def __init__(self, time_casa: str, time_visitante: str):
        super().__init__(timeout=None)
        self.time_casa = time_casa
        self.time_visitante = time_visitante

    @ui.button(label="Enviar / Editar Palpite", style=discord.ButtonStyle.success, custom_id="btn_palpite_publico")
    async def btn_palpite(self, interaction: discord.Interaction, button: ui.Button):
        if not config.palpites_abertos:
            await interaction.response.send_message("Os palpites para este jogo estão encerrados!", ephemeral=True)
            return

        palpite_atual = palpites_registrados.get(interaction.user.id)
        await interaction.response.send_modal(
            ModalEnviarPalpite(self.time_casa, self.time_visitante, palpite_atual)
        )
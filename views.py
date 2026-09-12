import discord
from discord import ui
import config
from modals import (
    ModalTitulo, ModalDescricao, ModalCor, 
    ModalAutor, ModalRodape, ModalMidia,
    ModalConfronto, ModalEnviarPalpite,
    palpites_registrados
)


class ViewPalpitePublico(ui.View):
    def __init__(self, time_casa: str, time_visitante: str):
        super().__init__(timeout=None)
        self.time_casa = time_casa
        self.time_visitante = time_visitante

    @ui.button(
        label="Palpitar", 
        style=discord.ButtonStyle.primary, 
        emoji="<:Icon_Sparkles:1540764556035498128>",
        custom_id="btn_palpitar_publico"
    )
    async def btn_palpitar(self, interaction: discord.Interaction, button: ui.Button):
        if not config.palpites_abertos:
            await interaction.response.send_message(
                content="Palpites encerrados! Não é mais possível enviar ou editar palpites.",
                ephemeral=True
            )
            return

        palpite_existente = palpites_registrados.get(interaction.user.id)

        if palpite_existente:
            await interaction.response.send_message(
                content="Você já enviou um palpite para esta partida! Utilize o botão **Editar Palpite** para alterá-lo.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            ModalEnviarPalpite(
                time_casa=self.time_casa, 
                time_visitante=self.time_visitante
            )
        )

    @ui.button(
        label="Editar Palpite", 
        style=discord.ButtonStyle.secondary, 
        emoji="<:Icon_Pencil:1540774667567235235>",
        custom_id="btn_editar_palpite_publico"
    )
    async def btn_editar(self, interaction: discord.Interaction, button: ui.Button):
        if not config.palpites_abertos:
            await interaction.response.send_message(
                content="Palpites encerrados! Não é mais possível enviar ou editar palpites.",
                ephemeral=True
            )
            return

        palpite_existente = palpites_registrados.get(interaction.user.id)

        if not palpite_existente:
            await interaction.response.send_message(
                content="Você ainda não possui um palpite registrado. Clique em **Palpitar** para enviar seu primeiro placar!",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            ModalEnviarPalpite(
                time_casa=self.time_casa, 
                time_visitante=self.time_visitante,
                palpite_atual=palpite_existente
            )
        )


def gerar_embed_previa() -> discord.Embed:
    data = config.embed_builder
    
    cor_str = data.get("cor", "#5865F2").strip()
    try:
        if cor_str.startswith("#"):
            cor_int = int(cor_str[1:], 16)
        else:
            cor_int = int(cor_str, 16)
        cor_hex = discord.Color(cor_int)
    except Exception:
        cor_hex = discord.Color.purple()

    embed = discord.Embed(
        title=data["titulo"] or None,
        description=data["descricao"] or None,
        color=cor_hex,
        url=data["titulo_url"] if data["titulo_url"] else None
    )

    if data.get("autor_nome"):
        embed.set_author(
            name=data["autor_nome"],
            icon_url=data["autor_icon"] if data["autor_icon"] else None,
            url=data["autor_url"] if data["autor_url"] else None
        )

    if data.get("rodape_texto"):
        embed.set_footer(
            text=data["rodape_texto"],
            icon_url=data["rodape_icon"] if data["rodape_icon"] else None
        )

    if data.get("imagem_url"):
        embed.set_image(url=data["imagem_url"])

    if data.get("thumbnail_url"):
        embed.set_thumbnail(url=data["thumbnail_url"])

    return embed


async def atualizar_painel(interaction: discord.Interaction):
    embed = gerar_embed_previa()
    texto_mensagem = "Para alterar as configurações do painel, utilize os botões abaixo. Em caso de dúvidas, consulte um superior."
    await interaction.response.edit_message(content=texto_mensagem, embed=embed, view=ViewPainelRio())


class ViewPainelRio(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Título", 
        style=discord.ButtonStyle.secondary, 
        emoji="<:Icon_Paper:1540751972511260792>", 
        row=0
    )
    async def btn_titulo(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalTitulo())

    @ui.button(
        label="Descrição", 
        style=discord.ButtonStyle.secondary, 
        emoji="<:Icon_Member_Applications:1540752715905376308>", 
        row=0
    )
    async def btn_descricao(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalDescricao())

    @ui.button(
        label="Cor Hex", 
        style=discord.ButtonStyle.secondary, 
        emoji="<:Icon_Paint_Palette:1540752779679633479>", 
        row=0
    )
    async def btn_cor(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalCor())

    @ui.button(
        label="Autor", 
        style=discord.ButtonStyle.secondary, 
        emoji="<:Icon_Shield_User:1540752834268766321>", 
        row=0
    )
    async def btn_autor(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalAutor())

    @ui.button(
        label="Confronto", 
        style=discord.ButtonStyle.secondary, 
        emoji="<:Icon_Game_Controller:1540763949895520366>", 
        row=1
    )
    async def btn_confronto(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalConfronto())

    @ui.button(
        label="Imagem", 
        style=discord.ButtonStyle.secondary, 
        emoji="<:Icon_Image:1540756117183922330>", 
        row=1
    )
    async def btn_midia(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalMidia())

    @ui.button(
        label="Rodapé", 
        style=discord.ButtonStyle.secondary, 
        emoji="<:Icon_Checkpoint:1540756169864384512>", 
        row=1
    )
    async def btn_rodape(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModalRodape())

    @ui.button(
        label="Publicar Bolão", 
        style=discord.ButtonStyle.primary, 
        emoji="<:Icon_Download:1540756242014933025>", 
        row=2
    )
    async def btn_publicar(self, interaction: discord.Interaction, button: ui.Button):
        canal = interaction.guild.get_channel(config.CANAL_PALPITES_ID)
        
        if not canal:
            await interaction.response.send_message(
                content=f"Canal de destino inválido! Verifique a ID {config.CANAL_PALPITES_ID} no config.py.", 
                ephemeral=True
            )
            return

        try:
            config.palpites_abertos = True
            palpites_registrados.clear()

            embed_final = gerar_embed_previa()
            
            view_publica = ViewPalpitePublico(
                time_casa=config.embed_builder["time_casa"],
                time_visitante=config.embed_builder["time_visitante"]
            )
            
            msg_enviada = await canal.send(embed=embed_final, view=view_publica)
            config.mensagem_bolao_id = msg_enviada.id
            
            await interaction.response.edit_message(
                content="Bolão enviado com sucesso! Os palpites já estão abertos.",
                embed=None,
                view=None
            )
        except Exception as e:
            await interaction.response.send_message(
                content=f"Erro ao publicar o bolão: `{e}`", 
                ephemeral=True
            )